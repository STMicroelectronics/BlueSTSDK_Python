#!/usr/bin/env python

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

from blue_st_sdk.features.feature_audio_adpcm_sync import FeatureAudioADPCMSync

class BVAudioSyncManager(object):
    """The feature contains all mandatory ADPCM synchronization parameters

    extracted from an AudioSync received packet.
    """
    intra_flag=False
    adpcm_index_in=0
    adpcm_predsample_in=0
    
    @classmethod
    def isIntra(self):
        """Returns the intra_flag parameter state.
        
        Returns:
            boolean: True if is activated, False elsewhere.
        """
        return self.intra_flag
    
    @classmethod
    def get_index_in(self):
        """Returns the adpcm_index_in parameter value.
        
        Returns:
            int: Current adpcm index.
        """
        return self.adpcm_index_in
    
    @classmethod
    def get_predsample_in(self):
        """Returns The adpcm_predsample_in parameter value.
        
        Returns:
            short: The adpcm predsample actual value.
        """
        return self.adpcm_predsample_in
        
    @classmethod
    def reinitResetFlag(self):
        self.intra_flag = False
        
    @classmethod
    def setSyncParams(self,sample):
        """Populate all mandatory adpcm synchronization parameters from an input
           FeatureAudioADPCMSync Sample.
        
        Args:
            sample (Sample): A Sample exctracted from a received
               FeatureAudioADPCMSync synchronization packet (6 bytes)
        """
        #print("SetSync Params!")
        self.adpcm_index_in = FeatureAudioADPCMSync.getIndex(sample)
        self.adpcm_predsample_in = FeatureAudioADPCMSync.getPredictedSample(sample)
        self.intra_flag = True
