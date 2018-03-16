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

import uuid
import re

from BlueSTSDK.Features import *


# CLASSES


#
# This class helps to get the list of services and characteristics available in
# the BlueST devices.
#
# <p>
# It defines the UUID and the name of the services and the characteristics
# available in the BlueST devices.
# </p>
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class BLENodeDefines(object):

	# Sensor service UUIDs handled by this SDK must end with this value.
	BLUESTSDK_SENSOR_SERVICE_UUID = '-11e1-9ab4-0002a5d5c51b'

	# Sensor characteristic UUIDs handled by this SDK must end with this value.
	BLUESTSDK_SENSOR_CHARACTERISTIC_UUID = '-11e1-ac36-0002a5d5c51b'

	# Feature UUID.
	FEATURE_UUID = '-0001'

	# Debug UUID.
	DEBUG_UUID = '-000E'

	# Config UUID.
	CONFIG_UUID = '-000F'


#
# This class helps to get list of services available in the BlueST devices.
#
# <p>
# It defines the UUID and the name of the services available in the BlueST
# devices.
# </p>
#
# <p>
# A valid service UUID has the form '00000000-XXXX-11e1-9ab4-0002a5d5c51b',
# where 'XXXX' is the service identifier.
# </p>
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class Services(object):

	# Format of the BlueSTSDK's sensor service UUID.
	BLUESTSDK_SENSOR_SERVICE_UUID_FORMAT = '00000000-[0-9a-fA-F]{4}' + BLENodeDefines.BLUESTSDK_SENSOR_SERVICE_UUID

	#
	# Check if the service is handled by this SDK, i.e. if the uuid has the
	# '00000000-YYYY-11e1-9ab4-0002a5d5c51b' format.
	#
	# @param uuid UUID of the service under test.
	# @return True if the UUID ends with 'BLUESTSDK_SENSOR_SERVICE_UUID', False
	#		 otherwise.
	#
	def isKnownService(self, uuid):
		return re.match(BLUESTSDK_SENSOR_SERVICE_UUID_FORMAT, uuid)


#
# Class to access the board' stdout/stderr streams.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class Debug(object):

	# Debug sensor service UUID.
	DEBUG_BLUESTSDK_SENSOR_SERVICE_UUID = uuid.UUID('00000000' + BLENodeDefines.DEBUG_UUID + BLENodeDefines.BLUESTSDK_SENSOR_SERVICE_UUID)

	# Debug sensor characteristic UUID where you can write and read
	# output commands.
	DEBUG_TERMINAL_BLUESTSDK_SENSOR_SERVICE_UUID = uuid.UUID('00000001' + BLENodeDefines.DEBUG_UUID + BLENodeDefines.BLUESTSDK_SENSOR_CHARACTERISTIC_UUID)

	# Debug sensor characteristic UUID where the node writes error
	# messages.
	DEBUG_STDERR_BLUESTSDK_SENSOR_SERVICE_UUID = uuid.UUID('00000002' + BLENodeDefines.DEBUG_UUID + BLENodeDefines.BLUESTSDK_SENSOR_CHARACTERISTIC_UUID)

	#
	# Check if the provided UUID is a valid debug characteristic UUID.
	#
	# @param uuid Characteristic UUID.
	# @return True if the provided UUID is a valid debug characteristic
	#		 UUID.
	#
	def isDebugCharacteristics(self, uuid):
		return uuid == DEBUG_STDERR_BLUESTSDK_SENSOR_SERVICE_UUID or uuid == DEBUG_TERMINAL_BLUESTSDK_SENSOR_SERVICE_UUID


#
# Service that allows to configure the board parameters or the features.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class Config(object):

	# Control sensor service UUID.
	CONFIG_BLUESTSDK_SENSOR_SERVICE_UUID = uuid.UUID('00000000' + BLENodeDefines.CONFIG_UUID + BLENodeDefines.BLUESTSDK_SENSOR_SERVICE_UUID)

	# Control sensor characteristic UUID through which you can manage
	# registers, i.e. to read or write registers.
	REGISTERS_ACCESS_UUID = uuid.UUID('00000001' + BLENodeDefines.CONFIG_UUID + BLENodeDefines.BLUESTSDK_SENSOR_SERVICE_UUID)

	# Control sensor characteristic UUID through which you can send
	# commands to a feature.
	CONFIG_COMMAND_BLUESTSDK_SENSOR_SERVICE_UUID = uuid.UUID('00000002' + BLENodeDefines.CONFIG_UUID + BLENodeDefines.BLUESTSDK_SENSOR_SERVICE_UUID)


