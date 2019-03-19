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

from blue_st_sdk.feature import Feature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.utils.number_conversion import LittleEndian
from blue_st_sdk.utils.blue_st_exceptions import InvalidDataException


# CLASSES

class FeatureProximity(Feature):
    """The feature handles the data coming from a proximity sensor.

    Data is two bytes long and has no decimal digits.
    """

    FEATURE_NAME = "Proximity"
    FEATURE_UNIT = "mm"
    FEATURE_DATA_NAME = "Proximity"
    OUT_OF_RANGE_VALUE = 0xFFFF  # The measure is out of range_value.
    LOW_RANGE_DATA_MAX = 0x00FE  # Maximum distance in low-range_value mode.
    HIGH_RANGE_DATA_MAX = 0X7FFE  # Maximum distance in high-range_value mode.
    DATA_MIN = 0  # Minimum distance measurable.
    LOW_RANGE_FEATURE_FIELDS = Field(
        FEATURE_DATA_NAME,
        FEATURE_UNIT,
        FieldType.UInt16,
        LOW_RANGE_DATA_MAX,
        DATA_MIN)
    HIGH_RANGE_FEATURE_FIELDS = Field(
        FEATURE_DATA_NAME,
        FEATURE_UNIT,
        FieldType.UInt16,
        HIGH_RANGE_DATA_MAX,
        DATA_MIN)
    DATA_LENGTH_BYTES = 2

    def __init__(self, node):
        """Constructor.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that will send data to
                this feature.
        """
        super(FeatureProximity, self).__init__(
            self.FEATURE_NAME, node, [self.HIGH_RANGE_FEATURE_FIELDS])

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
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidDataException` if
                the data array has not enough data to read.
        """
        if len(data) - offset < self.DATA_LENGTH_BYTES:
            raise InvalidDataException(
                'There are no %d bytes available to read.' \
                % (self.DATA_LENGTH_BYTES))
        sample = None
        value = LittleEndian.bytesToUInt16(data, offset)
        if self._is_low_range_sensor(value):
            sample = self._get_low_range_sample(timestamp, value)
        else:
            sample = self._get_high_range_sample(timestamp, value)
        return ExtractedData(sample, self.DATA_LENGTH_BYTES)

    @classmethod
    def get_proximity_distance(self, sample):
        """Extract the data from the feature's raw data.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.
        
        Returns:
            int: The proximity distance value if the data array is valid, "-1"
            otherwise.
        """
        if sample is not None:
            if sample._data:
                if sample._data[0] is not None:
                    return int(sample._data[0])
        return -1

    @classmethod
    def is_out_of_range_distance(self, sample):
        """Check if the measure is out of range_value.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.
        
        Returns:
            bool: True if the proximity distance is out of range_value, False
            otherwise.
        """
        return self.get_proximity_distance(s) == self.OUT_OF_RANGE_VALUE

    @classmethod
    def _is_low_range_sensor(self, value):
        """Check if the sensor is a low-range_value sensor.

        Args:
            value (int): Measured proximity.
        
        Returns:
            bool: True if the sensor is a low-range_value sensor, False
            otherwise.
        """
        return (value & 0x8000) == 0

    @classmethod
    def _get_range_value(self, value):
        """Get the range_value value of the sensor.

        Args:
            value (int): Measured proximity.
        
        Returns:
            int: The range_value value of the sensor.
        """
        return (value & ~0x8000)

    def _get_low_range_sample(self, timestamp, value):
        """Get a sample from a low-range sensor built from the given data.

        Args:
            timestamp (int): Data's timestamp.
            value (int): Measured proximity.

        Returns:
            :class:`blue_st_sdk.feature.Sample`: A sample from a low-range
            sensor built from the given data.
        """
        range_value = self._get_range_value(value)
        if range_value > self.LOW_RANGE_DATA_MAX:
            range_value = self.OUT_OF_RANGE_VALUE
        return Sample(
            [range_value],
            [self.LOW_RANGE_FEATURE_FIELDS],
            timestamp)

    def _get_high_range_sample(self, timestamp, value):
        """Get a sample from a high-range sensor built from the given data.

        Args:
            timestamp (int): Data's timestamp.
            value (int): Measured proximity.

        Returns:
            :class:`blue_st_sdk.feature.Sample`: A sample from a high-range
            sensor built from the given data.
        """
        range_value = self._get_range_value(value)
        if range_value > self.HIGH_RANGE_DATA_MAX:
            range_value = self.OUT_OF_RANGE_VALUE
        return Sample(
            [range_value],
            [self.HIGH_RANGE_FEATURE_FIELDS],
            timestamp)

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
            distance = get_proximity_distance(sample)
            if distance != self.OUT_OF_RANGE_VALUE:
                result = '%s(%d): %s %s' \
                    % (self._name,
                       sample._timestamp,
                       str(distance),
                       self._description[0]._unit)
            else:
                result = '%s(%d): %s' \
                    % (self._name,
                       sample._timestamp,
                       'Out Of Range')
            return result
