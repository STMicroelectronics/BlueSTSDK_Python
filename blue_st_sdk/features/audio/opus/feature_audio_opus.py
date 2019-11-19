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

# Opus Codec #
import ctypes
import opuslib
import opuslib.api
import opuslib.api.decoder

import array

from blue_st_sdk.feature import Feature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.utils.number_conversion import LittleEndian
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidDataException


# CLASSES

class FeatureAudioOpus(Feature):
    """The feature handles the compressed audio data acquired from a microphone.

    Data is a set of twenty bytes array
    """
    FEATURE_NAME = "Opus Audio"
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
    
    OPUS_PACKET_LENGTH = 320 #shorts
    
    
    
    mBVOpusProtocolManager = None
    
    def __init__(self, node):
        """Constructor.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that will send data to
                this feature.
        """
        super(FeatureAudioOpus, self).__init__(
            self.FEATURE_NAME, node, [self.FEATURE_FIELDS])
        FeatureAudioOpus.mBVOpusProtocolManager=OpusProtocolManager()
            
    def extract_data(self, timestamp, data, offset):
        """Extract the data from the feature's raw data.

        Args:
            data (bytearray): The data read from the feature (a 20 bytes array).
            offset (int): Offset where to start reading data (0 by default).
        
        Returns:
            :class:`blue_st_sdk.feature.ExtractedData`: Container of the number
            of decoded bytes, 20 bytes per packet (None until an opus packet has 
            been reconstructed, then filled with the 320 decoded shorts array).

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
                if the data array has not enough data to read.
        """
        if data is None or len(data) == 0:
            raise BlueSTInvalidDataException(
                'There are no %d bytes available to read.' \
                % (self.DATA_LENGTH_BYTES))
        
        data_byte = bytearray(data)
        
        data_pkt = self.mBVOpusProtocolManager.getDecodedPacket(data_byte)
        
        sample = Sample(
            data_pkt,
            self.get_fields_description(),
            None)
        return ExtractedData(sample, len(data_byte))

class OpusProtocolManager(object):
    """The feature contains all mandatory Opus configuration parameters
    
    and implements the decoder function
    """
    
    BV_OPUS_TP_START_PACKET = 0
    BV_OPUS_TP_START_END_PACKET = 32
    BV_OPUS_TP_MIDDLE_PACKET = 64
    BV_OPUS_TP_END_PACKET = 128
    
    OPUS_MS = 20
    OPUS_DEC_SAMPLING_FREQ = 16000
    OPUS_DEC_CHANNELS = 1
    OPUS_DEC_FRAME_SIZE_PCM = ((OPUS_DEC_SAMPLING_FREQ/1000)*OPUS_MS)
    
    OPUScoded = []
    OPUSoutputPCM = [None] * FeatureAudioOpus.OPUS_PACKET_LENGTH
    dec = None
            
    def opusDecode(self):
        """Returns the Opus decoded packet.
        
        Returns:
            short: The actual Opus decoded packet.
        """
        arrC = ctypes.c_char_p(bytes(self.OPUScoded))
        OPUSdecodedStr = opuslib.api.decoder.decode(self.dec, arrC, len(self.OPUScoded), 320, 0, 1)
        self.OPUSoutputPCM = OPUSdecodedStr
    
    def __init__(self): 
        self.OPUScoded = []
        self.OPUScodedLen = 0
        self.OPUSoutputPCM = [None] * FeatureAudioOpus.OPUS_PACKET_LENGTH
        
        self.dec = opuslib.api.decoder.create_state(self.OPUS_DEC_SAMPLING_FREQ,self.OPUS_DEC_CHANNELS)
        version_string = opuslib.api.info.get_version_string()
        print("Opus version: " + str(version_string))
                       
    def getDecodedPacket(self, audioSample):
        """Check audioSample transport protocol byte, updates the current Opus
        encoded packet and returns None if it isn't an "END" packet, the Opus
        decoded packet elsewhere.
        
        Returns:
            short: None, or the actual Opus decoded packet.
        """         
        if audioSample[0] == self.BV_OPUS_TP_START_PACKET:
            self.OPUScoded = []
            self.OPUScoded.extend(audioSample[1:])
        elif audioSample[0] == self.BV_OPUS_TP_START_END_PACKET:
            self.OPUScoded = []
            self.OPUScoded.extend(audioSample[1:])
            self.opusDecode()
            return self.OPUSoutputPCM
        elif audioSample[0] == self.BV_OPUS_TP_MIDDLE_PACKET:
            self.OPUScoded.extend(audioSample[1:])
        elif audioSample[0] == self.BV_OPUS_TP_END_PACKET:
            self.OPUScoded.extend(audioSample[1:])
            self.opusDecode()
            return self.OPUSoutputPCM   
        return None
