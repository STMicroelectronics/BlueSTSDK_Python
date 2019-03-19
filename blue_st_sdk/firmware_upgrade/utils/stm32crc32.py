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


"""firmware_file

The firmware_file module is responsible for handling a firmware file.
"""


# IMPORT

import sys
import os

from blue_st_sdk.utils.number_conversion import LittleEndian


# CLASSES

class STM32Crc32(object):
    """Computes the CRC32 by using the same algorithm implemented by STM32 chips.

    The algorithm works on unsigned integer 32 numbers, hence the buffer must
    have a length multiple of 4.
    """
    INITIAL_VALUE = 0xffffffff
    """Initial value of the CRC."""

    CRC_TABLE = [
        0x00000000, 0x04C11DB7, 0x09823B6E, 0x0D4326D9,
        0x130476DC, 0x17C56B6B, 0x1A864DB2, 0x1E475005,
        0x2608EDB8, 0x22C9F00F, 0x2F8AD6D6, 0x2B4BCB61,
        0x350C9B64, 0x31CD86D3, 0x3C8EA00A, 0x384FBDBD]
    """Nibble lookup table for 0x04C11DB7 polynomial."""

    def __init__(self):
        """Constructor."""
        self.reset()

    def _urs(self, value, n):
        """Getting the Unsigned Right Shift operation.

        E.g.:
            a >>> b

        Python does not provide a built-in operator for this, so here it is
        simulated. This assumes integers are 32 bits long.
        """
        return (value % 0x100000000) >> n

    def _crc32_fast(self, crc, data):
        """Fast CRC at 32 bits.

        Apply all 32-bits.
        Process 32-bits, 4 at a time, or 8 rounds.
        Assumes 32-bit reg, masking index to 4-bits.
        0x04C11DB7 Polynomial used in STM32 chips.
        """
        crc = crc ^ data
        crc = ((crc << 4) & 0xffffffff) ^ self.CRC_TABLE[self._urs(crc, 28)]
        crc = ((crc << 4) & 0xffffffff) ^ self.CRC_TABLE[self._urs(crc, 28)]
        crc = ((crc << 4) & 0xffffffff) ^ self.CRC_TABLE[self._urs(crc, 28)]
        crc = ((crc << 4) & 0xffffffff) ^ self.CRC_TABLE[self._urs(crc, 28)]
        crc = ((crc << 4) & 0xffffffff) ^ self.CRC_TABLE[self._urs(crc, 28)]
        crc = ((crc << 4) & 0xffffffff) ^ self.CRC_TABLE[self._urs(crc, 28)]
        crc = ((crc << 4) & 0xffffffff) ^ self.CRC_TABLE[self._urs(crc, 28)]
        crc = ((crc << 4) & 0xffffffff) ^ self.CRC_TABLE[self._urs(crc, 28)]
        return crc

    def get_value(self):
        """Get the CRC value.

        Returns:
            int: The value of the current CRC.
        """
        return self._current_crc

    def update(self, data):
        """Update the value of the CRC.

        Size of data in bytes must be multiple of 4.

        Args:
            data (bytearray): Data to compute the CRC value of.

        Raises:
            :exc:`ValueError` if the length of the data is not multiple of 4.
        """
        if len(data) % 4 != 0:
            raise ValueError('Size of data to compute the CRC on must be \
                multiple of 4 [bytes].')

        for i in range(0, len(data), 4):
            tmp = LittleEndian.bytesToInt32(data, i * 4)
            self._current_crc = self._crc32_fast(self._current_crc, tmp)

    def reset(self):
        """Reset the CRC to the initial value."""
        self._current_crc = self.INITIAL_VALUE
