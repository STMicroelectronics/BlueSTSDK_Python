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

from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from bluepy.btle import Peripheral, DefaultDelegate
from enum import Enum
import struct
import itertools
import logging

import BlueSTSDK.Manager
from BlueSTSDK.PythonUtils import lock
from BlueSTSDK.Utils.BLENodeDefines import FeatureCharacteristic
from BlueSTSDK.Utils.NumberConversion import LittleEndian
from BlueSTSDK.Utils.BLEAdvertisingDataParser import BLEAdvertisingDataParser
from BlueSTSDK.Utils.InvalidBLEAdvertisingDataFormat import InvalidBLEAdvertisingDataFormat
from BlueSTSDK.Utils.UnwrapTimestamp import UnwrapTimestamp
from BlueSTSDK.Utils.UUIDToFeatureMap import UUIDToFeatureMap



# CLASSES

#
# Object that can export features using Bluetooth Low Energy (BLE) transmission.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class Node(Peripheral, object):

	# Notifications.
	NOTIFICATION_ON = struct.pack("BB", 0x01, 0x00)
	NOTIFICATION_OFF = struct.pack("BB", 0x00, 0x00)

	# Time to wait before re-trying to send a command to the BLE.
	#RETRY_COMMAND_DELAY_ms = 300
	RETRY_COMMAND_DELAY_s = 1

	# Number of threads to be used to notify the listeners.
	NUMBER_OF_THREADS = 5

	#
	# Constructor.
	#
	# @param device BLE device.
	# @throws InvalidBLEAdvertisingDataFormat if the advertising data is not
	#		  well formed.
	#
	def __init__(self, device):

		# Creating an un-connected "Peripheral" object.
		# You must call the "connect()" method on this object (passing it a
		# device address) before it will be usable.
		Peripheral.__init__(self)
		self.withDelegate(NodeDelegate(self))

		# Advertising data.
		try:
			self._advertising_data = BLEAdvertisingDataParser(device.getScanData())
		except InvalidBLEAdvertisingDataFormat as e:
			raise e

		# BLE device.
		# Python's "ScanEntry" object, equivalent to Android's "BluetoothDevice" object.
		self._device = device
		
		# Received Signal Strength Indication.
		self._rssi = device.rssi

		# Last update to the Received Signal Strength Indication.
		self._last_rssi_update = None

		# Status.
		self._status = NodeStatus.INIT

		# Pool of thread used to notify the listeners.
		self._thread_pool = ThreadPoolExecutor(Node.NUMBER_OF_THREADS)

		# List of listeners to the node changes.
		# It is a thread safe list, so a listener can subscribe itself through a
		# callback.
		self._listeners = []

		# List of all the available features as claimed by the advertising data.
		# (No duplicates.)
		self._available_features = []

		# Mask to feature dictionary: there is an entry for each one-high-bit 32-bit
		# mask.
		self._mask_to_feature_dic = {}

		# UUID to list of external features dictionary: there is an entry for each
		# list of exported external features.
		# Node: A UUID may export more features.
		self._external_uuid_to_features_dic = UUIDToFeatureMap() #mExternalCharFeatures

		# Characteristic's handle to list of features dictionary: it tells which
		# features to update when new data from a characteristic are received.
		# Node: A UUID may export more features.
		# Note: The same feature may be added to different list of features in case
		#	   more characteristics have the same corresponding bit set to high.
		self._update_char_handle_to_features_dict = {} #mCharFeatureMap

		# Characteristic's handle to characteristic dictionary.
		self._char_handle_to_characteristic_dict = {}

		# Unwrap timestamp reference.
		self._unwrap_timestamp = UnwrapTimestamp()

		# Updating node.
		self.updateRSSI(self._rssi)
		self.updateNodeStatus(NodeStatus.IDLE)

		# Building available features.
		self.buildAvailableFeatures()

	#
	# Open a connection to the node.
	#
	# @param user_defined_features User-defined feature to be registered.
	#
	def connect(self, user_defined_features=None):
		self.updateNodeStatus(NodeStatus.CONNECTING)
		#Start the connection: stop receiving advertising data, deleting the timeout.
		#if(mHandler!=null) mHandler.removeCallbacks(mSetNodeLost);
		#mUserAskToDisconnect=false;
		self.addExternalFeatures(user_defined_features)
		#mBleThread.post(mConnectionTask);
		super(Node, self).connect(self.getTag(), "random")

		# Getting services.
		services = self.getServices()
		if not services:
			self.updateNodeStatus(NodeStatus.DEAD)
			return

		# Handling Debug, Config, and Feature characteristics.
		for service in services:
			#TBD
			#if service.uuid == Debug.DEBUG_BLUESTSDK_SENSOR_SERVICE_UUID:
				# Handling Debug.
			#	pass
			#elif service.uuid == Config.CONFIG_BLUESTSDK_SENSOR_SERVICE_UUID:
				# Handling Config.
			#	pass
			#else:
			# Getting characteristics.
			characteristics = service.getCharacteristics()
			i = 0
			for characteristic in characteristics:

				# Storing characteristics' handle to characteristic mapping.
				self._char_handle_to_characteristic_dict[characteristic.getHandle()] = characteristic

				# Building characteristics' features.
				if FeatureCharacteristic.isFeatureCharacteristic(characteristic.uuid):
					self.buildFeatures(characteristic)
				elif bool(self._external_uuid_to_features_dic) and characteristic.uuid in self._external_uuid_to_features_dic:
					self.buildFeaturesKnownUUID(characteristic, self._external_uuid_to_features_dic[characteristic.uuid])

		# For each feature store a reference to the characteristic offering the
		# feature, useful to enable/disable notifications on the characteristic
		# itself.
		self._setFeaturesCharacteristics()

		# Change node's status.
		self.updateNodeStatus(NodeStatus.CONNECTED)

	#
	# Close the connection to the node.
	#
	def disconnect(self):
		if not self.isConnected():
			return
		#mUserAskToDisconnect=true
		self.updateNodeStatus(NodeStatus.DISCONNECTING)
		#waitCompleteAllDescriptorWriteRequest(mDisconnectTask);
		#mHandler.postDelayed(mSetNodeLost, NODE_LOST_TIMEOUT_MS)
		super(Node, self).disconnect()
		self.updateNodeStatus(NodeStatus.IDLE)

	#
	# Add available features to an already discovered device, prior to
	# connecting to it.
	# If a UUID is already known, it will be overwritten with the new list of
	# available features.
	#
	# E.g.:
    # # Adding a 'FeatureHeartRate' feature to a Nucleo device and mapping it to
    # # the standard '00002a37-0000-1000-8000-00805f9b34fb' Heart Rate
    # # Measurement characteristic.
    # map = UUIDToFeatureMap()
    # map.put(uuid.UUID('00002a37-0000-1000-8000-00805f9b34fb'), BlueSTSDK.Features.StandardCharacteristics.FeatureHeartRate.FeatureHeartRate)
    # node.addExternalFeatures(map)
    # # Connecting to the node.
    # node.connect()
    #
    # Otherwise, it is possible to add available features before performing the
    # discovery process (see Manager.addFeaturesToNode()).
	#
	# @param user_defined_features User-defined feature to be added.
	#
	def addExternalFeatures(self, user_defined_features):
		if user_defined_features != None:
			self._external_uuid_to_features_dic.putAll(user_defined_features)

	#
	# Create a feature from its class.
	#
	# @param feature_class Feature class to build.
	# @return The feature object built.
	#
	def buildFeatureFromClass(self, feature_class):
		return feature_class(self)

	#
	# Build the exported features of a BLE characteristic, and add them to the
	# dictionary of the features to be updated.
	#
	# @param characteristic The BLE characteristic.
	#
	def buildFeatures(self, characteristic):
		# Extracting the feature mask from the characteristic's UUID.
		feature_mask = FeatureCharacteristic.extractFeatureMask(characteristic.uuid)
		# Looking for the exported features in reverse order to get them in the
		# correct order in case of characteristic that exports multiple features.
		features = []
		mask = 1 << 31
		for i in range(0, 32):
			if (feature_mask & mask) != 0:
				if mask in self._mask_to_feature_dic:
					feature = self._mask_to_feature_dic[mask]
					if feature != None:
						feature.setEnable(True)
						features.append(feature)
			mask = mask >> 1

		# If the features are valid, add an entry for the corresponding
		# characteristic.
		if features:
			self._update_char_handle_to_features_dict[characteristic.getHandle()] = features

	#
	# Build the given features, and add them to the dictionary of the features
	# to be updated.
	#
	# @param characteristic The BLE characteristic.
	# @param features_class The list of features-class to build.
	#
	def buildFeaturesKnownUUID(self, characteristic, features_class):
		# Build the features.
		features = []
		for feature_class in features_class:
			feature = self.buildFeatureFromClass(feature_class)
			if feature != None:
				feature.setEnable(True)
				features.append(feature)
				self._available_features.append(feature)

		# If the features are valid, add an entry for the corresponding
		# characteristic.
		if features:
			self._update_char_handle_to_features_dict[characteristic.getHandle()] = features

	#
	# Build a list of possible features that this node can export by relying on
	# the advertising data.
	#
	def buildAvailableFeatures(self):
		# Getting device identifier and feature mask from advertising data.
		device_id = self._advertising_data.getDeviceId()
		feature_mask = self._advertising_data.getFeatureMask()

		# Getting the dictionary that maps feature-masks to feature-classes
		# related to the advertising data's device identifier.
		decoder = BlueSTSDK.Manager.Manager.getNodeFeatures(device_id)

		# Initializing list of available-features and mask-to-feature dictionary.
		self._available_features = []
		self._mask_to_feature_dic = {}

		# Building features as claimed by the advertising data's feature-mask.
		mask = 1
		for i in range(0, 32):
			if feature_mask & mask != 0:
				feature_class = decoder.get(mask)
				if feature_class != None:
					feature = self.buildFeatureFromClass(feature_class)
					if feature != None:
						self._available_features.append(feature)
						self._mask_to_feature_dic[mask] = feature
					else:
						logging.error('Impossible to build the feature \"' + feature_class.getSimpleName() + '\".')
			mask = mask << 1

	# For each feature store a reference to the characteristic offering the
	# feature, useful to enable/disable notifications on the characteristic
	# itself.
	# By design, the characteristic that offers more features beyond the feature
	# is selected.
	def _setFeaturesCharacteristics(self):
		for feature in self._available_features:
			features_size = 0
			for entry in self._update_char_handle_to_features_dict.items():
				char_handle = entry[0]
				features = entry[1]
				if feature in features:
					if feature._characteristic == None:
						feature._characteristic = self._char_handle_to_characteristic_dict[char_handle]
						features_size = len(features)
					else:
						if len(features) > features_size:
							feature._characteristic = self._char_handle_to_characteristic_dict[char_handle]
							features_size = len(features)

	#
	# Update the features related to a given characteristic.
	#
	# @param char_handle The characteristic's handle to look for.
	# @param data		The data read from the given characteristic.
	# @return True if the characteristic has some features associated to it and
	#		 they have been updated, False otherwise.
	#
	def updateFeatures(self, char_handle, data):
		# Getting the features corresponding to the given characteristic.
		features = self.getCorrespondingFeatures(char_handle)
		if features == None:
			return False

		# Computing the timestamp.
		timestamp = self._unwrap_timestamp.unwrap(LittleEndian.bytesToUInt16(data))

		# Updating the features.
		offset = 2 #Timestamp's bytes.
		for feature in features:
			offset += feature.update(timestamp, data, offset)
		return True

	#
	# Get the features corresponding to the given characteristic.
	#
	# @param char_handle The characteristic's handle to look for.
	# @return The list of features associated to the given characteristic, None
	#		 if the characteristic does not exist.
	#
	def getCorrespondingFeatures(self, char_handle):
		if char_handle in self._update_char_handle_to_features_dict:
			return self._update_char_handle_to_features_dict[char_handle]
		return None

	#
	# Get the tag of the node, i.e. a unique identification, i.e. its MAC
	# address.
	#
	# @return The MAC address of the node.
	#
	def getTag(self):
		return self._device.addr

	#
	# Get the status of the node.
	#
	# @return The status of the node.
	#
	def getStatus(self):
		return self._status

	#
	# Get the name of the node.
	#
	# @return The name of the node.
	#
	def getName(self):
		return self._advertising_data.getName()

	#
	# Get the friendly name of the node.
	#
	# @return The friendly name of the node.
	#
	def getFriendlyName(self):
		if self._friendly_name == None:
			tag = self.getTag()
			if tag != None and len(tag) > 0:
				tag_clean = tag.replace(":", "")
			self._friendly_name = self.getName() + " @" + tag_cleanode.substring(len(tag_clean) - min(6, tag_cleanode.length()), len(tag_clean))
		return self._friendly_name

	#
	# Get the type of the node.
	#
	# @return The type of the node.
	# @throws InvalidBLEAdvertisingDataFormat if the board type is unknown.
	#
	def getType(self):
		return self._advertising_data.getBoardType()

	#
	# Get the type identifier of the node.
	#
	# @return The type identifier of the node.
	#
	def getTypeId(self):
		return self._advertising_data.getDeviceId()

	#
	# Get the device Protocol Version.
	#
	# @return The device Protocol Version.
	#
	def getProtocolVersion(self):
		return self._advertising_data.getProtocolVersion()

	#
	# Get the list of features available in the advertising data, or the list of
	# features of the specific type (class name) if given.
	#
	# @return A list of features. An empty list if no features are found.
	#
	def getFeatures(self, feature_class=None):
		if feature_class == None:
			features = self._available_features
		else:
			features = []
			for feature in self._available_features:
				if isinstance(feature, feature_class):
					features.append(feature)
		return features

	#
	# Search for a specific feature type (class name).
	#
	# @param feature_class Type (class name) of the feature to search for.
	# @return The feature of the given type (class name) if exported by this
	#		 node, None otherwise.
	#
	def getFeature(self, feature_class):
		features = self.getFeatures(feature_class)
		if len(features) != 0:
			return features[0]
		return None

	#
	# Get the node transmission power in mdb.
	#
	# @return The node transmission power in mdb.
	#
	def getTxPowerLevel(self):
		return self._advertising_data.getTxPower()

	#
	# Get the most recent value of RSSI.
	#
	# @return The last known RSSI value.
	#
	def getLastRSSI(self):
		return self._rssi

	#
	# Get the time of the last RSSI update received.
	#
	# @return The time of the last RSSI update received.
	#
	def getLastRSSIUpdateDate(self):
		return self._last_rssi_update

	#
	# Store the new RSSI and call the callback if needed.
	#
	# @param rssi New RSSI value.
	#
	def updateRSSI(self, rssi):
		self._rssi = rssi
		self._last_rssi_update = datetime.now()
		if self._status == NodeStatus.LOST:
			self.updateNodeStatus(NodeStatus.IDLE)

	#
	# Update the status of the node.
	#
	# @param new_status New status.
	#
	def updateNodeStatus(self, new_status):
		old_status = self._status
		self._status = new_status
		for listener in self._listeners:
			# Calling user-defined callback.
			self._thread_pool.submit(listener.onStatusChange(self, new_status.value, old_status.value))


	#
	# Check whether the node is connected.
	#
	# @return True if the node is connected, False otherwise.
	#
	def isConnected(self):
		return self._status == NodeStatus.CONNECTED

	#
	# Check whether the node is sleeping.
	#
	# @return True if the node is sleeping, False otherwise.
	#
	def isSleeping(self):
		return self._advertising_data.getBoardSleeping()

	#
	# Check whether the node is alive.
	# To be called whenever the Manager receives a new advertising data from
	# this node.
	#
	# @param rssi rssi of the last advertising data.
	#
	def isAlive(self, rssi):
		self.updateRSSI(rssi)

	#
	# Check whether the node has a general purpose capability.
	#
	# @return True if the node has a general purpose capability, False otherwise.
	#
	def hasGeneralPurpose(self):
		return self._advertising_data.getBoardHasGP()

	#
	# Update advertising data.
	#
	# @param advertising_data Advertising data.
	#
	def updateAdvertising(self, advertising_data):
		try:
			self._advertising_data = BLEAdvertisingDataParser(advertising_data)
		except InvalidBLEAdvertisingDataFormat as e:
			logging.error('Error updating advertising data for \"' + self.getName() + '\".')

	#
	# Compare the current node with the given one.
	#
	# @return True if the current node is equal to the given node, False
	#		 otherwise.
	#
	def equals(self, node):
		return isinstance(node, Node) and (node == self or self.getTag() == node.getTag())

	#
	# Check if a characteristics can be read.
	#
	# @param characteristic The characteristic to check.
	# @return True if the characteristic can be read, False otherwise.
	#
	def characteristicCanBeRead(self, characteristic):
		if characteristic != None:
			return "READ" in characteristic.propertiesToString()
		return False

	#
	# Check if a characteristics can be written.
	#
	# @param characteristic The characteristic to check.
	# @return True if the characteristic can be written, False otherwise.
	#
	def characteristicCanBeWritten(self, characteristic):
		if characteristic != None:
			return "WRITE" in characteristic.propertiesToString()
		return False

	#
	# Check if a characteristics can be notified.
	#
	# @param characteristic The characteristic to check.
	# @return True if the characteristic can be notified, False otherwise.
	#
	def characteristicCanBeNotified(self, characteristic):
		if characteristic != None:
			return "NOTIFY" in characteristic.propertiesToString()
		return False

	#
	# Asynchronous request to read a feature.
	# The read value is notified thought a feature listener.
	#
	# @param feature The feature to read.
	# @return False if the feature is not handled by the node or it is disabled,
	#		  True otherwise.
	#
	def readFeature(self, feature):
		if not feature.isEnabled():
			return False

		characteristic = feature.getCharacteristic()
		if not self.characteristicCanBeRead(characteristic):
			return False

		char_handle = characteristic.getHandle()
		data = self.readCharacteristic(char_handle)
		self.updateFeatures(char_handle, data)

		return True

	#
	# Synchronous request to write a feature.
	#
	# @param feature The feature to write to.
	# #param data    The data to be written.
	# @return False if the feature is not handled by the node or it is disabled,
	#		  True otherwise.
	#
	def writeFeature(feature, data):
		if not feature.isEnabled():
			return False

		characteristic = feature.getCharacteristic()
		if not self.characteristicCanBeRead(characteristic):
			return False

		self.writeCharacteristic(characteristic.getHandle(), data, True)

		return True

	#
	# Ask the node to notify when a feature updates its value.
	# The received values are notified thought a feature listener.
	#
	# @param feature The feature.
	# @return False if the feature is not handled by this node, or it is
	#		  disabled, or it is not possible to turn notifications on for it,
	#		  True otherwise.
	#
	def enableNotifications(self, feature):
		if not feature.isEnabled() or feature.getParentNode() != self:
			return False
		characteristic = feature.getCharacteristic()
		if self.characteristicCanBeNotified(characteristic):
			feature.setNotify(True)
			self.writeCharacteristic(characteristic.getHandle() + 1, self.NOTIFICATION_ON, True)
			return True
		return False

	#
	# Ask the node to stop notifying when a feature updates its value.
	#
	# @param feature The feature.
	# @return False if the feature is not handled by this node, or it is
	#		  disabled, or it is not possible to turn notifications off for it,
	#		  True otherwise.
	#
	def disableNotifications(self, feature):
		if not feature.isEnabled() or feature.getParentNode() != self:
			return False
		characteristic = feature.getCharacteristic()
		if self.characteristicCanBeNotified(characteristic):
			feature.setNotify(False)
			if not self.characteristicHasOtherNotifyingFeatures(characteristic, feature):
				self.writeCharacteristic(characteristic.getHandle() + 1, self.NOTIFICATION_OFF, True)
			return True
		return False

	#
	# Check whether notifications are enabled for a feature.
	# 
	# @param feature The feature.
	# @return True if notifications are enabled, False otherwise.
	#
	def notificationsEnabled(self, feature):
		return feature.isNotifying()

	#
	# Check whether a characteristic has other enabled features beyond the given
	# one.
	#
	# @param characteristic The characteristic.
	# @param feature		The feature to disable.
	# @return True if the characteristic has other enabled features beyond the
	#		  given one, False otherwise.
	#
	def characteristicHasOtherNotifyingFeatures(self, characteristic, feature):
		features = self.getCorrespondingFeatures(characteristic.getHandle())
		for feature_entry in features:
			if feature_entry == feature:
				pass
			elif feature_entry.isNotifying():
				return True
		return False

	# 
	# Add a listener.
	#
	# @param listener Listener to be added.
	#
	def addListener(self, listener):
		if listener != None:
			with lock(self):
				if not listener in self._listeners:
					self._listeners.append(listener)

	#
	# Remove a listener.
	#
	# @param listener Listener to be removed.
	#
	def removeListener(self, listener):
		if listener != None:
			with lock(self):
				if listener in self._listeners:
					self._listeners.remove(listener)


