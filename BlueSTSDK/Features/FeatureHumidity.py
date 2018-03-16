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
# Feature that contains the data coming from a humidity sensor.
#
# <p>
# The data has one decimal digit.
# </p>
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#  
class FeatureHumidity(Feature):

	FEATURE_NAME = "Humidity"
	FEATURE_UNIT = "%"
	FEATURE_DATA_NAME = "Humidity"
	DATA_MAX = 100
	DATA_MIN = 0
	FEATURE_FIELDS = Field(FEATURE_DATA_NAME, FEATURE_UNIT, FieldType.Float, DATA_MAX, DATA_MIN)
	SCALE_FACTOR = 10.0
	DATA_LENGTH_BYTES = 2

	#
	# Constructor.
	#
	# @param node Node that will send data to this feature.
	#
	def __init__(self, node):
		super(FeatureHumidity, self).__init__(self.FEATURE_NAME, node, [self.FEATURE_FIELDS])

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
		if len(data) - offset < self.DATA_LENGTH_BYTES:
			raise Exception('There are no %d bytes available to read.' % (self.DATA_LENGTH_BYTES))
		sample = Sample([LittleEndian.bytesToInt16(data, offset) / self.SCALE_FACTOR], super(FeatureHumidity, self).getFieldsDescription(), timestamp)
		return ExtractedData(sample, self.DATA_LENGTH_BYTES)

	#
	# Get the humidity value from a sample.
	#
	# @param sample Sample data.
	# @return The humidity value if the data array is valid, <nan> otherwise.
	#	  
	@classmethod
	def getHumidity(self, sample):
		if sample != None:
			if len(sample._data) > 0:
				if sample._data[0] != None:
					return float(sample._data[0])
		return float('nan')
