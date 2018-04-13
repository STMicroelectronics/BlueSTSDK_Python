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


"""ble_node_definitions

The ble_node_definitions module contains definitions related to the Bluetooth
and recognized by the BlueSTSDK.
"""


# IMPORT

import uuid
import re

from blue_st_sdk.features import *


# DEFINITIONS

TIMESTAMP_OFFSET_BYTES = 2


# CLASSES


class BLENodeDefinitions(object):
    """This class helps to get the list of services and characteristics
    available in the BlueST devices.

    It defines the UUID and the name of the services and the characteristics
    available in the BlueST devices.
    """

    BLUESTSDK_SERVICE_UUID = '-11e1-9ab4-0002a5d5c51b'
    """Service UUIDs handled by this SDK must end with this value."""

    BLUESTSDK_CHARACTERISTIC_UUID = '-11e1-ac36-0002a5d5c51b'
    """Characteristic UUIDs handled by this SDK must end with this value."""

    FEATURE_UUID = '-0001'
    """Feature UUID."""

    DEBUG_UUID = '-000E'
    """Debug UUID."""

    CONFIG_UUID = '-000F'
    """Config UUID."""


class Services(object):
    """This class helps to get list of services available in the BlueST devices.

    It defines the UUID and the name of the services available in the BlueST
    devices.

    A valid service UUID has the form '00000000-XXXX-11e1-9ab4-0002a5d5c51b',
    where 'XXXX' is the service identifier.
    """

    BLUESTSDK_SERVICE_UUID_FORMAT = \
        '00000000-[0-9a-fA-F]{4}' + BLENodeDefinitions.BLUESTSDK_SERVICE_UUID
    """Format of the blue_st_sdk's service UUID."""

    def isKnownService(self, uuid):
        """Check if the service is handled by this SDK, i.e. if the uuid has the
        '00000000-YYYY-11e1-9ab4-0002a5d5c51b' format.

        Args:
            uuid (str): UUID of the service under test.

        Returns:
            True if the UUID ends with
            :attr:`blue_st_sdk.utils.ble_node_definitions.BLENodeDefinitions.BLUESTSDK_SERVICE_UUID`,
            False otherwise.
        """
        return re.match(BLUESTSDK_SERVICE_UUID_FORMAT, uuid)


class Debug(object):
    """Class to access the board' stdout/stderr streams.
    """

    DEBUG_BLUESTSDK_SERVICE_UUID = \
        uuid.UUID('00000000' \
        + BLENodeDefinitions.DEBUG_UUID \
        + BLENodeDefinitions.BLUESTSDK_SERVICE_UUID)
    """Debug service UUID."""

    DEBUG_TERMINAL_BLUESTSDK_SERVICE_UUID = \
        uuid.UUID('00000001' \
        + BLENodeDefinitions.DEBUG_UUID \
        + BLENodeDefinitions.BLUESTSDK_CHARACTERISTIC_UUID)
    """Debug characteristic UUID where you can write and read output commands."""

    DEBUG_STDERR_BLUESTSDK_SERVICE_UUID = \
        uuid.UUID('00000002' \
        + BLENodeDefinitions.DEBUG_UUID \
        + BLENodeDefinitions.BLUESTSDK_CHARACTERISTIC_UUID)
    """Debug characteristic UUID where the node writes error messages."""

    def isDebugCharacteristics(self, uuid):
        """Check if the provided UUID is a valid debug characteristic UUID.

        Args:
            uuid Characteristic UUID.
        
        Returns:
            True if the provided UUID is a valid debug characteristic UUID,
            False otherwise.
        """
        return uuid == DEBUG_STDERR_BLUESTSDK_SERVICE_UUID \
            or uuid == DEBUG_TERMINAL_BLUESTSDK_SERVICE_UUID


class Config(object):
    """Service that allows to configure the board parameters or the features."""

    CONFIG_BLUESTSDK_SERVICE_UUID = \
        uuid.UUID('00000000' \
        + BLENodeDefinitions.CONFIG_UUID \
        + BLENodeDefinitions.BLUESTSDK_SERVICE_UUID)
    """Control service UUID."""

    REGISTERS_ACCESS_UUID = \
        uuid.UUID('00000001' \
        + BLENodeDefinitions.CONFIG_UUID \
        + BLENodeDefinitions.BLUESTSDK_SERVICE_UUID)
    """Control characteristic UUID through which you can manage registers, i.e.
    to read or write registers."""

    CONFIG_COMMAND_BLUESTSDK_SERVICE_UUID = \
        uuid.UUID('00000002' \
        + BLENodeDefinitions.CONFIG_UUID \
        + BLENodeDefinitions.BLUESTSDK_SERVICE_UUID)
    """Control characteristic UUID through which you can send commands to a
    feature."""


