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


"""blue_st_advertising_data_parser

The blue_st_advertising_data_parser module contains tools to parse the
advertising data coming from Bluetooth devices implementing the Blue ST protocol.
"""


# IMPORT

import binascii

import blue_st_sdk.node
from blue_st_sdk.advertising_data.ble_advertising_data_parser import BLEAdvertisingDataParser
from blue_st_sdk.advertising_data.blue_st_advertising_data import BlueSTAdvertisingData
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidAdvertisingDataException


# CLASSES

class BlueSTAdvertisingDataParser(BLEAdvertisingDataParser):
    """Advertising data sent by a device that follows the BlueST protocol."""

    # Note: the Bluepy library hides the field-type.
    ADVERTISING_DATA_MANUFACTURER_LENGTH_1 = 7
    """Allowed length for the advertising data manufacturer in bytes.""" 
    
    ADVERTISING_DATA_MANUFACTURER_LENGTH_2 = 13
    """Allowed length for the advertising data manufacturer in bytes.""" 

    VERSION_PROTOCOL_SUPPORTED_MIN = 0x01
    """Minimum version protocol supported."""
    
    VERSION_PROTOCOL_SUPPORTED_MAX = 0x01
    """Maximum version protocol supported."""

    _NO_NAME = 'NO_NAME'
    """Default name of a device with no name specified within the advertising
    data."""

    _COMPLETE_LOCAL_NAME = 0x09
    """Code identifier for the complete local name."""

    _TX_POWER = 0x0A
    """Code identifier for the transmission power."""

    _MANUFACTURER_SPECIFIC_DATA = 0xFF
    """Code identifier for themanufacturer data."""

    @classmethod
    def parse(self, advertising_data):
        """Parse the BLE advertising_data.

        Args:
            advertising_data (list): BLE advertising_data.

        Returns:
            :class:`blue_st_sdk.advertising_data.ble_advertising_data.BLEAdvertisingData`:
            The advertising data information sent by the device.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidAdvertisingDataException`
            is raised if the advertising data is not well formed.
        """
        # Getting data fields out of the received advertising data.
        name = self._NO_NAME
        tx_power = -1
        manufacturer_specific_data = None
        address = None
        device_id = -1
        device_type = blue_st_sdk.node.NodeType.GENERIC
        protocol_version = -1
        feature_mask = -1
        sleeping = False
        for data in advertising_data:
            if data[0] == self._COMPLETE_LOCAL_NAME:
                # Python 2
                #name = data[2].encode('utf-8')
                # Python 3
                name = data[2]
            elif data[0] == self._TX_POWER:
                tx_power = data[2]
            elif data[0] == self._MANUFACTURER_SPECIFIC_DATA:
                manufacturer_specific_data = data[2]

        # Checking the presence of the manufacturer specific data.
        if manufacturer_specific_data is None:
            raise BlueSTInvalidAdvertisingDataException(
                ' ' + name + ': ' \
                '"Manufacturer specific data" is mandatory: ' \
                'the advertising data does not contain it.'
            )

        # Checking the length of the manufacturer specific data.
        # Adding 1 byte of the field-type, which is hidden by the Bluepy library.
        # Python 2.7
        #length = len(manufacturer_specific_data.decode('hex')) + 1
        # Python 3.5
        length = len(
            binascii.unhexlify(
                manufacturer_specific_data.encode('utf-8'))) + 1
        if length != self.ADVERTISING_DATA_MANUFACTURER_LENGTH_1 and \
            length != self.ADVERTISING_DATA_MANUFACTURER_LENGTH_2:
            raise BlueSTInvalidAdvertisingDataException(
                ' ' + name + ': ' \
                '"Manufacturer specific data" must be of length "' \
                + str(self.ADVERTISING_DATA_MANUFACTURER_LENGTH_1) + '" or "' \
                + str(self.ADVERTISING_DATA_MANUFACTURER_LENGTH_2) + '", not "' \
                + str(length) + '".'
            )

        # Getting information from the manufacturer specific data.
        protocol_version = int(manufacturer_specific_data[0:2], 16)
        if (protocol_version < self.VERSION_PROTOCOL_SUPPORTED_MIN) or \
           (protocol_version > self.VERSION_PROTOCOL_SUPPORTED_MAX):
            raise BlueSTInvalidAdvertisingDataException(
                ' ' + name + ': ' \
                'Protocol version "' + str(protocol_version) + \
                '" unsupported. Version must be in [' \
                + str(self.VERSION_PROTOCOL_SUPPORTED_MIN) + '..'
                + str(self.VERSION_PROTOCOL_SUPPORTED_MAX) + '].'
            )
        device_id = int(manufacturer_specific_data[2:4], 16)
        device_id = device_id & 0xFF \
            if device_id & 0x80 == 0x80 else device_id & 0x1F
        device_type = self._get_node_type(device_id)
        sleeping = self._get_node_sleeping_status(
            int(manufacturer_specific_data[2:4], 16))
        feature_mask = int(manufacturer_specific_data[4:12], 16)
        address = manufacturer_specific_data[12:24] \
            if length == self.ADVERTISING_DATA_MANUFACTURER_LENGTH_2 else None

        # Returning a formatted Blue ST Advertising Data object.
        return BlueSTAdvertisingData(name, tx_power, address, device_id,
            device_type, protocol_version, feature_mask, sleeping)

    @classmethod
    def _get_node_type(self, device_id):
        """Get the node's type.

        Args:
            device_id (int): Device identifier.
        
        Returns:
            :class:`blue_st_sdk.node.NodeType`: The node's type.
        """
        temp = int(device_id & 0xFF)
        if temp == 0x01:
            return blue_st_sdk.node.NodeType.STEVAL_WESU1
        if temp == 0x02:
            return blue_st_sdk.node.NodeType.SENSOR_TILE
        if temp == 0x03:
            return blue_st_sdk.node.NodeType.BLUE_COIN
        if temp == 0x04:
            return blue_st_sdk.node.NodeType.STEVAL_IDB008VX
        if temp == 0x05:
            return blue_st_sdk.node.NodeType.STEVAL_BCN002V1
        if temp == 0x06:
            return blue_st_sdk.node.NodeType.SENSOR_TILE_BOX
        if temp >= 0x80 and temp <= 0xFF:
            return blue_st_sdk.node.NodeType.NUCLEO
        return blue_st_sdk.node.NodeType.GENERIC

    @classmethod
    def _get_node_sleeping_status(self, node_type):
        """Parse the node type field to check whether the device is sleeping.
    
        Args:
            node_type (int): Node type.
        
        Returns:
            True if the device is sleeping, False otherwise.
        """
        return ((node_type & 0x80) != 0x80 and ((node_type & 0x40) == 0x40))
