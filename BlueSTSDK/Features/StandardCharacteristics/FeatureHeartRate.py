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

from BlueSTSDK.Feature import Sample, ExtractedData
from BlueSTSDK.Features.DeviceTimestampFeature import DeviceTimestampFeature
from BlueSTSDK.Features.Field import Field, FieldType
from BlueSTSDK.Utils.NumberConversion import LittleEndian


# CLASSES

# 
# Feature that manages the Heart Rate'sample data as defined by the Bluetooth
# specification. 
#
# @see <a href="https://developer.bluetooth.org/gatt/characteristics/Pages/CharacteristicViewer
# .aspx?u=org.bluetooth.characteristic.heart_rate_measurement.xml">Heart Rate Measurement Specs</a>
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#  
class FeatureHeartRate(DeviceTimestampFeature):

	FEATURE_NAME = "Heart Rate"
	HEART_RATE_INDEX = 0
	HEART_RATE_FIELD = Field("Heart Rate Measurement", "bpm", FieldType.UInt16, 0, 1 << 16)
	ENERGY_EXPENDED_INDEX = 1
	ENERGY_EXPENDED_FIELD = Field("Energy Expended", "kJ", FieldType.UInt16, 0, 1 << 16)
	RR_INTERVAL_INDEX = 2
	RR_INTERVAL_FIELD = Field("RR-Interval", "sample", FieldType.Float, 0, sys.float_info.max)
	DATA_LENGTH_BYTES = 2

	#
	# Build a new disabled feature, that doesn't need to be initialized at
	# node'sample side.
	#
	# @param node Node that will update this feature.
	#
	def __init__(self, node):
		super(FeatureHeartRate, self).__init__(
			self.FEATURE_NAME,
			node,
			[self.HEART_RATE_FIELD, self.ENERGY_EXPENDED_FIELD, self.RR_INTERVAL_FIELD]
		)

	#
	# Extract the Heart Rate from the sample.
	#
	# @param sample The sample.
	# @return The Heart Rate if available, a negative number otherwise.
	#	  
	@classmethod
	def getHeartRate(self, sample):
		if sample != None:
			if len(sample._data) > self.HEART_RATE_INDEX:
				hr = sample._data[self.HEART_RATE_INDEX]
				if hr != None:
					return int(hr)
		return -1

	#
	# Extract the energy expended field from the sample.
	#
	# @param sample The sample.
	# @return The energy expended if available, a negative number otherwise.
	#
	@classmethod
	def getEnergyExpended(self, sample):
		if sample != None:
			if len(sample._data) > self.ENERGY_EXPENDED_INDEX:
				ee = sample._data[self.ENERGY_EXPENDED_INDEX]
				if ee != None:
					return int(ee)
		return -1

	#
	# Extract the RR interval field from the sample.
	#
	# @param sample The sample.
	# @return The RR interval if available, <nan> otherwise.
	#
	@classmethod
	def getRRInterval(self, sample):
		if sample != None:
			if len(sample._data) > self.RR_INTERVAL_INDEX:
				rri = sample._data[self.RR_INTERVAL_INDEX]
				if rri != None:
					return float(rri)
		return float('nan')

	#
	# Extract the data from the node's raw data.
	# In this case it reads a 16-bit signed integer value.
	#
	# @param timestamp Data's timestamp.
	# @param data      Array where to read data from.
	# @param offset    Offset where to start reading data.
	# @return The number of bytes read and the extracted data.
	# @throws Exception if the data array has not enough data to read.
	#
	def extractData(self, timestamp, data, offset):
		if (len(data) - offset < self.DATA_LENGTH_BYTES):
			raise Exception('There are no %d bytes available to read.' % (self.DATA_LENGTH_BYTES))

		offset = offset
		flags = data[offset]
		offset += 1

		if self.has8BitHeartRate(flags):
			hr = data[offset]
			offset += 1
		else:
			hr = LittleEndian.bytesToUInt16(data, offset)
			offset += 2

		if self.hasEnergyExpended(flags):
			ee = LittleEndian.bytesToUInt16(data, offset)
			offset += 2
		else:
			ee = -1

		if self.hasRRInterval(flags):
			rri = LittleEndian.bytesToUInt16(data, offset) / 1024.0
			offset += 2
		else:
			rri = float('nan')

		return ExtractedData(
			Sample(
				timestamp,
				[hr, ee, rri],
				getFieldsDescription()
			),
			offset - offset
		)

	#
	# Check if there is Heart Rate.
	#
	# @ param flags Flags.
	# @return True if there is Heart Rate, False otherwise.
	#
	@classmethod
	def has8BitHeartRate(self, flags):
		return (flags & 0x01) == 0

	#
	# Check if there is Energy Expended.
	#
	# @ param flags Flags.
	# @return True if there is Energy Expended, False otherwise.
	#
	@classmethod
	def hasEnergyExpended(self, flags):
		return (flags & 0x08) != 0

	#
	# Check if there is RR interval.
	#
	# @ param flags Flags.
	# @return True if there is RR Interval, False otherwise.
	#
	@classmethod
	def hasRRInterval(self, flags):
		return (flags & 0x10) != 0
