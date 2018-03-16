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

import BlueSTSDK.Manager
import BlueSTSDK.Node
from BlueSTSDK.Utils.InvalidBLEAdvertisingDataFormat import InvalidBLEAdvertisingDataFormat


# CLASSES

# 
# Parse the advertising data sent by a device that follows the BlueST protocol.
# It throws an exception if the advertising data is not valid.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#  
class BLEAdvertisingDataParser(object):

	# Note: the Bluepy library hides the field-type.
	ADVERTISING_DATA_MANUFACTURER_LENGTH_1 = 7
	ADVERTISING_DATA_MANUFACTURER_LENGTH_2 = 13
	VERSION_PROTOCOL_SUPPORTED_MIN = 0x01
	VERSION_PROTOCOL_SUPPORTED_MAX = 0x01
	COMPLETE_LOCAL_NAME = 0x09
	TX_POWER = 0x0A
	MANUFACTURER_SPECIFIC_DATA = 0xFF
	UNKNOWN = "UNKNOWN"

	# Device name (String).
	_name = None

	# Device transmission power (Integer).
	_tx_power = -1

	# Device MAC address (String).
	_address = None

	# Bitmask that keeps track of the available features (Integer).
	_feature_mask = -1

	# Device identifier (Integer).
	_device_id = -1

	# Device Protocol Version (Integer).
	_protocol_version = -1

	# Board's type (NodeType).
	_board_type = None

	# Board in sleeping state (Boolean).
	_board_sleeping = None

	# 
	# Constructor.
	#
	# @param  advertising_data BLE advertising_data.
	# @throws InvalidBLEAdvertisingDataFormat thrown if the advertising data
	#         doesn't respect the BlueST format.
	#
	def __init__(self, advertising_data):
		manufacturer_specific_data = None
		self._name = self.UNKNOWN

		# Printing advertising data.
		#print advertising_data

		# Getting data.
		for data in advertising_data:
			if data[0] == self.COMPLETE_LOCAL_NAME:
				self._name = data[2]
			elif data[0] == self.TX_POWER:
				self._tx_power = data[2]
			elif data[0] == self.MANUFACTURER_SPECIFIC_DATA:
				manufacturer_specific_data = data[2]

		if manufacturer_specific_data == None:
			raise InvalidBLEAdvertisingDataFormat(
				"\"Manufacturer specific data\" is mandatory: the advertising data does not contain it."
			)
			return None

		try:
			# Parse manufacturer specific data.
			self.parseManufacturerSpecificData(manufacturer_specific_data)
		except InvalidBLEAdvertisingDataFormat as e:
			raise e
			return None

	# 
	# Parse the manufacturer specific data.
	#
	# @param  manufacturer_specific_data The manufacturer specific data.
	# @throws InvalidBLEAdvertisingDataFormat thrown if the advertising data
	#         doesn't respect the BlueST format.
	#
	def parseManufacturerSpecificData(self, manufacturer_specific_data):

		length = len(manufacturer_specific_data.decode('hex')) + 1 # Adding 1 byte of the field-type, which is hidden by the Bluepy library.
		if length != self.ADVERTISING_DATA_MANUFACTURER_LENGTH_1 and length != self.ADVERTISING_DATA_MANUFACTURER_LENGTH_2:
			raise InvalidBLEAdvertisingDataFormat(
				"\"Manufacturer specific data\" must be of length \"" + \
				str(self.ADVERTISING_DATA_MANUFACTURER_LENGTH_1) + "\" or \"" + \
				str(self.ADVERTISING_DATA_MANUFACTURER_LENGTH_2) + "\", not \"" + str(length) + "\"."
			)
			return

		self._protocol_version = int(manufacturer_specific_data[0:2], 16)
		if (self._protocol_version < self.VERSION_PROTOCOL_SUPPORTED_MIN) or \
		   (self._protocol_version > self.VERSION_PROTOCOL_SUPPORTED_MAX):
			raise InvalidBLEAdvertisingDataFormat(
				"Protocol version \"" + str(self._protocol_version) + "\" unsupported. " \
				"Version must be in [" + str(self.VERSION_PROTOCOL_SUPPORTED_MIN) + ".." + str(self.VERSION_PROTOCOL_SUPPORTED_MAX) + "]."
			)
			return

		self._device_id = int(manufacturer_specific_data[2:4], 16)
		self._device_id = self._device_id & 0xFF if self._device_id & 0x80 == 0x80 else self._device_id & 0x1F

		try:
			self._board_type = self.getNodeType(self._device_id)
		except InvalidBLEAdvertisingDataFormat as e:
			raise e
			return

		self._board_sleeping = self.getNodeSleepingState(int(manufacturer_specific_data[2:4], 16))
		self._feature_mask = int(manufacturer_specific_data[4:12], 16)
		self._address = manufacturer_specific_data[12:24] if length == self.ADVERTISING_DATA_MANUFACTURER_LENGTH_2 else None

    #
    # Get the node's type.
    #
    # @param device_id Device identifier.
    # @return The node's type.
    # @throws InvalidBLEAdvertisingDataFormat if the device identifier is
    #         unknows.
    #
	def getNodeType(self, device_id):
		temp = int(device_id & 0xFF)
		if temp == 0x01:
			return BlueSTSDK.Node.NodeType.STEVAL_WESU1
		if temp == 0x02:
			return BlueSTSDK.Node.NodeType.SENSOR_TILE
		if temp == 0x03:
			return BlueSTSDK.Node.NodeType.BLUE_COIN
		if temp == 0x04:
			return BlueSTSDK.Node.NodeType.STEVAL_IDB008VX
		if temp >= 0x80 and temp <= 0xFF:
			return BlueSTSDK.Node.NodeType.NUCLEO
		return BlueSTSDK.Node.NodeType.GENERIC

	# 
	# Parse the node type field to check whether the board is sleeping.
	#
	# @param  node_type Node type.
	# @return True if the board is sleeping, False otherwise.
	#	  
	@classmethod
	def getNodeSleepingState(self, node_type):
		return ((node_type & 0x80) != 0x80 and ((node_type & 0x40) == 0x40))

	# 
	# Get the device name.
	#
	# @return The device name.
	#	  
	def getName(self):
		return self._name

	# 
	# Get the device transmission power in mdb.
	#
	# @return The device transmission power in mdb.
	#	  
	def getTxPower(self):
		return self._tx_power

	# 
	# Get the device MAC address.
	#
	# @return The device MAC address.
	#	  
	def getAddress(self):
		return self._address

	# 
	# Get the device protocol version.
	#
	# @return The device protocol version.
	#	  
	def getProtocolVersion(self):
		return self._protocol_version

	#
	# Get the board's type.
	#
	# @return The board's type.
	#
	def getBoardType(self):
		return self._board_type

	#
	# Get the sleeping status.
	#
	# @return The board sleeping status.
	#	  
	def getBoardSleeping(self):
		return self._board_sleeping

	# 
	# Get the device identifier.
	#
	# @return The device identifier.
	#	  
	def getDeviceId(self):
		return self._device_id

	# 
	# Get the bitmask that keeps track of the available features.
	#
	# @return The bitmask that keeps track of the available features.
	#	  
	def getFeatureMask(self):
		return self._feature_mask

	# 
	# Print the advertising_data.
	# @return A string that contains the advertising_data.
	#	  
	def __str__(self):
		return "Name: " + self._name + \
			   "\n\tTxPower: " + self._tx_power + \
			   "\n\tAddress: " + self._address + \
			   "\n\tFeature Mask: " + self._feature_mask + \
			   "\n\tProtocol Version: " + self._protocol_version
