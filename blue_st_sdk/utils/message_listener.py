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


# IMPORT

import sys
import os
from enum import Enum
from abc import ABCMeta
from abc import abstractmethod

# INTERFACES

class MessageListener(object):
    """Interface used by the :class:`blue_st_sdk.firmware_upgrade.firmware_upgrade.FirmwareUpgrade`
    class to notify changes of the firmware uprgade process.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_message_send_complete(self, debug_console, msg, bytes_sent):
        raise NotImplementedError('You must implement '
                                  '"on_message_send_complete()" to '
                                  'use the "MessageListener" class.')

    
    @abstractmethod
    def on_message_send_error(self, debug_console, msg, error):
        raise NotImplementedError('You must implement '
                                  '"on_message_send_error()" to '
                                  'use the "MessageListener" class.')

    
    @abstractmethod
    def on_message_rcv_complete(self, debug_console, msg, bytes_sent):
        raise NotImplementedError('You must implement '
                                  '"on_message_rcv_complete()" to '
                                  'use the "MessageListener" class.')
    
    @abstractmethod
    def on_message_rcv_error(self, debug_console, msg, error):
        raise NotImplementedError('You must implement '
                                  '"on_message_rcv_error()" to '
                                  'use the "MessageListener" class.')
