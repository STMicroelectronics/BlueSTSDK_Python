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
import threading
import logging
from bluepy.btle import Scanner, DefaultDelegate, BTLEException

from BlueSTSDK.Node import Node
from BlueSTSDK.Utils import BLENodeDefines, InvalidFeatureBitMaskException
from BlueSTSDK.Utils.InvalidBLEAdvertisingDataFormat import InvalidBLEAdvertisingDataFormat
from BlueSTSDK.PythonUtils import lock, lock_for_object


# CLASSES

#
# Delegate class for scanning Bluetooth Low Energy (BLE) devices.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class ScannerDelegate(DefaultDelegate):

	# Timeouts.
	SCANNING_TIME_DEFAULT_s = 10
	SCANNING_TIME_PROCESS_s = 1

	#
	# Constructor.
	#
	def __init__(self, show_warnings=False):
		DefaultDelegate.__init__(self)
		self._show_warnings = show_warnings

	#
	# Callback to handle new received advertising data packages.
	#
	# <p>
	# It notifies a new node only the first time that the advertising data is
	# received, and only the nodes with a compatible advertising data.
	# If a device has been already built, its rssi value gets updated.
	# </p>
	#
	# @param scan_entry	Remote BLE device.
	# @param is_new_device True if the device has not been seen before, False otherwise.
	# @param is_new_data   True if new or updated advertising data is available.
	#
	def handleDiscovery(self, scan_entry, is_new_device, is_new_data):
		# Getting a Manager's instance.
		manager = Manager.instance()

		# Getting device's address.
		device_address = scan_entry.addr

		try:
			# Updating already discovered node.
			nodes = manager.getNodes()[:]
			for node in nodes:
				if node.getTag() == device_address:
					node.isAlive(scan_entry.rssi)
					node.updateAdvertising(scan_entry.getScanData())
					return

			# Creating new node.
			node = Node(scan_entry)
			#node.addListener(node_listener)
			manager.addNode(node)
		except (BTLEException, InvalidBLEAdvertisingDataFormat) as e:
			if self._show_warnings:
				logging.warning(e)
			return

#
# Scanner class which can be started and stopped asynchronously.
#
# Non-thread-safe.
#
# It is implemented as a thread which checks regularly for the "stopped()"
# condition within the "run()" method; it can be stopped by calling the "stop()"
# method.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class StoppableScanner(threading.Thread):

	#
	# Constructor.
	#
	def __init__(self, timeout_s, *args, **kwargs):
		super(StoppableScanner, self).__init__(*args, **kwargs)
		self._stop_called = threading.Event()
		self._process_done = threading.Event()
		self._scanner = Scanner().withDelegate(ScannerDelegate(show_warnings))
		self._timeout_s = timeout_s

	#
	# Run the thread.
	#
	def run(self):
		self._stop_called.clear()
		self._process_done.clear()
		self._scanner.clear()
		self._scanner.start(passive=False)
		elapsed_time_s = 0
		while True:
			self._scanner.process(ScannerDelegate.SCANNING_TIME_PROCESS_s)
			elapsed_time_s += ScannerDelegate.SCANNING_TIME_PROCESS_s
			if self._stop_called.isSet():
				self._process_done.set()
				break
			if elapsed_time_s >= self._timeout_s:
				self._process_done.set()
				self.stop()
				break

	#
	# Stop the thread.
	#
	def stop(self):
		self._stop_called.set()
		while not self._process_done.isSet():
			pass
		self._scanner.stop()


