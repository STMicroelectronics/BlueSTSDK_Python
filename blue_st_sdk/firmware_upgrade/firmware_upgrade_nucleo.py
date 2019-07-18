################################################################################
# COPYRIGHT(c) 2018 STMicroelectronics                                         #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided that the following conditions are met:  #
#   1. Redistributions of source code must retain the above copyright notice,  #
#      this list of conditions and the following disclaimer.                   #
#   2. Redistributions in binary form must reproduce the above copyright       #
#      notice, this list of conditions and the following disclaimer in the     #
#      documentation and/or other materials provided with the distribution.    #
#   3. Neither the name of STMicroelectronics nor the names of its             #
#      contributors may be used to endorse or promote products derived from    #
#      this software without specific prior written permission.                #
#                                                                              #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"  #
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE    #
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE   #
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE    #
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR          #
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF         #
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS     #
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN      #
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)      #
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE   #
# POSSIBILITY OF SUCH DAMAGE.                                                  #
################################################################################


"""firmware_upgrade

The firmware_upgrade_nucleo module is responsible for managing the upgrading
process of devices'firmware via Bluetooth Low Energy (BLE).
"""


# IMPORT

import sys
import os
import threading
from enum import Enum

from blue_st_sdk.node import NodeType
from blue_st_sdk.debug_console import DebugConsoleListener
from blue_st_sdk.firmware_upgrade.firmware_upgrade import FirmwareUpgrade
from blue_st_sdk.firmware_upgrade.firmware_upgrade import FirmwareUpgradeError
from blue_st_sdk.utils.number_conversion import LittleEndian
from blue_st_sdk.utils.python_utils import lock


# CLASSES

class FirmwareUpgradeNucleo(FirmwareUpgrade):
    """Class that implements the firmware upgrade capability for a Nucleo device.
    """

    def __init__(self, debug_console):
        """Constructor.

        Args:
            debug_console (:class:`blue_st_sdk.firmware_upgrade.debug.Debug`): Console
            used to send commands.
        """
        FirmwareUpgrade.__init__(self)

        self._debug_console = debug_console
        """Debug console where to send commands."""

        self._debug_console_listener = None
        """Listener to nucleo debug console events."""

    def _set_listener(self, listener):
        """Set the listener to the debug console.

        Args:
            listener (:class:`blue_st_sdk.firmware_upgrade.debug_console.DebugConsoleListener`):
            Listener to the debug console.
        """
        with lock(self):
            self._debug_console.remove_listener(self._debug_console_listener)
            self._debug_console.add_listener(listener)
            self._debug_console_listener = listener

    def _firmware_is_upgrading(self):
        """Check whether a firmware upgrade process is already in place.

        Returns:
            bool: True if a firmware upgrade process is already in place, False
            otherwise.
        """
        return self._debug_console_listener != None

    @classmethod
    def get_console(self, node):
        """Get an instance of this class.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node whose firmware has to be
            updated.

        Returns:
            :class:`blue_st_sdk.firmware_upgrade.firmware_upgrade.FirmwareUpgrade`:
            An instance of this class if the given node implements the BlueST
            protocol, "None" otherwise.
        """
        debug = node.get_debug()

        if debug is not None:
            _type = node.get_type()
            if _type == NodeType.NUCLEO or \
                _type == NodeType.SENSOR_TILE or \
                _type == NodeType.BLUE_COIN or \
                _type == NodeType.STEVAL_BCN002V1 or \
                _type == NodeType.SENSOR_TILE_BOX:
                return FirmwareUpgradeNucleo(debug)
        return None

    def upgrade_firmware(self, firmware_file):
        """Upgrade the firmware onto the device assiciated to the debug console.
        The firmware is loaded starting from the address "0x0804000".

        Args:
            firmware_file (:class:`blue_st_sdk.firmware_upgrade.utils.firmware_file.FirmwareFile`):
            Firmware file.

        Raises:
            :exc:`OSError` if the file is not found or is inaccessible.
            :exc:`ValueError` if the firmware file can not be read properly.

        Returns:
            bool: True if the upload starts correctly, False otherwise.
        """
        if self._firmware_is_upgrading():
            return False
        self._set_listener(FirmwareUpgradeDebugConsoleListener(self))
        try:
            self._debug_console_listener.load_file(firmware_file)
        except (OSError, ValueError) as e:
            raise e

        return True


