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

from BlueSTSDK.Feature import Feature, Sample, ExtractedData
from BlueSTSDK.Features.Field import Field, FieldType
from BlueSTSDK.Utils.NumberConversion import LittleEndian


# CLASSES

#
# Feature that contains the data coming from a magnetometer sensor.
#
# <p>
# The data have no decimal digits.
# </p>
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#  
class FeatureMagnetometer(Feature):

	FEATURE_NAME = "Magnetometer"
	FEATURE_UNIT = "mGa"
	FEATURE_DATA_NAME = ["X", "Y", "Z"]
	DATA_MAX = +2000
	DATA_MIN = -2000
	MAG_X_INDEX = 0
	MAG_Y_INDEX = 1
	MAG_Z_INDEX = 2
	FEATURE_X_FIELD = Field(FEATURE_DATA_NAME[MAG_X_INDEX], FEATURE_UNIT, FieldType.Int16, DATA_MAX, DATA_MIN)
	FEATURE_Y_FIELD = Field(FEATURE_DATA_NAME[MAG_Y_INDEX], FEATURE_UNIT, FieldType.Int16, DATA_MAX, DATA_MIN)
	FEATURE_Z_FIELD = Field(FEATURE_DATA_NAME[MAG_Z_INDEX], FEATURE_UNIT, FieldType.Int16, DATA_MAX, DATA_MIN)
	DATA_LENGTH_BYTES = 6

	#
	# Constructor.
	#
	# @param node Node that will send data to this feature.
	#
	def __init__(self, node):
		super(FeatureMagnetometer, self).__init__(self.FEATURE_NAME, node, [self.FEATURE_X_FIELD, self.FEATURE_Y_FIELD, self.FEATURE_Z_FIELD])

	#
	# Extract the data from the node's raw data.
	# In this case it reads three 16-bit signed integer values.
	#
	# @param timestamp Data's timestamp.
	# @param data      Array where to read data from.
	# @param offset    Offset where to start reading data.
	# @return The number of bytes read and the extracted data.
	# @throws Exception if the data array has not enough data to read.
	#
	def extractData(self, timestamp, data, offset):
		if len(data) - offset < self.DATA_LENGTH_BYTES:
			raise Exception('There are no %s bytes available to read.' % (self.DATA_LENGTH_BYTES))
		sample = Sample(
					[LittleEndian.bytesToInt16(data, offset),
					 LittleEndian.bytesToInt16(data, offset + 2),
					 LittleEndian.bytesToInt16(data, offset + 4)],
					super(FeatureMagnetometer, self).getFieldsDescription(),
					timestamp
				)
		return ExtractedData(sample, self.DATA_LENGTH_BYTES)

	#
	# Get the magnetometer value on the X axis from a sample.
	#
	# @param sample Sample data.
	# @return The magnetometer value on the X axis if the data array is valid,
	#         <nan> otherwise.
	#	  
	@classmethod
	def getMagX(self, sample):
		if sample != None:
			if len(sample._data) > 0:
				if sample._data[self.MAG_X_INDEX] != None:
					return float(sample._data[self.MAG_X_INDEX])
		return float('nan')

	#
	# Get the magnetometer value on the Y axis from a sample.
	#
	# @param sample Sample data.
	# @return The magnetometer value on the Y axis if the data array is valid,
	#         <nan> otherwise.
	#	  
	@classmethod
	def getMagY(self, sample):
		if sample != None:
			if len(sample._data) > 0:
				if sample._data[self.MAG_Y_INDEX] != None:
					return float(sample._data[self.MAG_Y_INDEX])
		return float('nan')

	#
	# Get the magnetometer value on the Z axis from a sample.
	#
	# @param sample Sample data.
	# @return The magnetometer value on the Z axis if the data array is valid,
	#         <nan> otherwise.
	#	  
	@classmethod
	def getMagZ(self, sample):
		if sample != None:
			if len(sample._data) > 0:
				if sample._data[self.MAG_Z_INDEX] != None:
					return float(sample._data[self.MAG_Z_INDEX])
		return float('nan')