# 
# Singleton class to manage the discovery of Bluetooth Low Energy (BLE) devices.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class Manager(object):

	# Instance object.
	INSTANCE = None

	# Features decoder dictionary.
	# Dictionary that maps device identifiers to dictionaries that map
	# feature-masks to feature-classes.
	features_decoder_dic = {}

	# Number of threads to be used to notify the listeners.
	NUMBER_OF_THREADS = 5

	#
	# Constructor.
	#
	def __init__(self):
		# Raise an exception if an object has already been instantiated.
		if self.INSTANCE != None:
			raise Exception('An instance of \'Manager\' class already exists.')

		# BLE scanner.
		self._scanner = None

		# Scanning state.
		self._is_scanning = False

		# List of discovered nodes.
		self._discovered_nodes = []

		# Pool of thread used to notify the listeners.
		self._thread_pool = ThreadPoolExecutor(Manager.NUMBER_OF_THREADS)

		# List of listeners to the manager changes.
		# It is a thread safe list, so a listener can subscribe itself through a
		# callback.
		self._listeners = []

	#
	# Getting an instance of the class.
	#
	@classmethod
	def instance(self):
		if self.INSTANCE == None:
			self.INSTANCE = Manager()
		return self.INSTANCE

	#
	# Perform the discovery process that will last <code>timeout_s</code>
	# milliseconds if provided, default milliseconds otherwise.
	#
	# Synchronous method.
	#
	# @param show_warnings Show discovery warning related to non-compliant
	#                      advertising data.
	# @param timeout_s     Time in seconds to wait before stopping the
	#                      discovery process.
	# @return True if the discovery has finished, False if a discovery is
	#		  already running.
	#
	def discover(self, show_warnings=False, timeout_s=0):
		if self.isDiscovering():
			return False
		if timeout_s == 0:
			timeout_s = ScannerDelegate.SCANNING_TIME_DEFAULT_s
		self.notifyDiscoveryChange(True)
		self._scanner = Scanner().withDelegate(ScannerDelegate(show_warnings))
		self._scanner.scan(timeout_s)
		self.notifyDiscoveryChange(False)
		return True

	#
	# Start the discovery process that will last <code>timeout_s</code>
	# milliseconds if provided, default milliseconds otherwise.
	#
	# Asynchronous method, to be followed by a call to "stopDiscovery()".
	#
	# @param show_warnings Show discovery warning related to non-compliant
	#                      advertising data.
	# @param  timeout_s    Time in seconds to wait before stopping the discovery
	#				       process.
	# @return True if the discovery has started, False if a discovery is already
	#		  running.
	#
	def startDiscovery(self, show_warnings=False, timeout_s=0):
		if self.isDiscovering():
			return False
		if timeout_s == 0:
			timeout_s = ScannerDelegate.SCANNING_TIME_DEFAULT_s
		self.notifyDiscoveryChange(True)
		self._scanner_thread = StoppableScanner(show_warnings, timeout_s)
		self._scanner_thread.start()
		return True

	#
	# Stop a discovery process.
	#
	# Asynchronous method, to be preceeded by a call to "startDiscovery()".
	#
	# @return True if the discovery has been stopped, False if there are no
	#		  running discovery processes.
	#
	def stopDiscovery(self):
		if self.isDiscovering():
			self._scanner_thread.stop()
			self._scanner_thread.join()
			self.notifyDiscoveryChange(False)
			return True
		return False

	#
	# Check the discovery process.
	#
	# @return True if the manager is looking for new nodes, False otherwise.
	#
	def isDiscovering(self):
		return self._is_scanning

	#
	# Stop the discovery process and remove all the already discovered nodes.
	# Node already bounded with the device will be kept in the list.
	#
	def resetDiscovery(self):
		if self.isDiscovering():
			self.stopDiscovery()
		self.removeNodes()

	#
	# Notify each ManagerListener that the discovery process has changed status.
	#
	# @param status True the discovery start, False the discovery stop
	#
	def notifyDiscoveryChange(self, status):
		self._is_scanning = status
		for listener in self._listeners:
			# Calling user-defined callback.
			self._thread_pool.submit(listener.onDiscoveryChange(self, status))

	#
	# Notify each ManagerListener that a new node has been discovered.
	#
	# @param node Node discovered.
	#
	def notifyNewNodeDiscovered(self, node):
		for listener in self._listeners:
			# Calling user-defined callback.
			self._thread_pool.submit(listener.onNodeDiscovered(self, node))

	#
	# Insert a node into the Manager, and notify all the listeners about it.
	#
	# @param  new_node Node to add.
	# @return True if the node is added, False if a node with the same tag is
	#		  already present.
	#
	def addNode(self, new_node):
		with lock_for_object(self._discovered_nodes):
			new_tag = new_node.getTag()
			for node in self._discovered_nodes:
				if new_tag == node.getTag():
					return False
			self._discovered_nodes.append(new_node)
		self.notifyNewNodeDiscovered(new_node)
		return True

	#
	# Get the list of the discovered nodes.
	#
	# @return the list of all discovered nodes until the time of invocation.
	#
	def getNodes(self):
		with lock_for_object(self._discovered_nodes):
			return self._discovered_nodes

	#
	# Return the node with a specific tag.
	#
	# @param  tag Unique string that identifies a node.
	# @return The node with the specific tag, null if not present.
	#
	def getNodeWithTag(self, tag):
		with lock_for_object(self._discovered_nodes):
			for node in self._discovered_nodes:
				if node.getTag() == tag:
					return node
		return None

	#
	# Return the node with a specific name.
	# <p>Note: As the name is not unique, it will return the fist node matching.</p>
	# <p>Note: The match is case sensitive.</p>
	#
	# @param  name Name of the device.
	# @return The device with the specific name, null if not present.
	#
	def getNodeWithName(self, name):
		with lock_for_object(self._discovered_nodes):
			for node in self._discovered_nodes:
				if node.getName() == name:
					return node
		return None

	#
	# Remove all nodes not bounded with the device.
	#
	def removeNodes(self):
		with lock_for_object(self._discovered_nodes):
			for node in self._discovered_nodes:
				if not node.isConnected():
					self._discovered_nodes.remove(node)

	#
	# Register a new device identifier with the corresponding mask-to-features
	# dictionary, or add features to an already registered device.
	#
	# @param device_id Device identifier.
	# @param features  Mask-to-features dictionary to be added to the features
	#				   decoder dictionary, referenced by the device identifier.
	#				   The feature masks of the dictionary must have only one
	#				   bit set to "1".
	# @throws InvalidFeatureBitMaskException is thrown when a feature is in a
	#		  non-power-of-two position.
	#
	@classmethod
	def addFeaturesToNode(self, device_id, mask_to_features_dic):
		if device_id in self.features_decoder_dic:
			decoder = self.features_decoder_dic.get(device_id)
		else:
			decoder = {}
			self.features_decoder_dic[device_id] = decoder

		decoder_to_check = mask_to_features_dic.copy()

		mask = 1
		for i in range(0, 32):
			feature_class = decoder_to_check.get(mask)
			if feature_class != None:
				decoder[mask] = feature_class
				decoder_to_check.pop(mask)
			mask = mask << 1

		if bool(decoder_to_check):
			raise InvalidFeatureBitMaskException('Not all keys of the mask-to-features dictionary have a single bit set to "1".')

	#
	# Get a copy of the features map available for the given device identifier.
	#
	# @param device_id Device identifier.
	# @return A copy of the features map available for the given device
	#		  identifier if found, None otherwise.
	#
	@classmethod
	def getNodeFeatures(self, device_id):
		if device_id in self.features_decoder_dic:
			return self.features_decoder_dic[device_id].copy()
		return BLENodeDefines.FeatureCharacteristic.DEFAULT_MASK_TO_FEATURE_DIC.copy()

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


# INTERFACES

#
# Interface used by the Manager class to notify that a new Node has been
# discovered or that the scanning starts/stops.
#
class ManagerListener(object):
	__metaclass__ = ABCMeta

	#
	# This method is called when a discovery process starts or stops.
	#
	# @param manager Manager that start/stop the process.
	# @param enabled True if a new discovery starts, False otherwise.
	#
	@abstractmethod
	def onDiscoveryChange(self, manager, enabled):
		raise NotImplementedError('You must define \"onDiscoveryChange()\" to use the \"ManagerListener\" class.')

	#
	# This method is called when the Manager discovers a new node.
	#
	# @param manager Manager that discovers the node.
	# @param node    New node discovered.
	#
	@abstractmethod
	def onNodeDiscovered(self, manager, node):
		raise NotImplementedError('You must define \"onNodeDiscovered()\" to use the \"ManagerListener\" class.')
