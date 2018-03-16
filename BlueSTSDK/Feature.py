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
#import Queue

from BlueSTSDK.PythonUtils import lock
import BlueSTSDK.Features.Field


# CLASSES

# 
# Contains description and data exported by a node.
# <p>
# Adding a new sensor in a node implies extending this class and implementing
# the "extractData()" method to extract the information from the raw data coming
# from the node. This class manages notifications and listeners' subscriptions.
# </p>
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
# 
class Feature(object):

	# Number of threads to be used to notify the listeners.
	NUMBER_OF_THREADS = 5

	# 
	# Build a new disabled feature, that doesn't need to be initialized in the
	# node side.
	#
	# @param name        Name of the feature.
	# @param node        Node that will update the feature.
	# @param description Description of the data of the feature.
	#
	def __init__(self, name, node, description):

		# Feature name.
		self._name = name

		# Node that will update the feature.
		self._parent = node

		# Array of feature's fields.
		# Fields are described by name, unit, type, and minimum/maximum values.
		self._description = description

		# Tells whether the feature is enabled or not.
		self._is_enabled = False

		# Tells whether the feature's notifications are enabled or not
		self._notify = False

		# Pool of thread used to notify the listeners.
		self._thread_pool = ThreadPoolExecutor(Feature.NUMBER_OF_THREADS)

		# List of listeners to the feature changes.
		# It is a thread safe list, so a listener can subscribe itself through a
		# callback.
		self._listeners = []

		# List of listeners to log the received data.
		# It is a thread safe list, so a listener can subscribe itself through a
		# callback.
		self._loggers = []

		# Local time of the last update.
		self._last_update = None

		# Last data received from the node.
		self._last_sample = None

		# Reference to the characteristic that offers the feature.
		# Note: By design, it is the characteristic that offers more features beyond
		#       the current one, among those offering the current one.
		self._characteristic = None

	# 
	# Check if the sample has valid data in the index position.
	# @param sample Sample to test.
	# @param index  Index to test.
	# @return True if the sample is not null and has a non null value into the
	#   index position, False otherwise.
	#
	@classmethod
	def hasValidIndex(self, sample, index):
		return sample != None and len(sample._data) > index and sample._data[index] != None

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
	# Add a logger.
	#
	# @param logger Logger to be added.
	#
	def addLogger(self, logger):
		if logger != None:
			with lock(self):
				if not logger in self._loggers:
					self._loggers.append(logger)

	#
	# Remove a logger.
	#
	# @param logger Logger to be removed.
	#
	def removeLogger(self, logger):
		if logger != None:
			with lock(self):
				if logger in self._loggers:
					self._loggers.remove(logger)

	# 
	# Get the time of the last update.
	#
	# @return Time of the last update.
	#
	def getLastUpdate(self):
		return self._last_update

	# 
	# Get the feature name.
	#
	# @return The feature name.
	#
	def getName(self):
		return self._name

	#
	# Get the node that will update the feature.
	#
	# @return The node that will update the feature.
	#
	def getParentNode(self):
		return self._parent

	#
	# Get the characteristic that offers the feature.
	#
	# Note: By design, it is the characteristic that offers more features beyond
	#       the current one, among those offering the current one.
	#
	# @return The characteristic that offers the feature.
	#
	def getCharacteristic(self):
		return self._characteristic

	# 
	# Get the description of the data fields of the feature.
	#
	# @return The description of the data fields of the feature.
	#
	def getFieldsDescription(self):
		return self._description

	# 
	# Return the last timestamp and the data received from the device.
	#
	# @return Last sample received, None if missing.
	#
	def getSample(self):
		if self._last_sample != None:
			return Sample(self._last_sample)
		return None

	#
	# Change the enable status of the feature.
	#
	# @param flag New enable status: True to enable, False otherwise.
	#
	def setEnable(self, flag):
		self._is_enabled = flag

	# 
	# Checking whether the node exports the data of the feature.
	# <p> A node can export a feature in the advertising data without having the
	#	  equivalent characteristic.</p>
	#
	# @return True if the node exports the data of the feature, False otherwise.
	#
	def isEnabled(self):
		return self._is_enabled

	#
	# Change the notification status of the feature.
	#
	# @param flag New notification status: True to turn on notifications, False
	#             otherwise.
	#
	def setNotify(self, flag):
		self._notify = flag

	# 
	# Checking whether the notifications for the feature are enabled.
	#
	# @return True if the feature is notifying, False otherwise.
	#
	def isNotifying(self):
		return self._notify

	#
	# Notify each FeatureListener that the feature has been updated.
	#
	# <p> Each call runs in a different thread.</p>
	# <p>
	# Overwriting the method "BlueSTSDK.Feature#_update()" implies calling
	# this method to notify the user about the new sample.
	# </p>
	# @param sample New data to be notified to the listener.
	#
	def notifyUpdate(self, sample):
		for listener in self._listeners:
			# Calling user-defined callback.
			self._thread_pool.submit(listener.onUpdate(self, sample))

	#
	# Notify each FeatureLogger that the feature has been updated.
	#
	# <p> Each call runs in a different thread.</p>
	# <p>
	# Overwriting the method "BlueSTSDK.Feature#_update()" implies calling
	# this method after updating the data if you want the feature to be
	# logged.
	# </p>
	#
	# @param raw_data Raw data used to extract the feature field. It can be
	#                 "None".
	# @param sample   Sample to be logged.
	#
	def logFeatureUpdate(self, raw_data, sample):
		for listener in self._loggers:
			self._thread_pool.submit(logger.logFeatureUpdate(self, raw_data, sample))

	#
	# Update feature's internal data through an atomic operation, and notify the
	# listeners about the update.
	#
	# <p>
	# When overriding this method, please remember to update the timestamp and
	# the last-update value, and to acquire the write-lock. When finished, you
	# should call the "notifyUpdate()" and "logFeatureUpdate()" methods to
	# notify the user about the update.
	# </p>
	# <p>
	# This method should be called by the node itself, not by the application.
	# </p>
	#
	# @param timestamp Package timestamp.
	# @param data	   Array of data.
	# @param offset    Offset position to start reading data.
	# @return The number of bytes read.
	#
	def _update(self, timestamp, data, offset):
		# Update the feature's internal data
		sample = None
		with lock(self):
			extracted_data = self.extractData(timestamp, data, offset)
			sample = self._last_sample = extracted_data.getSample()
			read_bytes = extracted_data.getReadBytes()
			self._last_update = datetime.now()

		# Notify all the listeners about the new data arrived.
		self.notifyUpdate(sample)

		# Log only the read bytes.
		self.logFeatureUpdate(data[offset:offset + read_bytes], sample)

		return read_bytes

	# 
	# This method is called by the node whenever it receives new data from the
	# feature.
	#
	# @param timestamp   Package timestamp.
	# @param data		 Array of data where to extract the data.
	# @param offset Data offset from where to read.
	# @return The number of bytes read.
	#
	def update(self, timestamp, data, offset):
		return self._update(timestamp, data, offset)

	# 
	# Parse the command response data.
	#
	# <p>
	# It is implemented as an empty method; it is an optional abstract method.
	# </p>
	#
	# @param timestamp Device timestamp of the time the response was sent.
	# @param command   Identifier of the request done by the feature.
	# @param data	   Data attached to the response.
	#
	#def parseCommandResponse(self, timestamp, command, data):
	#	pass

	# 
	# Notify the feature that the node has received a response to a command
	# sent from the feature.
	#
	# @param timestamp Device timestamp of the time the response was sent.
	# @param command   Identifier of the request done by the feature.
	# @param data	   Data attached to the response.
	#
	#def commandResponseReceived(self, timestamp, command, data):
	#	self.parseCommandResponse(timestamp, command, data)

	#
	# In case the corrisponding characteristic has the write permission you can
	# send some data to the feature.
	#
	# @param  data Raw data to write.
	# @return True if the command is executed correctly, False otherwise.
	#
	def writeData(self, data):
		return self._parent.writeFeature(self, data)

	# 
	# Extract the feature data from a raw bytes stream.
	#
	# <p>
	# You have to parse the data inside the "data" field and skip the first
	# "offset" byte.
	# </p>
	# <p>
	# This method has to extract the data, create a "BlueSTSDK.Feature.Sample"
	# object, and return an "ExtractedData" object containing it.
	# </p>
	# <p>
	# The method that calls this one has to manage the lock acquisition/release
	# and to notify the user about the new sample.
	# </p>
	#
	# @param timestamp Data timestamp.
	# @param data      Array where to read the data from.
	# @param offset    Offset where to start to reading the data.
	# @return The number of bytes read and the extracted data.
	# @throws Exception if the data array has not enough data to read.
	#
	@abstractmethod
	def extractData(self, timestamp, data, offset):
		raise NotImplementedError('You must define "extractData()" to use the "Feature" class.')

	#
	# Print the last feature's data.
	#
	# @return A string containing the last feature's data.
	#
	def __str__(self):
		with lock(self):
			sample = self._last_sample

		if sample == None or len(sample._data) == 0:
			return self._name + ': Unknown'

		if len(sample._data) == 1:
			result = '%s(%d): %s %s' % (self._name, sample._timestamp, str(sample._data[0]), self._description[0]._unit)
			return result

		result = '%s(%d): ( ' % (self._name, sample._timestamp)
		i = 0
		while i < len(sample._data):
			result += '%s: %s %s%s' % (self._description[i]._name, str(sample._data[i]), self._description[i]._unit, '    ' if i < len(sample._data) - 1 else ' )')
			i += 1
		return result

