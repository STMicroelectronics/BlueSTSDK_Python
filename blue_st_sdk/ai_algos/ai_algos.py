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


"""ai_algos_support

The ai_algos module is responsible for getting/setting supported algo firmware
on the node device via Bluetooth Low Energy (BLE).
"""


# IMPORT

import sys
import os
import time
import threading
from enum import Enum

from blue_st_sdk.node import NodeType
from blue_st_sdk.debug_console import DebugConsoleListener
from blue_st_sdk.utils.number_conversion import LittleEndian
from blue_st_sdk.utils.python_utils import lock


# CLASSES

class AIAlgos(object):
    """Class that implements the get/set of AI Algos from/to a Nucleo device.
    """

    def __init__(self, debug_console):

        self._debug_console = debug_console
        """Debug console where to send commands."""

        self._debug_console_listener = None
        """Listener to nucleo debug console events."""

        self._listeners = []
        """List of listeners to the node changes.
        It is a thread safe list, so a listener can subscribe itself through a
        callback."""
        
        self._algo = 0
        self._har_algo = 'gmp'

    def add_listener(self, listener):
        """Add a listener.
        
        Args:
            listener (:class:`blue_st_sdk.utils.message_listener.MessageListener`):
            Listener to be added.
        """
        if listener is not None:
            with lock(self):
                if not listener in self._listeners:
                    self._listeners.append(listener)

    def remove_listener(self, listener):
        """Remove a listener.

        Args:
            listener (:class:`blue_st_sdk.utils.message_listener.MessageListener`):
            Listener to be removed.
        """
        if listener is not None:
            with lock(self):
                if listener in self._listeners:
                    self._listeners.remove(listener)
    
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

    @classmethod
    def get_console(self, node):
        """Get an instance of this class.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node with which msg has to be sent/received

        Returns:
            :class:`blue_st_sdk.ai_algos.ai_algos.AIAlgos`:
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
                return AIAlgos(debug)
        return None

    def getAvailableCmds(self):
        self._set_listener(AIAlgosDebugConsoleListener(self))
        try:
            self._debug_console_listener.send_message(bytearray("help             ", 'utf-8'))
        except (OSError, ValueError) as e:
            raise e
        return True

    def getAIAlgo(self):
        self._set_listener(AIAlgosDebugConsoleListener(self))
        try:
            self._debug_console_listener.send_message(bytearray("getAIAlgo", 'utf-8'))
        except (OSError, ValueError) as e:
            raise e
        return True
    
    def getAIAlgos(self):
        self._set_listener(AIAlgosDebugConsoleListener(self))
        try:
            self._debug_console_listener.send_message(bytearray("getAllAIAlgo", 'utf-8'))
        except (OSError, ValueError) as e:
            raise e
        return True
   
    def getAIAllAlgoDetails(self):
        self._set_listener(AIAlgosDebugConsoleListener(self))
        try:
            self._debug_console_listener.send_message(bytearray("getAllAIAlgoDetails", 'utf-8'))
        except (OSError, ValueError) as e:
            raise e
        return True

    def setAIAlgo(self, algo_no=1, _har_algo='gmp', start_algo='asc'):
        self._set_listener(AIAlgosDebugConsoleListener(self))        
        try:
            self._debug_console_listener.send_message(bytearray("har stop ign_wsdm",  'utf-8'))
            self._debug_console_listener.send_message(bytearray("asc stop         ",  'utf-8'))
            self._algo = algo_no
            self._har_algo = _har_algo
            self._debug_console_listener.send_message(bytearray("setAIAlgo "+str(algo_no)+"     ",  'utf-8'))
            self._debug_console_listener.send_message(bytearray("asc start        ",  'utf-8'))
            self._debug_console_listener.send_message(bytearray("har start "+str(_har_algo)+"     ",  'utf-8'))
        except (OSError, ValueError) as e:
            raise e
        return True

    def stopAlgos(self):
        self._set_listener(AIAlgosDebugConsoleListener(self))
        try:
            self._debug_console_listener.send_message(bytearray("har stop ign_wsdm",  'utf-8'))
            time.sleep(1)
            self._debug_console_listener.send_message(bytearray("asc stop         ",  'utf-8'))
            time.sleep(1)            
        except (OSError, ValueError) as e:
            raise e
        return True

    def startAlgos(self):
        self._set_listener(AIAlgosDebugConsoleListener(self))
        try:            
            self._debug_console_listener.send_message(bytearray("asc start        ",  'utf-8'))
            time.sleep(1)
            self._debug_console_listener.send_message(bytearray("har start "+str(self._har_algo)+"     ",  'utf-8'))
            time.sleep(1)                     
        except (OSError, ValueError) as e:
            raise e
        return True

    def startHARAlgo(self, har_algo='gmp'):        
        self._set_listener(AIAlgosDebugConsoleListener(self))
        try:
            self._debug_console_listener.send_message(bytearray("har stop "+str(har_algo)+"     ",  'utf-8'))
            time.sleep(1)
            self._har_algo = har_algo
            self._debug_console_listener.send_message(bytearray("har start "+str(har_algo)+"     ",  'utf-8'))
            time.sleep(1)
        except (OSError, ValueError) as e:
            raise e
        return True

    def startASCAlgo(self):
        self._set_listener(AIAlgosDebugConsoleListener(self))
        try:
            self._debug_console_listener.send_message(bytearray("asc stop         ",  'utf-8'))
            time.sleep(1)
            self._debug_console_listener.send_message(bytearray("asc start        ",  'utf-8'))
            time.sleep(1)
        except (OSError, ValueError) as e:
            raise e
        return True

class AIAlgosDebugConsoleListener(DebugConsoleListener):
    """Class that handles the send/receive of messages to a device via
    Bluetooth."""

    MSG_SEND_COMMAND = b'sendMsg'
    """Message send command."""

    ACK_MSG = u'\u0001'  # Unicode character
    """Acknowledgement message."""

    MAX_MSG_SIZE = 16
    """The STM32L4 Family can write only 8 bytes at a time, thus sending a
    multiple of 8 bytes simplifies the code."""

    LOST_MSG_TIMEOUT_ms = 1000
    """Timeout for sending a message."""

    def __init__(self, aialgo_console):
        DebugConsoleListener.__init__(self)
        self._message = ""
        self._rcv_message = ""
        self._aialgo_console = aialgo_console
        self._bytes_sent = 0

    
    def send_message(self, message):
        self._message = message
        # Sending data
        self._aialgo_console._debug_console.write(message)

    def on_stdout_receive(self, debug_console, message):
        self._rcv_message = self._rcv_message + message
        # if message.lower() == self.ACK_MSG.lower():
        if message.endswith('\n'):
            for listener in self._aialgo_console._listeners:
                listener.on_message_send_complete(self._aialgo_console, self._rcv_message, self._bytes_sent)

    def on_stderr_receive(self, debug_console, message):
        print('on_stderr_receive: ' + message)
        pass

    def on_stdin_send(self, debug_console, message, status):
        # print('on_stdin_send: '+ message)
        pass

