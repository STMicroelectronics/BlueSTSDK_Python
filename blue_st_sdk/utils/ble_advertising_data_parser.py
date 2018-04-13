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


"""ble_advertising_data_parser

The ble_advertising_data_parser module contains tools to parse the advertising
data coming from Bluetooth devices and recognized by the BlueSTSDK.
"""


# IMPORT

import blue_st_sdk.node
from blue_st_sdk.utils.blue_st_exceptions import InvalidBLEAdvertisingDataException


# CLASSES


class BLEAdvertisingDataParser(object):
    """Parse the advertising data sent by a device that follows the BlueST
    protocol.
    
    It raises an exception if the advertising data is not valid.
    """

    # Note: the Bluepy library hides the field-type.
    ADVERTISING_DATA_MANUFACTURER_LENGTH_1 = 7
    """Allowed length for the advertising data manufacturer in bytes.""" 
    
    ADVERTISING_DATA_MANUFACTURER_LENGTH_2 = 13
    """Allowed length for the advertising data manufacturer in bytes.""" 

    VERSION_PROTOCOL_SUPPORTED_MIN = 0x01
    """Minimum version protocol supported."""
    
    VERSION_PROTOCOL_SUPPORTED_MAX = 0x01
    """Maximum version protocol supported."""

    _COMPLETE_LOCAL_NAME = 0x09
    """Code identifier for the complete local name."""
    
    _TX_POWER = 0x0A
    """Code identifier for the transmission power."""

    _MANUFACTURER_SPECIFIC_DATA = 0xFF
    """Code identifier for themanufacturer data."""

    _NAME_UNKNOWN = 'UNKNOWN'
    """Unknown name."""

    def __init__(self, advertising_data):
        """Constructor.
        
        Args:
            advertising_data (str): BLE advertising_data.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidBLEAdvertisingDataException`
                is raised if the advertising data is not well formed.
        """

        # Device name (str).
        self._name = self._NAME_UNKNOWN

        # Device transmission power (int).
        self._tx_power = -1

        # Device MAC address (str).
        self._address = None

        # Bitmask that keeps track of the available features (int).
        self._feature_mask = -1

        # Device identifier (int).
        self._device_id = -1

        # Device Protocol Version (int).
        self._protocol_version = -1

        # Board's type (NodeType).
        self._board_type = None

        # Board in sleeping status (bool).
        self._board_sleeping = None

        # Manufacturer specific data (str).
        self._manufacturer_specific_data = None

        # Getting data.
        for data in advertising_data:
            if data[0] == self._COMPLETE_LOCAL_NAME:
                self._name = data[2].encode('utf-8')
            elif data[0] == self._TX_POWER:
                self._tx_power = data[2]
            elif data[0] == self._MANUFACTURER_SPECIFIC_DATA:
                self._manufacturer_specific_data = data[2]

        if self._manufacturer_specific_data is None:
            raise InvalidBLEAdvertisingDataException(
                ' ' + self._name + ': ' \
                '"Manufacturer specific data" is mandatory: ' \
                'the advertising data does not contain it.'
            )

        try:
            # Parse manufacturer specific data.
            self._parse_manufacturer_specific_data(self._manufacturer_specific_data)
        except InvalidBLEAdvertisingDataException as e:
            raise e

    def _parse_manufacturer_specific_data(self, manufacturer_specific_data):
        """Parse the manufacturer specific data.
    
        Args:
            manufacturer_specific_data (str): The manufacturer specific data.
    
        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidBLEAdvertisingDataException`
                is raised if the advertising data is not well formed.
        """
        length = len(manufacturer_specific_data.decode('hex')) + 1  # Adding 1 byte of the field-type, which is hidden by the Bluepy library.
        if length != self.ADVERTISING_DATA_MANUFACTURER_LENGTH_1 and length != self.ADVERTISING_DATA_MANUFACTURER_LENGTH_2:
            raise InvalidBLEAdvertisingDataException(
                ' ' + self._name + ': ' \
                '"Manufacturer specific data" must be of length "' \
                + str(self.ADVERTISING_DATA_MANUFACTURER_LENGTH_1) + '" or "' \
                + str(self.ADVERTISING_DATA_MANUFACTURER_LENGTH_2) + '", not "' + str(length) + '".'
            )

        self._protocol_version = int(manufacturer_specific_data[0:2], 16)
        if (self._protocol_version < self.VERSION_PROTOCOL_SUPPORTED_MIN) or \
           (self._protocol_version > self.VERSION_PROTOCOL_SUPPORTED_MAX):
            raise InvalidBLEAdvertisingDataException(
                ' ' + self._name + ': ' \
                'Protocol version "' + str(self._protocol_version) + '" unsupported. ' \
                'Version must be in [' + str(self.VERSION_PROTOCOL_SUPPORTED_MIN) + '..' + str(self.VERSION_PROTOCOL_SUPPORTED_MAX) + '].'
            )

        self._device_id = int(manufacturer_specific_data[2:4], 16)
        self._device_id = self._device_id & 0xFF if self._device_id & 0x80 == 0x80 else self._device_id & 0x1F

        try:
            self._board_type = self._get_node_type(self._device_id)
        except InvalidBLEAdvertisingDataException as e:
            raise e

        self._board_sleeping = self._get_node_sleeping_status(int(manufacturer_specific_data[2:4], 16))
        self._feature_mask = int(manufacturer_specific_data[4:12], 16)
        self._address = manufacturer_specific_data[12:24] if length == self.ADVERTISING_DATA_MANUFACTURER_LENGTH_2 else None

    def _get_node_type(self, device_id):
        """Get the node's type.
    
        Args:
            device_id (int): Device identifier.
        
        Returns:
            :class:`blue_st_sdk.node.NodeType`: The node's type.
        
        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidBLEAdvertisingDataException`
                is raised if the advertising data is not well formed.
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
        if temp >= 0x80 and temp <= 0xFF:
            return blue_st_sdk.node.NodeType.NUCLEO
        return blue_st_sdk.node.NodeType.GENERIC

    @classmethod
    def _get_node_sleeping_status(self, node_type):
        """Parse the node type field to check whether the board is sleeping.
    
        Args:
            node_type (int): Node type.
        
        Returns:
            True if the board is sleeping, False otherwise.
        """
        return ((node_type & 0x80) != 0x80 and ((node_type & 0x40) == 0x40))

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

    def get_protocol_version(self):
        """Get the device protocol version.

        Returns:
            int: The device protocol version.
        """
        return self._protocol_version

    def get_board_type(self):
        """Get the board's type.
        
        Returns:
            The board's type.
        """
        return self._board_type

    def get_board_sleeping(self):
        """Get the sleeping status.

        Returns:
            True if the board is sleeping, False otherwise.
        """
        return self._board_sleeping

    def get_device_id(self):
        """Get the device identifier.

        Returns:
            int: The device identifier.
        """
        return self._device_id

    def get_feature_mask(self):
        """Get the bitmask that keeps track of the available features.

        Returns:
            The bitmask that keeps track of the available features.
        """
        return self._feature_mask

    def __str__(self):
        """Print the advertising_data.
        
        Returns:
            str: A string that contains the advertising_data.
        """
        return "Name: " + self._name + \
               "\n\tTxPower: " + self._tx_power + \
               "\n\tAddress: " + self._address + \
               "\n\tFeature Mask: " + self._feature_mask + \
               "\n\tProtocol Version: " + self._protocol_version
