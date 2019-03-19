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
from enum import Enum

from blue_st_sdk.firmware_upgrade.utils.stm32crc32 import STM32Crc32


# CLASSES

class FirmwareFile():

    def __init__(self, filename):
        """Constructor.

        Args:
            filename (str): File name of the firmware file.

        Raises:
            :exc:`OSError` if the file is not found or is inaccessible.
        """
        try:
            self._filename = filename
            self._fd = None
            self._set_type(self._filename)
            self._set_size(self._filename)
        except OSError as e:
            raise e

    def get_type(self):
        """Get the firmware type.

        Returns:
            :class:`blue_st_sdk.firmware_upgrade.utils.firmware_file.FirmwareType`:
            The firmware type.
        """
        return self._type

    def get_size(self):
        """Get the firmware size in bytes.

        Returns:
            int: The firmware size in bytes.
        """
        return self._size

    def _set_type(self, filename):
        """Set the firmware type.

        Args:
            filename (str): File name of the firmware file.
        """
        if filename.lower().endswith("bin"):
            self._type = FirmwareType.BIN
        #elif filename.lower().endswith("img"):
        #    self._type = FirmwareType.IMG
        else:
            self._type = FirmwareType.UNKNOWN

    def _set_size(self, filename):
        """Set the firmware size in bytes.

        Args:
            filename (str): File name of the firmware file.

        Raises:
            :exc:`OSError` if the file is not found or is inaccessible.
        """
        try:
            self._size = os.path.getsize(filename)
        except OSError as e:
            raise e

    def open(self):
        """Open the firmware file.

        Raises:
            :exc:`OSError` if the file is not found or is inaccessible.

        Returns:
            file: The file descriptor of the firmware file.
        """
        try:
            self._fd = open(self._filename, 'rb')
        except OSError as e:
            raise e

        return self._fd


    def close(self):
        """Close the firmware file.

        Raises:
            :exc:`OSError` if the file is not found or is inaccessible.
        """
        try:
            self._fd.close()
        except OSError as e:
            raise e

    def get_crc_32(self):
        """Getting the 32 bit CRC of the firmware file.

        The file size must be multiple of 32 bits.

        Raises:
            :exc:`ValueError` if the firmware file can not be read properly.

        Returns:
            int: The CRC of the firmware file.
        """
        crc = STM32Crc32()
        tmp_fd = open(self._filename, 'rb')
        tmp_size = self._size - self._size % 4
        try:
            for i in range(0, tmp_size, 4):
                data = tmp_fd.read(4)
                if len(data) == 4:
                    crc.update(data)
                else:
                    raise ValueError('Could not read data from firmware file.')
            tmp_fd.close()
            return crc.get_value()
        except ValueError as e:
            tmp_fd.close()
            raise e

class FirmwareType(Enum):
    """Firmware type.

    Currently only BIN format is handled.
    """
    UNKNOWN = 0
    BIN = 1
    #IMG = 2
