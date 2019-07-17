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


"""ble_advertising_data

The ble_advertising_data module keeps the information contained within the
advertising data coming from Bluetooth devices.
"""


# IMPORT

from abc import ABCMeta
from abc import abstractmethod


# INTERFACES

class BLEAdvertisingData(object):
    """Interface that defines the advertising data."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_name(self):
        """Get the device name.
    
        Returns:
            str: The device name.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "get_name()" to '
                                  'use the "BLEAdvertisingData" class.')

    @abstractmethod
    def get_tx_power(self):
        """Get the device transmission power in mdb.

        Returns:
            int: The device transmission power in mdb.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "get_tx_power()" to '
                                  'use the "BLEAdvertisingData" class.')

    @abstractmethod
    def get_address(self):
        """Get the device MAC address.

        Returns:
            str: The device MAC address.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "get_address()" to '
                                  'use the "BLEAdvertisingData" class.')

    @abstractmethod
    def get_protocol_version(self):
        """Get the device protocol version.

        Returns:
            int: The device protocol version.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "get_protocol_version()" '
                                  'to use the "BLEAdvertisingData" class.')

    @abstractmethod
    def get_device_type(self):
        """Get the device's type.
        
        Returns:
            The device's type.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "get_device_type()" to '
                                  'use the "BLEAdvertisingData" class.')

    @abstractmethod
    def get_device_id(self):
        """Get the device identifier.

        Returns:
            int: The device identifier.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "get_device_id()" to '
                                  'use the "BLEAdvertisingData" class.')

    @abstractmethod
    def get_feature_mask(self):
        """Get the bitmask that keeps track of the available features.

        Returns:
            The bitmask that keeps track of the available features.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "get_feature_mask()" to '
                                  'use the "BLEAdvertisingData" class.')

    @abstractmethod
    def is_device_sleeping(self):
        """Check whether the device is sleeping.

        Returns:
            True if the device is sleeping, False otherwise.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "is_device_sleeping()" to '
                                  'use the "BLEAdvertisingData" class.')
