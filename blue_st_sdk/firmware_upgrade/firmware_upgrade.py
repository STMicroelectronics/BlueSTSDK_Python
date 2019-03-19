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

The firmware_upgrade module is responsible for managing the upgrading process of
devices' firmware via Bluetooth Low Energy (BLE).
"""


# IMPORT

import sys
import os
from enum import Enum
from abc import ABCMeta
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor

from blue_st_sdk.python_utils import lock


# CLASSES

class FirmwareUpgrade(object):
    """Class to handle the firmware upgrade capability for a board running the
    BlueST Protocol.
    """

    _NUMBER_OF_THREADS = 5
    """Number of threads to be used to notify the listeners."""

    def __init__(self):
        """Constructor."""

        self._thread_pool = ThreadPoolExecutor(FirmwareUpgrade._NUMBER_OF_THREADS)
        """Pool of thread used to notify the listeners."""

        self._listeners = []
        """List of listeners to the node changes.
        It is a thread safe list, so a listener can subscribe itself through a
        callback."""

    def add_listener(self, listener):
        """Add a listener.
        
        Args:
            listener (:class:`blue_st_sdk.firmware_upgrade.utils.firmware_upgrade.FirmwareUpgradeListener`):
                Listener to be added.
        """
        if listener is not None:
            with lock(self):
                if not listener in self._listeners:
                    self._listeners.append(listener)

    def remove_listener(self, listener):
        """Remove a listener.

        Args:
            listener (:class:`blue_st_sdk.firmware_upgrade.utils.firmware_upgrade.FirmwareUpgradeListener`):
                Listener to be removed.
        """
        if listener is not None:
            with lock(self):
                if listener in self._listeners:
                    self._listeners.remove(listener)

    @abstractmethod
    def get_console(self, node):
        """Get an instance of this class.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node whose firmware has to be
                updated.
        
        Returns:
            :class:`blue_st_sdk.firmware_upgrade.firmware_upgrade.FirmwareUpgrade`:
            An instance of this class if the given node implements the BlueST
            protocol, "None" otherwise.
        
        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "get_console()" to '
                                  'use the "FirmwareUpgrade" class.')

    @abstractmethod
    def upgrade_firmware(self, firmware_file):
        """Upgrade the firmware onto the device assiciated to the debug console.
        The firmware is loaded starting from the address "0x0804000".

        Args:
            firmware_file (:class:`blue_st_sdk.firmware_upgrade.utils.firmware_file.FirmwareFile`):
                Firmware file.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
            :exc:`OSError` if the file is not found or is inaccessible.
            :exc:`ValueError` if the firmware file can not be read properly.

        Returns:
            bool: True if the upload starts correctly, False otherwise.
        """
        raise NotImplementedError('You must implement "upgrade_firmware()" to '
                                  'use the "FirmwareUpgrade" class.')


class FirmwareUpgradeError(Enum):
    """Class with different errors that may happen when upgrading the
    firmware"""

    # Error fired when the CRC computed at node side does not correspond to
    # the one computed at gateway side.
    # This may happen when there errors during the transmission.
    CORRUPTED_FILE_ERROR = 0

    # Error fired when is not possible to upload all the file.
    TRANSMISSION_ERROR = 1

    # Error fired when it is not possible to open the file.
    INVALID_FIRMWARE_ERROR = 2


# INTERFACES

class FirmwareUpgradeListener(object):
    """Interface used by the :class:`blue_st_sdk.firmware_upgrade.firmware_upgrade.FirmwareUpgrade`
    class to notify changes of the firmware uprgade process.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_upgrade_firmware_complete(self, debug_console, firmware_file):
        """To be called whenever the firmware has been upgraded correctly.

        Args:
            debug_console (:class:`blue_st_sdk.debug_console.DebugConsole`):
                Debug console.
            firmware_file (:class:`blue_st_sdk.firmware_upgrade.utils.firmware_file.FirmwareFile`):
                Firmware file.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "on_upgrade_firmware_complete()" to '
                                  'use the "FirmwareUpgradeListener" class.')

    
    @abstractmethod
    def on_upgrade_firmware_error(self, debug_console, firmware_file, error):
        """To be called whenever there is an error in upgrading the firmware.

        Args:
            debug_console (:class:`blue_st_sdk.debug_console.DebugConsole`):
                Debug console.
            firmware_file (:class:`blue_st_sdk.firmware_upgrade.utils.firmware_file.FirmwareFile`):
                Firmware file.
            error (:class:`blue_st_sdk.firmware_upgrade.firmware_upgrade.FirmwareUpgradeError`):
                Error code.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "on_upgrade_firmware_error()" to '
                                  'use the "FirmwareUpgradeListener" class.')

    
    @abstractmethod
    def on_upgrade_firmware_progress(self, debug_console, firmware_file, bytes_sent):
        """To be called whenever there is an update in upgrading the firmware,
        i.e. a block of data has been correctly sent and it is possible to send
        a new one.

        Args:
            debug_console (:class:`blue_st_sdk.debug_console.DebugConsole`):
                Debug console.
            firmware_file (:class:`blue_st_sdk.firmware_upgrade.utils.firmware_file.FirmwareFile`):
                Firmware file.
            bytes_sent (int): Data sent in bytes.
            bytes_to_send (int): Data to send in bytes.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "on_upgrade_firmware_progress()" to '
                                  'use the "FirmwareUpgradeListener" class.')
