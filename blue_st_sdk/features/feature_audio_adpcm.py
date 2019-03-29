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
from blue_st_sdk.utils.bv_audio_sync_manager import BVAudioSyncManager
from blue_st_sdk.utils.blue_st_exceptions import InvalidDataException


# CLASSES

class FeatureAudioADPCM(Feature):
    """The feature handles the compressed audio data acquired from a microphone.

    Data is a twenty bytes array
    """
    FEATURE_NAME = "ADPCM Audio"
    FEATURE_UNIT = None
    FEATURE_DATA_NAME = "Audio"
    DATA_MAX = 0
    DATA_MIN = 256
    FEATURE_FIELDS = Field(
        FEATURE_DATA_NAME,
        FEATURE_UNIT,
        FieldType.ByteArray,
        DATA_MAX,
        DATA_MIN)
    DATA_LENGTH_BYTES = 20
    AUDIO_PACKAGE_SIZE = 40
    
    bvSyncManager = None
    engineADPCM = None
    
    def __init__(self, node):
        """Constructor.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that will send data to
                this feature.
        """
        global bvSyncManager
        super(FeatureAudioADPCM, self).__init__(
            self.FEATURE_NAME, node, [self.FEATURE_FIELDS])
            
        FeatureAudioADPCM.bvSyncManager=BVAudioSyncManager()
        FeatureAudioADPCM.engineADPCM=ADPCMEngine()
            
    def extract_data(self, timestamp, data, offset):
        """Extract the data from the feature's raw data.
        
        Args:
            data (bytearray): The data read from the feature (a 20 bytes array).
            offset (int): Offset where to start reading data (0 by default).
        
        Returns:
            :class:`blue_st_sdk.feature.ExtractedData`: Container of the number
            of bytes read (20)  and the extracted data (audio info, the 40
            shorts array).

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidDataException`
                if the data array has not enough data to read.
        """
        if len(data) != self.DATA_LENGTH_BYTES:
            raise InvalidDataException(
                'There are no %d bytes available to read.' \
                % (self.DATA_LENGTH_BYTES))
        
        dataByte = bytearray(data)
        
        dataPkt = [None] * self.AUDIO_PACKAGE_SIZE
        for x in range(0,self.AUDIO_PACKAGE_SIZE/2):
            dataPkt[2*x] = self.engineADPCM.decode((dataByte[x] & 0x0F), self.bvSyncManager)
            dataPkt[(2*x)+1] = self.engineADPCM.decode(((dataByte[x] >> 4) & 0x0F), self.bvSyncManager)
        
        sample = Sample(
            dataPkt,
            self.get_fields_description(),
            None)
        return ExtractedData(sample, self.DATA_LENGTH_BYTES)
    
    @classmethod
    def get_audio(self, sample):
        """Get the audio data from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.
        
        Returns:
            short[]: audio values if the data array is valid, None[]
            otherwise.
        """
        audioPckt = []
        if sample is not None:
            if sample._data:
                if sample._data[0] is not None:
                    length = len(sample._data)
                    audioPckt = [None] * length
                    
                    for i in range(0,length):
                        if sample.data[i] != None:
                            audioPckt[i] = LittleEndian.bytes_to_int16(sample._data[i], (2*i))
                    return audioPckt
        return audioPckt
    
    def set_audio_sync_parameters(self, sample):
        """Set the object synchronization parameters necessary to the
		   decompression process.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Extracted sample which
                contains the synchronization parameters.
        """
        self.bvSyncManager.setSyncParams(sample)

class ADPCMEngine(object):
    """DPCM Engine class.
    It contains all the operations and parameters necessary to decompress the
    received audio.
    """
    
    def __init__(self): 
        """Constructor."""

        #Quantizer step size lookup table 
        self.StepSizeTable=[7,8,9,10,11,12,13,14,16,17,
            19,21,23,25,28,31,34,37,41,45,
            50,55,60,66,73,80,88,97,107,118,
            130,143,157,173,190,209,230,253,279,307,
            337,371,408,449,494,544,598,658,724,796,
            876,963,1060,1166,1282,1411,1552,1707,1878,2066,
            2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,
            5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,
            15289,16818,18500,20350,22385,24623,27086,29794,32767]

        # Table of index changes 
        self.IndexTable = [-1,-1,-1,-1,2,4,6,8,-1,-1,-1,-1,2,4,6,8]
        
        self.index = 0
        self.predsample = 0

    def decode(self, code, syncManager): 
        """ADPCM_Decode.
        
        Args:
            code (byte): It contains a 4-bit ADPCM sample.
        
        Returns:
            int: A 16-bit ADPCM sample.
        """
        # 1. get sample
        if (syncManager is not None and syncManager.isIntra()):
            self.index = syncManager.get_index_in()
            self.predsample = syncManager.get_predsample_in()
            syncManager.reinitResetFlag()
        step = self.StepSizeTable[self.index]

        # 2. inverse code into diff 
        diffq = step>> 3
        if ((code&4)!=0):
            diffq += step
        
        if ((code&2)!=0):
            diffq += step>>1
        

        if ((code&1)!=0):
            diffq += step>>2

        # 3. add diff to predicted sample
        if ((code&8)!=0):
            self.predsample -= diffq
        
        else:
            self.predsample += diffq
        
        # check for overflow
        if (self.predsample > 32767):
            self.predsample = 32767

        elif (self.predsample < -32768):
            self.predsample = -32768

        # 4. find new quantizer step size 
        self.index += self.IndexTable [code]
        #check for overflow
        if (self.index < 0):
            self.index = 0
            
        if (self.index > 88):
            self.index = 88

        # 5. save predict sample and index for next iteration 
        # done! static variables 

        # 6. return speech sample
        return self.predsample
