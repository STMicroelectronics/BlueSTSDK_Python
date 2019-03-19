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


"""debug

The debug module is responsible for managing the debugging capabilities offered
by the BlueSTSDK.
"""


# IMPORT

from abc import ABCMeta
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor

from blue_st_sdk.utils.ble_node_definitions import Debug
from blue_st_sdk.python_utils import lock


# CLASSES

class DebugConsole():
    """Class used to read/write debug messages."""

    _MAXIMUM_MESSAGE_SIZE_BYTES = 20
    """Maximum size of the messages to send."""

    _NUMBER_OF_THREADS = 5
    """Number of threads to be used to notify the listeners."""

    def __init__(self, node, stdinout_characteristic, stderr_characteristic):
        """Constructor.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that will send the data.
            stdinout_characteristic (Characteristic): The BLE characteristic
                used to read/write data from/to stdin/stdout. Refer to
                    `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                    for more information.
            stderr_characteristic (Characteristic): The BLE characteristic used
                to read data from stderr. Refer to
                    `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                    for more information.
        """
        self._node = node
        """Node that sends data to this class."""

        self._stdinout_characteristic = stdinout_characteristic
        """Characteristic used to read/write data from/to stdin/stdout."""

        self._stderr_characteristic = stderr_characteristic
        """Characteristic used to read data from stderr."""

        self._thread_pool = ThreadPoolExecutor(DebugConsole._NUMBER_OF_THREADS)
        """Pool of thread used to notify the listeners."""

        self._listeners = []
        """List of listeners to the events of new data received.
        It is a thread safe list, so a listener can subscribe itself through a
        callback."""

    def _decode_data(self, data):
        """Convert data to standard ascii characters.

        Args:
            data (bytearray): Data to be encoded.

        Returns:
            str: A string representing the given data.
        """
        return data.decode('ISO-8859-1')

    def write(self, data):
        """Write an array of bytes to the stdin.

        The message might be sent through more iterations on the Bluetooth
        channel.

        Args:
            data (bytearray): Data to be sent.

        Returns:
            int: The number of bytes sent to the stdin/stdout standard
            characteristic.
        """
        char_handle = self._stdinout_characteristic.getHandle()
        bytes_sent = 0
        while bytes_sent < len(data):
            # Computing data to send.
            bytes_to_send = min(
                self._MAXIMUM_MESSAGE_SIZE_BYTES,
                len(data) - bytes_sent
            )
            data_to_send = data[bytes_sent:bytes_sent + bytes_to_send]

            # Writing data.
            self._node.writeCharacteristic(
                char_handle,
                data_to_send,
                True)
            bytes_sent += bytes_to_send

            # Calling on-write callback for a debug characteristic.
            self.on_write_characteristic(
                self._stdinout_characteristic, data_to_send, True)

        return bytes_sent

    def add_listener(self, listener):
        """Adding a listener.

        Args:
            listener (:class:`blue_st_sdk.debug.DebugListener`): Listener to
                be added.
        """
        if listener is not None:
            with lock(self):
                if not listener in self._listeners:
                    self._listeners.append(listener)
                if self._listeners:
                    self._node.set_notification_status(
                        self._stdinout_characteristic, True)
                    self._node.set_notification_status(
                        self._stderr_characteristic, True)

    def remove_listener(self, listener):
        """Remove a listener.

        Args:
            listener (:class:`blue_st_sdk.debug.DebugListener`): Listener to
                be removed.
        """
        if listener is not None:
            with lock(self):
                if listener in self._listeners:
                    self._listeners.remove(listener)
                if not self._listeners:
                    self._node.set_notification_status(
                        self._stdinout_characteristic, False)
                    self._node.set_notification_status(
                        self._stderr_characteristic, False)

    def on_update_characteristic(self, characteristic, data):
        """The characteristic has been updated.

        If it is a debug characteristic, data are sent to the registered
        listeners.

        Args:
            characteristic (Characteristic): The BLE characteristic that has
                been updated.
                Refer to
                `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                for more information.
            data (str): The data notified from the given characteristic.
        """
        if len(self._listeners) == 0:
            return

        data_str = self._decode_data(data)

        if characteristic.uuid == \
            Debug.DEBUG_STDINOUT_BLUESTSDK_SERVICE_UUID:
            for listener in self._listeners:
                # Calling user-defined callback.
                self._thread_pool.submit(listener.on_stdout_receive(
                    self, data_str))

        elif characteristic.uuid == \
            Debug.DEBUG_STDERR_BLUESTSDK_SERVICE_UUID:
            for listener in self._listeners:
                # Calling user-defined callback.
                self._thread_pool.submit(listener.on_stderr_receive(
                    self, data_str))

    def on_write_characteristic(self, characteristic, data, status):
        """The characteristic has been written.

        Args:
            characteristic (Characteristic): The BLE characteristic that has
                been written.
            data (bytearray): Received data.
            status (bool): True if the writing operation was successfully, False
                otherwise.
        """
        if len(self._listeners) == 0:
            return

        data_str = self._decode_data(data)

        if characteristic.uuid == \
            Debug.DEBUG_STDINOUT_BLUESTSDK_SERVICE_UUID:
            for listener in self._listeners:
                # Calling user-defined callback.
                self._thread_pool.submit(listener.on_stdin_send(
                    self,
                    data_str[0:self._MAXIMUM_MESSAGE_SIZE_BYTES],
                    #data[0:self._MAXIMUM_MESSAGE_SIZE_BYTES],
                    status))

    def get_node(self):
        """Getting the node that listen to / write to this debug console.

        Returns:
            node (:class:`blue_st_sdk.node.Node`): the node that listen/write to
                this debug console.
        """
        return self._node


class DebugConsoleListener(object):
    """Interface used by the :class:`blue_st_sdk.debug.DebugConsole` class to
    notify changes on a debug console.
    Data received/sent from/to a node are encoded with ISO-8859-1 charset.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_stdout_receive(self, debug_console, message):
        """Called whenever a new message is received on the standard output.

        Args:
            debug_console (object): Console that sends the message.
            message (str): The message received on the stdout console.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError(
            'You must implement "on_stdut_received()" to use the "DebugListener"'
            'class.')

    @abstractmethod
    def on_stderr_receive(self, debug_console, message):
        """Called whenever a new message is received on the standard error.

        Args:
            debug_console (object): Console that sends the message.
            message (str): The message received on the stderr console.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError(
            'You must implement "on_stderr_receive()" to use the "DebugListener"'
            'class.')

    @abstractmethod
    def on_stdin_send(self, debug_console, message, status):
        """Called whenever a new message is sent to the standard input.

        Args:
            debug_console (object): Console that receives the message.
            message (str): The message sent to the stdin console.
            status (bool): True if the message is sent correctly, False
                otherwise.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError(
            'You must implement "on_stdin_send()" to use the "DebugListener"'
            'class.')
