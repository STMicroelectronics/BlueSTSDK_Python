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

import sys

from blue_st_sdk.features.device_timestamp_feature import DeviceTimestampFeature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.utils.number_conversion import LittleEndian
from blue_st_sdk.utils.blue_st_exceptions import InvalidDataException


# CLASSES

class FeatureHeartRate(DeviceTimestampFeature):
    """Feature that manages the Heart Rate'sample data as defined by the
    Bluetooth specification. 

    Refer to
    `Heart Rate Measurement Specs <https://developer.bluetooth.org/gatt/characteristics/Pages/CharacteristicViewer.aspx?u=org.bluetooth.characteristic.heart_rate_measurement.xml>`_
    for more information.
    """

    FEATURE_NAME = "Heart Rate"
    HEART_RATE_INDEX = 0
    HEART_RATE_FIELD = Field("Heart Rate Measurement", "bpm", FieldType.UInt16, 0, 1 << 16)
    ENERGY_EXPENDED_INDEX = 1
    ENERGY_EXPENDED_FIELD = Field("Energy Expended", "kJ", FieldType.UInt16, 0, 1 << 16)
    RR_INTERVAL_INDEX = 2
    RR_INTERVAL_FIELD = Field("RR-Interval", "sample", FieldType.Float, 0, sys.float_info.max)
    DATA_LENGTH_BYTES = 2

    def __init__(self, node):
        """Build a new disabled feature, that doesn't need to be initialized at
        node'sample side.
    
        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that will update this
                feature.
        """
        super(FeatureHeartRate, self).__init__(
            self.FEATURE_NAME,
            node,
            [self.HEART_RATE_FIELD, self.ENERGY_EXPENDED_FIELD, self.RR_INTERVAL_FIELD]
        )

    @classmethod
    def getHeartRate(self, sample):
        """Extract the Heart Rate from the sample.
    
        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): The sample.

        Returns:
            int: The Heart Rate if available, a negative number otherwise.
        """      
        if sample is not None:
            if len(sample._data) > self.HEART_RATE_INDEX:
                hr = sample._data[self.HEART_RATE_INDEX]
                if hr is not None:
                    return int(hr)
        return -1

    @classmethod
    def getEnergyExpended(self, sample):
        """Extract the energy expended field from the sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): The sample.

        Returns:
            int: The energy expended if available, a negative number otherwise.
        """
        if sample is not None:
            if len(sample._data) > self.ENERGY_EXPENDED_INDEX:
                ee = sample._data[self.ENERGY_EXPENDED_INDEX]
                if ee is not None:
                    return int(ee)
        return -1

    @classmethod
    def getRRInterval(self, sample):
        """Extract the RR interval field from the sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): The sample.
    
        Returns:
            float: The RR interval if available, <nan> otherwise.
        """
        if sample is not None:
            if len(sample._data) > self.RR_INTERVAL_INDEX:
                rri = sample._data[self.RR_INTERVAL_INDEX]
                if rri is not None:
                    return float(rri)
        return float('nan')

    def extract_data(self, timestamp, data, offset):
        """Extract the data from the feature's raw data.
        In this case it reads a 16-bit signed integer value.

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
        if (len(data) - offset < self.DATA_LENGTH_BYTES):
            raise InvalidDataException(
                'There are no %d bytes available to read.' \
                % (self.DATA_LENGTH_BYTES))

        offset = offset
        flags = data[offset]
        offset += 1

        if self.has8BitHeartRate(flags):
            hr = data[offset]
            offset += 1
        else:
            hr = LittleEndian.bytesToUInt16(data, offset)
            offset += 2

        if self.hasEnergyExpended(flags):
            ee = LittleEndian.bytesToUInt16(data, offset)
            offset += 2
        else:
            ee = -1

        if self.hasRRInterval(flags):
            rri = LittleEndian.bytesToUInt16(data, offset) / 1024.0
            offset += 2
        else:
            rri = float('nan')

        return ExtractedData(
            Sample(
                timestamp,
                [hr, ee, rri],
                getFieldsDescription()
            ),
            offset - offset
        )

    @classmethod
    def has8BitHeartRate(self, flags):
        """Check if there is Heart Rate.

        Args:
            flags (int): Flags.

        Returns:
            bool: True if there is Heart Rate, False otherwise.
        """
        return (flags & 0x01) == 0

    @classmethod
    def hasEnergyExpended(self, flags):
        """Check if there is Energy Expended.

        Args:
            flags (int): Flags.

        Returns:
            bool: True if there is Energy Expended, False otherwise.
        """
        return (flags & 0x08) != 0

    @classmethod
    def hasRRInterval(self, flags):
        """Check if there is RR interval.

        Args:
            flags (int): Flags.
    
        Returns:
            bool: True if there is RR Interval, False otherwise.
        """
        return (flags & 0x10) != 0
