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

from enum import Enum
import struct

from blue_st_sdk.feature import Feature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.utils.number_conversion import NumberConversion
from blue_st_sdk.utils.blue_st_exceptions import InvalidOperationException


# CLASSES

class StepperMotorStatus(Enum):
    """This class lists the types of status in which a stepper motor can found
    itself."""

    MOTOR_INACTIVE = 0  # The motor is not running.
    MOTOR_RUNNING = 1   # The motor is running.


class StepperMotorCommands(Enum):
    """This class lists the types of commands that can be given to a stepper
    motor."""

    MOTOR_STOP_RUNNING_WITHOUT_TORQUE = 0  # Stops running with HiZ.
    MOTOR_STOP_RUNNING_WITH_TORQUE = 1     # Stops running with torque applied.
    MOTOR_RUN_FORWARD = 2                  # Runs forward indefinitely.
    MOTOR_RUN_BACKWARD  = 3                # Runs backward indefinitely.
    MOTOR_MOVE_STEPS_FORWARD = 4           # Moves steps forward.
    MOTOR_MOVE_STEPS_BACKWARD = 5          # Moves steps backward.


class FeatureStepperMotor(Feature):
    """The feature handles a stepper motor.

    It can be read or written and behaves differently depending on this.
    When read, the data read is the status of the motor, and is one byte long.
    When written, the data written is the command to be executed, and can be
    either one or five bytes long (see
    :meth:`blue_st_sdk.features.feature_stepper_motor.FeatureStepperMotor.write_motor_command`
    method).
    """

    FEATURE_NAME = "Stepper Motor"
    STATUS_FEATURE_FIELDS = Field(
        "Status",
        None,
        StepperMotorStatus,
        len(StepperMotorStatus),
        0)
    STATUS_DATA_LENGTH_BYTES = 1
    COMMAND_FEATURE_FIELDS = Field(
        "Command",
        None,
        StepperMotorCommands,
        len(StepperMotorCommands),
        0)
    COMMAND_DATA_LENGTH_BYTES = 5

    def __init__(self, node):
        """Constructor.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that will send data to
                this feature.
        """
        super(FeatureStepperMotor, self).__init__(
            self.FEATURE_NAME, node, [self.STATUS_FEATURE_FIELDS])

    def extract_data(self, timestamp, data, offset):
        """Extract the data from the feature's raw data.
        
        Args:
            timestamp (int): Data's timestamp.
            data (str): The data read from the feature.
            offset (int): Offset where to start reading data.
        
        Returns:
            :class:`blue_st_sdk.feature.ExtractedData`: Container of the number
            of bytes read and the extracted data.

        Raises:
            :exc:`Exception` if the data array has not enough data to read.
        """
        if len(data) - offset < self.STATUS_DATA_LENGTH_BYTES:
            raise Exception('There are no %d bytes available to read.' \
                % (self.STATUS_DATA_LENGTH_BYTES))
        sample = Sample(
            [NumberConversion.byteToUInt8(data, offset)],
            self.get_fields_description(),
            timestamp)
        return ExtractedData(sample, self.STATUS_DATA_LENGTH_BYTES)

    @classmethod
    def get_motor_status(self, sample):
        """Get the motor status.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            int: The motor status if the sample is valid, "-1" otherwise.
        """
        if sample is not None:
            if sample._data:
                if sample._data[0] is not None:
                    return int(sample._data[0])
        return -1

    def read_motor_status(self):
        """Read the motor status.

        Returns:
            :class:`StepperMotorStatus`: The motor status.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        try:
            data = self.read_data()
            (ts, status) = struct.unpack('<Hb', data)
            return StepperMotorStatus(status)
        except InvalidOperationException as e:
            raise e

    def write_motor_command(self, command, steps=0):
        """Write the motor command.

        Args:
            command (:class:`StepperMotorCommands`):
                The command to be written.
            steps (int): The number of steps to perform, if required by the
                command.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        # The command string can be:
        # + Either one byte long: for the command itself;
        # + Or five bytes long: one byte for the command and four bytes for the
        #   number of steps, if required by the command itself.
        if not steps:
            command_str = struct.pack('B', int(command.value))
        else:
            command_str = struct.pack('=BH', int(command.value), steps)

        try:
            self.write_data(command_str)
            # To clean the BLE buffer read the feature and throw away the data.
            #if self._parent.characteristic_can_be_read(self.get_characteristic()):
            #    self.read_data()
            characteristic = self.get_characteristic()
            char_handle = characteristic.getHandle()
            data = self._parent.readCharacteristic(char_handle)
        except InvalidOperationException as e:
            raise e

    def __str__(self):
        """Get a string representing the last sample.

        Return:
            str: A string representing the last sample.
        """
        with lock(self):
            sample = self._last_sample

        if sample is None:
            return self._name + ': Unknown'
        if not sample._data:
            return self._name + ': Unknown'

        if len(sample._data) == 1:
            if self.get_motor_status(sample):
                status = 'MOTOR_RUNNING'
            else:
                status = 'MOTOR_INACTIVE'
            result = '%s(%d): %s' \
                % (self._name,
                   sample._timestamp,
                   status)
            return result
