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
from datetime import datetime

from blue_st_sdk.feature import Feature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.utils.number_conversion import NumberConversion
from blue_st_sdk.utils.blue_st_exceptions import InvalidDataException
from blue_st_sdk.python_utils import lock


# CLASSES

class ActivityType(Enum):
    """Allowed activities."""

    NO_ACTIVITY = 0
    STATIONARY = 1
    WALKING = 2
    FASTWALKING = 3
    JOGGING = 4
    BIKING = 5
    DRIVING = 6
    STAIRS = 7
    ERROR = 8


class FeatureActivityRecognition(Feature):
    """The feature handles the activities that can be detected by a device.

    Data is one or two bytes long and has no decimal digits.
    """

    FEATURE_NAME = "Activity Recognition"
    FEATURE_UNIT = [None, "ms", None]
    FEATURE_DATA_NAME = ["Activity", "DateTime", "Algorithm"]
    DATA_MAX = 7
    DATA_MIN = 0
    ACTIVITY_INDEX = 0
    TIME_FIELD = 1
    ALGORITHM_INDEX = 2
    FEATURE_ACTIVITY_FIELD = Field(
        FEATURE_DATA_NAME[ACTIVITY_INDEX],
        FEATURE_UNIT[ACTIVITY_INDEX],
        FieldType.UInt8,
        DATA_MAX,
        DATA_MIN)
    FEATURE_TIME_FIELD = Field(
        FEATURE_DATA_NAME[TIME_FIELD],
        FEATURE_UNIT[TIME_FIELD],
        FieldType.DateTime,
        None,
        None)
    FEATURE_ALGORITHM_FIELD = Field(
        FEATURE_DATA_NAME[ALGORITHM_INDEX],
        FEATURE_UNIT[ALGORITHM_INDEX],
        FieldType.UInt8,
        0xFF,
        0)
    # This can be "2" in case there is even the algorithm type, "1" otherwise.
    DATA_LENGTH_BYTES = 1

    def __init__(self, node):
        """Constructor.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that will send data to
                this feature.
        """
        super(FeatureActivityRecognition, self).__init__(
            self.FEATURE_NAME, node, [self.FEATURE_ACTIVITY_FIELD,
                                      self.FEATURE_TIME_FIELD,
                                      self.FEATURE_ALGORITHM_FIELD])

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
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidDataException`
                if the data array has not enough data to read.
        """
        if len(data) - offset < self.DATA_LENGTH_BYTES:
            raise InvalidDataException(
                'There is no %s byte available to read.' \
                % (self.DATA_LENGTH_BYTES))
        if len(data) - offset == self.DATA_LENGTH_BYTES:
            # Extract the activity from the feature's raw data.
            sample = Sample(
                [NumberConversion.byte_to_uint8(data, offset),
                 datetime.now()],
                self.get_fields_description(),
                timestamp)
            return ExtractedData(sample, self.DATA_LENGTH_BYTES)
        else:
            # Extract the activity and the algorithm from the feature's raw data.
            sample = Sample(
                [NumberConversion.byte_to_uint8(data, offset),
                 datetime.now(),
                 NumberConversion.byte_to_uint8(data, offset + 1)],
                self.get_fields_description(),
                timestamp)
            return ExtractedData(sample, self.DATA_LENGTH_BYTES + 1)

    @classmethod
    def get_activity(self, sample):
        """Getting the recognized activity from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            :class:`ActivityType`: The recognized activity if the sample is
            valid, "ActivityType.ERROR" otherwise.
        """
        if sample is not None:
            if sample._data:
                if sample._data[self.ACTIVITY_INDEX] is not None:
                    return ActivityType(sample._data[self.ACTIVITY_INDEX])
        return ActivityType.ERROR

    @classmethod
    def get_time(self, sample):
        """Getting the date and the time from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            :class:`datetime`: The date and the time of the recognized activity
            if the sample is valid, "None" otherwise.
            Refer to
            `datetime <https://docs.python.org/2/library/datetime.html>`_
            for more information.
        """
        if sample is not None:
            if sample._data:
                if sample._data[self.TIME_FIELD] is not None:
                    return sample._data[self.TIME_FIELD]
        return None

    @classmethod
    def get_algorithm(self, sample):
        """Getting the algorithm from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            int: The algorithm if the sample is valid, "0" otherwise.
        """
        if sample is not None:
            if sample._data:
                if sample._data[self.ALGORITHM_INDEX] is not None:
                    return int(sample._data[self.ALGORITHM_INDEX])
        return 0

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

        result = ''
        if len(sample._data) >= 2:
            result = '%s(%d): Activity is \"%s\", Time is \"%s\"' \
                % (self._name,
                   sample._timestamp,
                   str(self.get_activity(sample)),
                   str(self.get_time(sample))
                   )
        if len(sample._data) == 3:
            result += ', Algorithm is \"%d\"' \
                % (self.get_algorithm(sample))
        return result
