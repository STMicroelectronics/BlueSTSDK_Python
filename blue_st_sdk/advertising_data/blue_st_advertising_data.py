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


"""blue_st_advertising_data

The blue_st_advertising_data module keeps the information contained within the
advertising data coming from Bluetooth devices implementing the Blue ST protocol.
"""


# IMPORT

from blue_st_sdk.advertising_data.ble_advertising_data import BLEAdvertisingData


# CLASSES

class BlueSTAdvertisingData(BLEAdvertisingData):
    """Advertising data sent by a device that follows the BlueST protocol."""

    def __init__(self, name, tx_power, address, device_id, device_type,
        protocol_version, feature_mask, sleeping):
        """Constructor.

        Args:
            name (str): The device name.
            tx_power (int): The device transmission power.
            address (str): The device MAC address.
            device_id (int): The device identifier.
            device_type (:class:`blue_st_sdk.node.NodeType`): The type of the
            node.
            protocol_version (int): The device Protocol Version.
            feature_mask (int): The bitmask that keeps track of the available
            features.
            sleeping (bool): The device sleeping status.
        """
        # Device name.
        self._name = name

        # Device transmission power.
        self._tx_power = tx_power

        # Device MAC address.
        self._address = address

        # Device identifier.
        self._device_id = device_id

        # Device type.
        self._device_type = device_type

        # Device Protocol Version.
        self._protocol_version = protocol_version

        # Bitmask that keeps track of the available features.
        self._feature_mask = feature_mask

        # Sleeping status.
        self._sleeping = sleeping

    def get_name(self):
        """Get the device name.
    
        Returns:
            str: The device name.
        """
        return self._name

    def get_tx_power(self):
        """Get the device transmission power in mdb.

        Returns:
            int: The device transmission power in mdb.
        """
        return self._tx_power

    def get_address(self):
        """Get the device MAC address.

        Returns:
            str: The device MAC address.
        """
        return self._address

    def get_device_id(self):
        """Get the device identifier.

        Returns:
            int: The device identifier.
        """
        return self._device_id

    def get_device_type(self):
        """Get the device's type.
        
        Returns:
            The device's type.
        """
        return self._device_type

    def get_protocol_version(self):
        """Get the device protocol version.

        Returns:
            int: The device protocol version.
        """
        return self._protocol_version

    def get_feature_mask(self):
        """Get the bitmask that keeps track of the available features.

        Returns:
            The bitmask that keeps track of the available features.
        """
        return self._feature_mask

    def is_sleeping(self):
        """Check whether the device is sleeping.

        Returns:
            True if the device is sleeping, False otherwise.
        """
        return self._sleeping

    def __str__(self):
        """Print the advertising_data.
        
        Returns:
            str: A string that contains the advertising_data.
        """
        return "Name: " + self._name + \
               "\n\tTxPower: " + self._tx_power + \
               "\n\tAddress: " + self._address + \
               "\n\tProtocol Version: " + self._protocol_version + \
               "\n\tFeature Mask: " + self._feature_mask
