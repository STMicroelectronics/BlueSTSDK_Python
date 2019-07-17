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
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidDataException


# CLASSES
        
class FeatureAudioADPCMSync(Feature):
    """The feature handles the audio synchronization parameters mandatory to the
    ADPCM audio decompression.
    """

    FEATURE_NAME = "ADPCM Sync"
    FEATURE_UNIT = None
    FEATURE_DATA_NAME = ["ADPCM_index", "ADPCM_predsample"]
    DATA_MAX = 32767
    DATA_MIN = -32768
    ADPCM_INDEX_INDEX = 0
    ADPCM_PREDSAMPLE_INDEX = 1
    FEATURE_INDEX_FIELD = Field(
        FEATURE_DATA_NAME[ADPCM_INDEX_INDEX],
        FEATURE_UNIT,
        FieldType.Int16,
        DATA_MAX,
        DATA_MIN)
    FEATURE_PREDSAMPLE_FIELD = Field(
        FEATURE_DATA_NAME[ADPCM_PREDSAMPLE_INDEX],
        FEATURE_UNIT,
        FieldType.Int32,
        DATA_MAX,
        DATA_MIN)
    DATA_LENGTH_BYTES = 6
    
    def __init__(self, node):
        """Constructor.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that will send data to
                this feature.
        """
        super(FeatureAudioADPCMSync, self).__init__(
            self.FEATURE_NAME, node, [self.FEATURE_INDEX_FIELD,
                                      self.FEATURE_PREDSAMPLE_FIELD])
    
    def extract_data(self, timestamp, data, offset):
        """Extract the audio sync data from the feature's raw data.
           In this case it reads a short integer (adpcm_index) and an integer
           (adpcm_predsample).

        Args:
            data (bytearray): The data read from the feature (a 6 bytes array).
            offset (int): Offset where to start reading data (0 by default).
        
        Returns:
            :class:`blue_st_sdk.feature.ExtractedData`: Container of the number
            of bytes read (6)  and the extracted data (audio sync info, a short
            and an int).

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
                if the data array has not enough data to read.
        """
        if len(data) != self.DATA_LENGTH_BYTES:
            raise BlueSTInvalidDataException(
                'There are no %d bytes available to read.' \
                % (self.DATA_LENGTH_BYTES))
            
        sample = Sample(
            [LittleEndian.bytes_to_int16(data, 0),
             LittleEndian.bytes_to_int32(data, 2)],
            self.get_fields_description(),
            None)
        return ExtractedData(sample, self.DATA_LENGTH_BYTES)
    
    @staticmethod
    def get_index(sample):
        """Method which extract the index synchronization parameter from a buffer
           passed as parameter

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data (6 bytes).
        
        Returns:
            short: The ADPCM index synch parameter if the data array is
            valid, "None" otherwise.
        """
        if sample is not None:
            if sample._data:
                return sample._data[FeatureAudioADPCMSync.ADPCM_INDEX_INDEX]
        return None
    
    @staticmethod
    def get_predicted_sample(sample):
        """Method which extract the predsample synchronization parameter from a
           buffer passed as parameter

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data (6 bytes).
        
        Returns:
            short: The ADPCM predsample synch parameter if the data array is
            valid, "None" otherwise.
        """
        if sample is not None:
            if sample._data:
                return sample._data[FeatureAudioADPCMSync.ADPCM_PREDSAMPLE_INDEX]
        return None
        
