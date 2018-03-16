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

from BlueSTSDK.Feature import Feature


# CLASSES

# 
# Class that a feature has to extend if it doesn't have the timestamp field.
# The system time is used as timestamp.
#
# @see <a href="https://developer.bluetooth.org/gatt/characteristics/Pages/CharacteristicViewer
# .aspx?u=org.bluetooth.characteristic.heart_rate_measurement.xml">Heart Rate Measurement Specs</a>
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
# 
class DeviceTimestampFeature(Feature):

	#
	# Constructor.
	#
	# @param name        Name of the feature.
	# @param node        Node that will update the feature.
	# @param description Description of the data of the feature.
	#
	def __init__(self, name, node, description):
		super(DeviceTimestampFeature, self).__init__(name, node, description)

	#
	# Change the timestamp with the system timestamp and reset the data offset.
	#
	# @param timestamp Package timestamp.
	# @param data	   Array of data.
	# @param offset    Offset position to start reading data.
	# @return The number of bytes read.
	#
	def _update(self, timestamp, data, offset):
		return super(DeviceTimestampFeature, self)._update(datetime.now(), data, offset - 2)