#
# This class defines the associations characteristic-feature.
#
# <p>
# A feature's characteristic has the form
# 'XXXXXXXX-0001-11e1-ac36-0002a5d5c51b'.
# </p>
# <p>
# 'XXXXXXXX' is a number in which only one bit has value '1'.
# In case multiple bits have value '1' it means that this characteristic
# will send all the corresponding features' values at the same time.
# </p>
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class FeatureCharacteristic(object):

	# Sensor feature UUIDs handled by this SDK must end with this value.
	BLUESTSDK_SENSOR_FEATURES_UUID = BLENodeDefines.FEATURE_UUID + BLENodeDefines.BLUESTSDK_SENSOR_CHARACTERISTIC_UUID

	# Map from feature's masks to feature's classes.
	DEFAULT_MASK_TO_FEATURE_DIC = {
		#0x80000000: FeatureAnalog.FeatureAnalog,
		#0x40000000: FeatureAudioADPCMSync.FeatureAudioADPCMSync,
		#0x20000000: FeatureSwitch.FeatureSwitch,
		#0x10000000: FeatureDirectionOfArrival.FeatureDirectionOfArrival,

		#0x08000000: FeatureAudioADPCM.FeatureAudioADPCM,
		#0x04000000: FeatureMicLevel.FeatureMicLevel,
		#0x02000000: FeatureProximity.FeatureProximity,
		#0x01000000: FeatureLuminosity.FeatureLuminosity,

		0x00800000: FeatureAcceleration.FeatureAcceleration, #00e00000
		0x00400000: FeatureGyroscope.FeatureGyroscope,       #00e00000
		0x00200000: FeatureMagnetometer.FeatureMagnetometer, #00e00000
		0x00100000: FeaturePressure.FeaturePressure,         #001d0000

		0x00080000: FeatureHumidity.FeatureHumidity,         #001d0000
		0x00040000: FeatureTemperature.FeatureTemperature,   #001d0000
		#0x00020000: FeatureBattery.FeatureBattery,
		0x00010000: FeatureTemperature.FeatureTemperature,   #001d0000

		#0x00008000: FeatureCOSensor.FeatureCOSensor,
		#0x00004000: FeatureDCMotor.FeatureDCMotor,
		#0x00002000: FeatureStepperMotor.FeatureStepperMotor,
		#0x00001000: FeatureSDLogging.FeatureSDLogging,

		#0x00000800: FeatureBeamforming.FeatureBeamforming,
		#0x00000400: FeatureAccelerationEvent.FeatureAccelerationEvent,
		#0x00000200: FeatureFreeFall.FeatureFreeFall,
		#0x00000100: FeatureMemsSensorFusionCompact.FeatureMemsSensorFusionCompact,

		#0x00000080: FeatureMemsSensorFusion.FeatureMemsSensorFusion,
		#0x00000020: FeatureMotionIntensity.FeatureMotionIntensity,
		#0x00000040: FeatureCompass.FeatureCompass,
		#0x00000010: FeatureActivity.FeatureActivity,

		#0x00000008: FeatureCarryPosition.FeatureCarryPosition,
		#0x00000004: FeatureProximityGesture.FeatureProximityGesture,
		#0x00000002: FeatureMemsGesture.FeatureMemsGesture,
		#0x00000001: FeaturePedometer.FeaturePedometer
	}

	#
	# Extract the fist 32 bits from the characteristic's UUID.
	#
	# @param uuid Characteristic's UUID.
	# @return The first 32 bit of the characteristic's UUID.
	#
	@classmethod
	def extractFeatureMask(self, uuid):
		return int(str(uuid).split('-')[0], 16)

	#
	# Check if the UUID is a valid feature UUID.
	#
	# @param uuid Characteristic's UUID.
	# @return True if the UUID is a valid feature UUID.
	#
	@classmethod
	def isFeatureCharacteristic(self, uuid):
		return str(uuid).endswith(self.BLUESTSDK_SENSOR_FEATURES_UUID)