#
# Interface used to notify that the feature updates its data.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class FeatureListener(object):
	__metaclass__ = ABCMeta

	#
	# To be called whenever the feature updates its data.
	#
	# @param feature Feature that has updated.
	# @param sample  Data extracted from the feature.
	#
	@abstractmethod
	def onUpdate(self, feature, sample):
		raise NotImplementedError('You must define "onUpdate()" to use the "FeatureListener" class.')

#
# Interface used to dump the feature's data, both in raw format (as received
# from the node) and after parsing it.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class FeatureLogger(object):
	__metaclass__ = ABCMeta

	#
	# To be called to log the update of the feature.
	#
	# @param feature  Feature that has updated.
	# @param raw_data Raw data used to update the feature.
	# @param sample   Data extracted from the feature.
	#
	@abstractmethod
	def logFeatureUpdate(self, feature, raw_data, sample):
		raise NotImplementedError('You must define "logFeatureUpdate()" to use the "FeatureLogger" class.')


#
# Class used to return the data and the number of bytes read.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class ExtractedData(object):

	# 
	# Constructor.
	#
	# @param sample     Data extracted.
	# @param read_bytes Number of bytes read.
	#	
	def __init__(self, sample, read_bytes):
		# Data extracted from the byte stream.
		self._sample = sample
		
		# Number of bytes read.
		self._read_bytes = read_bytes

	# 
	# Get the number of bytes read.
	#
	# @return The number of bytes read.
	#	
	def getReadBytes(self):
		return self._read_bytes

	# 
	# Get the data extracted from the byte stream.
	# @return The data extracted from the byte stream.
	#	
	def getSample(self):
		return self._sample


#
# Class that contains the last data from the node.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class Sample(object):

	#
	# Constructor.
	#
	# @param data        Feature's data.
	# @param description Description of each data's field.
	# @param timestamp   Data's timestamp.
	#
	def __init__(self, data, description, timestamp = 0):
		self._data = data
		self._description = description
		self._timestamp = timestamp
		self._notification_time = datetime.now()

	#
	# Make a copy of a sample.
	#
	# @param sample An existing sample.
	#
	@classmethod
	def fromSample(self, copy_me):
		sample._data = copy_me._data.copy()
		sample._description = copy_me._description
		sample._timestamp = copy_me.timestamp
		sample._notification_time = copy_me.notification_time
		return sample

	#
	# Check the equality of two samples.
	#
	# @param sample A sample object.
	# @return True if the objects are equal (timestamp and data),
	#		  False otherwise.
	#
	def equals(self, sample):
		if sample == None:
			return False
		if isinstance(sample, self.Sample):
			return sample._timestamp == self._timestamp and sorted(sample._data) == sorted(self._data)
		return False

	#
	# Get a string representing the sample.
	#
	# @return A string representing the sample.
	#
	def __str__(self):
		return "Timestamp: " + str(self._timestamp) + " Data: " + str(self._data)