class FeatureCharacteristic(object):
    """This class defines the associations characteristic-feature.

    A feature's characteristic has the form
    'XXXXXXXX-0001-11e1-ac36-0002a5d5c51b'.

    'XXXXXXXX' is a number in which only one bit has value '1'.
    In case multiple bits have value '1' it means that this characteristic sends
    all the corresponding features' values at the same time.
    """

    BLUESTSDK_FEATURES_UUID = \
        BLENodeDefinitions.FEATURE_UUID \
        + BLENodeDefinitions.BLUESTSDK_CHARACTERISTIC_UUID
    """Feature UUIDs handled by this SDK must end with this value."""

    DEFAULT_MASK_TO_FEATURE_DIC = {
        #0x80000000: feature_analog.FeatureAnalog,
        #0x40000000: feature_audio_adpcm_sync.FeatureAudioADPCMSync,
        0x20000000: feature_switch.FeatureSwitch,
        #0x10000000: feature_direction_of_arrival.FeatureDirectionOfArrival,

        #0x08000000: feature_audio_adpcm.FeatureAudioADPCM,
        #0x04000000: feature_microphone_level.FeatureMicrophoneLevel,
        0x02000000: feature_proximity.FeatureProximity,
        #0x01000000: feature_luminosity.FeatureLuminosity,

        0x00800000: feature_accelerometer.FeatureAccelerometer, #00e00000
        0x00400000: feature_gyroscope.FeatureGyroscope,         #00e00000
        0x00200000: feature_magnetometer.FeatureMagnetometer,   #00e00000
        0x00100000: feature_pressure.FeaturePressure,           #001d0000

        0x00080000: feature_humidity.FeatureHumidity,           #001d0000
        0x00040000: feature_temperature.FeatureTemperature,     #001d0000
        #0x00020000: feature_battery.FeatureBattery,
        0x00010000: feature_temperature.FeatureTemperature,     #001d0000

        #0x00008000: feature_co_sensor.FeatureCOSensor,
        #0x00004000: feature_dc_motor.FeatureDCMotor,
        0x00002000: feature_stepper_motor.FeatureStepperMotor,
        #0x00001000: feature_sd_logging.FeatureSDLogging,

        #0x00000800: feature_beamforming.FeatureBeamforming,
        #0x00000400: feature_acceleration_event.FeatureAccelerometerEvent,
        #0x00000200: feature_free_fall.FeatureFreeFall,
        #0x00000100: feature_mems_sensor_fusion_compact.FeatureMemsSensorFusionCompact,

        #0x00000080: feature_mems_sensor_fusion.FeatureMemsSensorFusion,
        #0x00000020: feature_motion_intensity.FeatureMotionIntensity,
        #0x00000040: feature_compass.FeatureCompass,
        #0x00000010: feature_activity.FeatureActivity,

        #0x00000008: feature_carry_position.FeatureCarryPosition,
        0x00000004: feature_proximity_gesture.FeatureProximityGesture
        #0x00000002: feature_mems_gesture.FeatureMemsGesture,
        #0x00000001: feature_pedometer.FeaturePedometer
    }
    """Map from feature's masks to feature's classes."""

    @classmethod
    def extract_feature_mask(self, uuid):
        """"Extract the fist 32 bits from the characteristic's UUID.
        
        Args:
            uuid (str): Characteristic's UUID.
        
        Returns:
            The first 32 bit of the characteristic's UUID.
        """
        return int(str(uuid).split('-')[0], 16)

    @classmethod
    def is_feature_characteristic(self, uuid):
        """Check if the UUID is a valid feature UUID.

        Args:
            uuid (str): Characteristic's UUID.
        
        Returns:
            True if the UUID is a valid feature UUID, False otherwise.
        """
        return str(uuid).endswith(self.BLUESTSDK_FEATURES_UUID)