class FirmwareUpgradeDebugConsoleListener(DebugConsoleListener):
    """Class that handles the upgrade of the firmware file to a device via
    Bluetooth."""

    FIRMWARE_UPGRADE_COMMAND = b'upgradeFw'
    """Firmware upgrade command."""

    ACK_MSG = u'\u0001'  # Unicode character
    """Acknowledgement message."""

    MAX_MSG_SIZE = 16
    """The STM32L4 Family can write only 8 bytes at a time, thus sending a
    multiple of 8 bytes simplifies the code."""

    LOST_MSG_TIMEOUT_ms = 1000
    """Timeout for sending a message."""

    FIRMWARE_UPGRADE_TIMEOUT_ms = 4 * LOST_MSG_TIMEOUT_ms
    """Increased timeout for sending a message"""

    BLOCK_OF_PACKETS_SIZE = 10
    """Sending a block of packets at a time, in order to not to stress the
    Bluetooth too much."""

    def __init__(self, firmware_upgrade_console):
        """Costructor.

        Args:
            firmware_upgrade_console (FirmwareUpgrade): Firmware upgrade console
            used to call user-defined listener's methods.
        """
        DebugConsoleListener.__init__(self)

        self._firmware_file = None
        """Firmware file."""

        self._firmware_fd = None
        """Firmware file descriptor."""

        self._firmware_crc = 0
        """CRC code of the firmware file."""

        self._firmware_upgrade_console = firmware_upgrade_console
        """Firmware upgrade console."""

        self._bytes_sent = 0
        """Number of bytes sent."""

        self._block_shift = 0
        """Whenever there is a transmission error, the number of packets to send
        in a block is halved."""

        #self._timeout = threading.Timer(
        #    self.FIRMWARE_UPGRADE_TIMEOUT_ms * 1000,
        #    self._on_timeout)
        """Timeout for sending a single packet of data."""

    def _on_load_error(self, error):
        """Notifies to the user that the upload on the file raised an error.

        Args:
            error (:class:`blue_st_sdk.firmware_upgrade.firmware_upgrade.FirmwareUpgradeError`):
            Error code.
        """
        for listener in self._firmware_upgrade_console._listeners:
            listener.on_upgrade_firmware_error(self,
                self._firmware_file,
                error)
        self._firmware_upgrade_console._set_listener(None)

    def _on_load_progress(self):
        """Notifies to the user that a block of data has been correctly sent and
        that it is possible to send a new one."""
        self._number_of_packets_received += 1
        if self._number_of_packets_received % self._get_block_size() == 0:
            for listener in self._firmware_upgrade_console._listeners:
                listener.on_upgrade_firmware_progress(self,
                    self._firmware_file,
                    self._bytes_sent,
                    self._firmware_file.get_size())
            #self._send_block()
    
    def _on_load_complete(self):
        """Notifies to the user that the upload on the file has completed."""
        for listener in self._firmware_upgrade_console._listeners:
            listener.on_upgrade_firmware_complete(self,
                self._firmware_file,
                self._bytes_sent)
        self._firmware_upgrade_console._set_listener(None)

    #def _on_timeout(self):
    #    """Timeout callback."""
    #    self._on_load_error(FirmwareUpgradeError.TRANSMISSION_ERROR)
    #    self._block_shift += 1

    def _get_block_size(self):
        """Getting block size.

        Returns:
            int: The block size.
        """
        #return int(max(1,
        #    self.BLOCK_OF_PACKETS_SIZE / ( 1 << (self._block_shift))))
        return self.BLOCK_OF_PACKETS_SIZE

    def _send_block(self):
        """Sending a block of packets through the debug console.
        It stops at the first error.

        Returns:
            bool: True if all the packets are sent correctly, False otherwise.
        """
        # Sending a packet at a time.
        for packet in range(0, self._get_block_size()):
            # Computing the number of bytes to read from the file and to send
            # through the debug console.
            size_to_read = min(
                self._firmware_file.get_size() - self._bytes_sent,
                self.MAX_MSG_SIZE)

            # Reading data from the file.
            try:
                data = self._firmware_fd.read(size_to_read)
            except Exception as e:
                return False

            # Chek size of data.
            if len(data) != size_to_read:
                return False
            
            # Sending data throught the debug console.
            self._bytes_sent += size_to_read
            if self._firmware_upgrade_console._debug_console.write(data) \
                != size_to_read:
                return False

        return True

    def load_file(self, firmware_file):
        """Starts to upload the firmware.

        Args:
            firmware_file (:class:`blue_st_sdk.firmware_upgrade.utils.firmware_file.FirmwareFile`):
            Firmware file.

        Raises:
            :exc:`OSError` if the file is not found or is inaccessible.
            :exc:`ValueError` if the firmware file can not be read properly.
        """
        try:
            # Setting the firmware file.
            self._firmware_file = firmware_file

            # Computing the CRC of the firmware file content.
            self._firmware_crc = self._firmware_file.get_crc_32()

            # Creating the command to start the firmware upgrade.
            # Python 2.
            #command = bytearray(self.FIRMWARE_UPGRADE_COMMAND, encoding='utf8') \
            #    + bytearray(LittleEndian.uint32_to_bytes(
            #        self._firmware_file.get_size()), encoding='utf8') \
            #    + bytearray(LittleEndian.uint32_to_bytes(
            #        self._firmware_crc), encoding='utf8')
            # Python 3.
            command = self.FIRMWARE_UPGRADE_COMMAND \
                + LittleEndian.uint32_to_bytes(self._firmware_file.get_size()) \
                + LittleEndian.uint32_to_bytes(self._firmware_crc)
        except (OSError, ValueError) as e:
            raise e

        # Opening the firmware file to send data packets.
        self._firmware_fd = self._firmware_file.open()

        # Starting the firmware upgrade.
        self._loading_file_status = LoadingFileStatus.CRC_CHECK
        self._firmware_upgrade_console._debug_console.write(command)

    def on_stdout_receive(self, debug_console, message):
        """Called whenever a message is received on the standard output.

        A message is received on the standard output in two cases:
          + When the device sends back the CRC received from the gateway.
          + When the device sends an ACK or a NACK message after receiving the
            firmware file and comparing the CRC computed on it with the CRC
            previously received from the gateway.

        Args:
            debug_console (object): Console that sends the message.
            message (str): The message received on the stdout console.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        if self._loading_file_status == LoadingFileStatus.CRC_CHECK:
            # Check whether the message received from the node contains the same
            # CRC code that we have sent.
            if message.encode('ISO-8859-1') != \
                LittleEndian.uint32_to_bytes(self._firmware_crc):
                self._on_load_error(FirmwareUpgradeError.TRANSMISSION_ERROR)

            # Sending firmware in blocks of packets.
            self._loading_file_status = LoadingFileStatus.ACK_CHECK
            self._number_of_packets_received = 0
            while self._firmware_file.get_size() - self._bytes_sent > 0:
                if not self._send_block():
                    self._on_load_error(
                        FirmwareUpgradeError.CORRUPTED_FILE_ERROR)
                    break

        elif self._loading_file_status == LoadingFileStatus.ACK_CHECK:
            # Transfer completed.
            #self._timeout.cancel()
            # Python 2.
            #if message.encode('ISO-8859-1').lower() == self.ACK_MSG.lower():
            # Python 3.
            if message.lower() == self.ACK_MSG.lower():
                self._on_load_complete()
            else:
                self._on_load_error(FirmwareUpgradeError.CORRUPTED_FILE_ERROR)

    def on_stderr_receive(self, debug, message):
        """Called whenever a message is received on the standard error.

        Args:
            debug_console (object): Console that sends the message.
            message (str): The message received on the stderr console.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        pass

    def on_stdin_send(self, debug_console, message, status):
        """Called whenever a message is sent to the standard input.

        A message is sent to the standard input whenever some data are written
        to the debug console.

        Args:
            debug_console (object): Console that receives the message.
            message (str): The message sent to the stdin console.
            status (bool): True if the message is sent correctly, False
            otherwise.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        if status:
            if self._loading_file_status == LoadingFileStatus.ACK_CHECK:
                #self._timeout.cancel()
                self._on_load_progress()
                #self._timeout.start()
        else:
            self._on_load_error(FirmwareUpgradeError.TRANSMISSION_ERROR)


class LoadingFileStatus(Enum):
    """Status of loading file process."""
    CRC_CHECK = 0
    ACK_CHECK = 1
