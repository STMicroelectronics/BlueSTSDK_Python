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

from blue_st_sdk.feature import Feature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.utils.number_conversion import NumberConversion
from blue_st_sdk.utils.blue_st_exceptions import InvalidDataException


# CLASSES

class Gesture(Enum):
    """This class summarizes the types of gesture that can be recognized."""

    UNKNOWN = 0
    TAP = 1
    LEFT = 2
    RIGHT = 3
    ERROR = 4


class FeatureProximityGesture(Feature):
    """The feature handles the detected gesture using proximity sensors.

    Data is one byte long and has no decimal digits.
    """

    FEATURE_NAME = "Gesture"
    FEATURE_UNIT = None
    FEATURE_DATA_NAME = "Gesture"
    DATA_MAX = len(Gesture) - 1
    DATA_MIN = 0
    FEATURE_FIELDS = Field(
        FEATURE_DATA_NAME,
        FEATURE_UNIT,
        FieldType.UInt8,
        DATA_MAX,
        DATA_MIN)
    DATA_LENGTH_BYTES = 1

    def __init__(self, node):
        """Constructor.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that will send data to
                this feature.
        """
        super(FeatureProximityGesture, self).__init__(
            self.FEATURE_NAME, node, [self.FEATURE_FIELDS])

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
                'There is no %d byte available to read.' \
                % (self.DATA_LENGTH_BYTES))
        sample = Sample(
            [NumberConversion.byte_to_uint8(data, offset)],
            self.get_fields_description(),
            timestamp)
        return ExtractedData(sample, self.DATA_LENGTH_BYTES)

    @classmethod
    def get_gesture(self, sample):
        """Get the gesture value from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            :class:`blue_st_sdk.features.feature_proximity_gesture.Gesture`: The
            gesture value from a sample.
        """
        if sample is not None:
            if sample._data:
                if sample._data[0] is not None:
                    activity = sample._data[0]
                    if activity == 0:
                        return Gesture.UNKNOWN
                    elif activity == 1:
                        return Gesture.TAP
                    elif activity == 2:
                        return Gesture.LEFT
                    elif activity == 3:
                        return Gesture.RIGHT
                    else:
                        return Gesture.ERROR
        return Gesture.ERROR