#
# Interface used to notify changes of a node's status.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class NodeListener(object):
	__metaclass__ = ABCMeta

	#
	# To be called whenever a node changes its status.
	#
	# @param node	    Node that has changed its status.
	# @param new_status New node status.
	# @param old_status Old node status.
	#
	@abstractmethod
	def onStatusChange(self, node, new_status, old_status):
		raise NotImplementedError('You must define "onStatusChange()" to use the "NodeListener" class.')


#
# Delegate class for handling Bluetooth's notifications.
# It is called when Bluetooth's asynchronous events occur.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class NodeDelegate(DefaultDelegate):

	#
	# Constructor.
	#
	def __init__(self, node):
		DefaultDelegate.__init__(self)
		self._node = node

	#
	# Method called whenever a notification arises.
	#
	def handleNotification(self, char_handle, data):
		self._node.updateFeatures(char_handle, data)


#
# Type of node.
#
class NodeType(Enum):

	# Unknown board type.
	GENERIC = 0x00

	# STEVAL-WESU1 board.
	STEVAL_WESU1 = 0x01

	# SensorTile board. 
	SENSOR_TILE = 0x02

	# BlueCoin board.
	BLUE_COIN = 0x03

	# BlueNRG1 / BlueNRG2 STEVAL board.
	STEVAL_IDB008VX = 0x04

	# NUCLEO-based board.
	NUCLEO = 0x05


#
# Status of the node.
#
class NodeStatus(Enum):

	# Dummy initial status.
	INIT = 'INIT'

	# Waiting for a connection and sending advertising data.
	IDLE = 'IDLE'

	# Opening a connection with the node.
	CONNECTING = 'CONNECTING'

	# Connected to the node.
	# This status can be fired 2 times while doing a secure connection using
	# Bluetooth pairing.
	CONNECTED = 'CONNECTED'

	# Closing the connection to the node.
	DISCONNECTING = 'DISCONNECTING'

	# The advertising data has been received for some time, but not anymore.
	LOST = 'LOST'

	# The node disappeared without first disconnecting.
	UNREACHABLE = 'UNREACHABLE'

	# Dummy final status.
	DEAD = 'DEAD'
