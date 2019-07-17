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


"""number_conversion

The number_conversion module contains tools to convert features' data to
numbers.
"""


# IMPORT

import struct


# CLASSES

class NumberConversion(object):
    """This class helps to convert array of bytes to different formats, and
    viceversa.
    """

    @classmethod
    def byte_to_uint8(self, data, index = 0):
        """Returns the short value of the unsigned byte value in position
        "index".

        Args:
            data (str): Array of bytes that contains the value to convert.
            index (int): Position of the value to convert.

        Returns:
            int: The corresponding numerical value.      
        """
        # Python 2
        #return struct.unpack('B', data[index])[0]
        # Python 3
        return data[index]


class LittleEndian(object):
    """This class implements the conversion from array of bytes to different
    formats, and viceversa, in Little Endian base order.
    """

    @classmethod
    def bytes_to_int16(self, data, start = 0):
        """Return the signed short value of two bytes of the array in Little
        Endian base order.

        Args:
            data (str): Input array of bytes that contains the value to convert.
            start (int): Start index in the array of the value to convert.

        Returns:
            The corresponding numerical value.
        """
        # Python 2
        #return struct.unpack('<h', struct.pack('cc', *data[start : start + 2]))[0]
        # Python 3
        return struct.unpack('<h', data[start : start + 2])[0]

    @classmethod
    def bytes_to_int32(self, data, start = 0):
        """Return the signed integer value of four bytes of the array in Little
        Endian base order.

        Args:
            data (str): Input array of bytes that contains the value to convert.
            start (int): Start index in the array of the value to convert.

        Returns:
            The corresponding numerical value.
        """
        # Python 2
        #return struct.unpack('<i', struct.pack('cccc', *data[start : start + 4]))[0]
        # Python 3
        return struct.unpack('<i', data[start : start + 4])[0]

    @classmethod
    def bytes_to_uint16(self, data, start = 0):
        """Return the unsigned short value of two bytes of the array in Little
        Endian base order.

        Args:
            data (str): Input array of bytes that contains the value to convert.
            start (int): Start index in the array of the value to convert.

        Returns:
            The corresponding numerical value.
        """
        # Python 2
        #return struct.unpack('<H', struct.pack('cc', *data[start : start + 2]))[0]
        # Python 3
        return struct.unpack('<H', data[start : start + 2])[0]

    @classmethod
    def bytes_to_uint32(self, data, start = 0):
        """Return the unsigned integer value of four bytes of the array in
        Little Endian base order.

        Args:
            data (str): Input array of bytes that contains the value to convert.
            start (int): Start index in the array of the value to convert.

        Returns:
            The corresponding numerical value.
        """
        # Python 2
        #return struct.unpack('<I', struct.pack('cccc', *data[start : start + 4]))[0]
        # Python 3
        return struct.unpack('<I', data[start : start + 4])[0]

    @classmethod
    def bytes_to_float(self, data, start = 0):
        """Return the floating point value of four bytes of the array in Little
        Endian base order.

        Args:
            data (str): Input array of bytes that contains the value to convert.
            start (int): Start index in the array of the value to convert.

        Returns:
            The corresponding numerical value.
        """
        # Python 2
        #return struct.unpack('<f', struct.pack('cccc', *data[start : start + 4]))[0]
        # Python 3
        return struct.unpack('<f', data[start : start + 4])[0]

    @classmethod
    def int16_to_bytes(self, value):
        """Return the two bytes array corresponding to the signed short value in
        Little Endian base order.

        Args:
            value (int): Value to convert.

        Returns:
            The corresponding array of bytes.
        """
        return struct.pack("<i", value)[0:2]

    @classmethod
    def int32_to_bytes(self, value):
        """Return the four bytes array corresponding to the signed integer value
        in Little Endian base order.

        Args:
            value (int): Value to convert.

        Returns:
            The corresponding array of bytes.
        """
        return struct.pack("<q", value)[0:4]

    @classmethod
    def uint16_to_bytes(self, value):
        """Return the two bytes array corresponding to the unsigned short value
        in Little Endian base order.

        Args:
            value (int): Value to convert.

        Returns:
            The corresponding array of bytes.
        """
        return struct.pack("<I", value)[0:2]

    @classmethod
    def uint32_to_bytes(self, value):
        """Return the four bytes array corresponding to the unsigned integer
        value in Little Endian base order.

        Args:
            value (int): Value to convert.

        Returns:
            The corresponding array of bytes.
        """
        return struct.pack("<Q", value)[0:4]

    @classmethod
    def float_to_bytes(self, value):
        """Return the four bytes array corresponding to the floating point value
        in Little Endian base order.

        Args:
            value (float): Value to convert.

        Returns:
            The corresponding array of bytes.
        """
        return struct.pack("<f", value)


class BigEndian(object):
    """This class implements the conversion from array of bytes to different
    formats, and viceversa, in Big Endian base order.
    """

    @classmethod
    def bytes_to_int16(self, data, start = 0):
        """Return the signed short value of two bytes of the array in Big
        Endian base order.

        Args:
            data (str): Input array of bytes that contains the value to convert.
            start (int): Start index in the array of the value to convert.

        Returns:
            The corresponding numerical value.
        """
        # Python 2
        #return struct.unpack('>h', struct.pack('cc', *data[start : start + 2]))[0]
        # Python 3
        return struct.unpack('>h', data[start : start + 2])[0]

    @classmethod
    def bytes_to_int32(self, data, start = 0):
        """Return the signed integer value of four bytes of the array in Big
        Endian base order.

        Args:
            data (str): Input array of bytes that contains the value to convert.
            start (int): Start index in the array of the value to convert.

        Returns:
            The corresponding numerical value.
        """
        # Python 2
        #return struct.unpack('>i', struct.pack('cccc', *data[start : start + 4]))[0]
        # Python 3
        return struct.unpack('>i', data[start : start + 4])[0]

    @classmethod
    def bytes_to_uint16(self, data, start = 0):
        """Return the unsigned short value of two bytes of the array in Big
        Endian base order.

        Args:
            data (str): Input array of bytes that contains the value to convert.
            start (int): Start index in the array of the value to convert.

        Returns:
            The corresponding numerical value.
        """
        # Python 2
        #return struct.unpack('>H', struct.pack('cc', *data[start : start + 2]))[0]
        # Python 3
        return struct.unpack('>H', data[start : start + 2])[0]

    @classmethod
    def bytes_to_uint32(self, data, start = 0):
        """Return the unsigned integer value of four bytes of the array in Big
        Endian base order.

        Args:
            data (str): Input array of bytes that contains the value to convert.
            start (int): Start index in the array of the value to convert.

        Returns:
            The corresponding numerical value.
        """
        # Python 2
        #return struct.unpack('>I', struct.pack('cccc', *data[start : start + 4]))[0]
        # Python 3
        return struct.unpack('>I', data[start : start + 4])[0]

    @classmethod
    def bytes_to_float(self, data, start = 0):
        """Return the floating point value of four bytes of the array in Big
        Endian base order.

        Args:
            data (str): Input array of bytes that contains the value to convert.
            start (int): Start index in the array of the value to convert.

        Returns:
            The corresponding numerical value.
        """
        # Python 2
        #return struct.unpack('>f', struct.pack('cccc', *data[start : start + 4]))[0]
        # Python 3
        return struct.unpack('>f', data[start : start + 4])[0]

    @classmethod
    def int16_to_bytes(self, value):
        """Return the two bytes array corresponding to the signed short value in
        Big Endian base order.

        Args:
            value (int): Value to convert.

        Returns:
            The corresponding array of bytes.
        """
        return struct.pack(">i", value)[2:4]

    @classmethod
    def int32_to_bytes(self, value):
        """Return the four bytes array corresponding to the signed integer value
        in Big Endian base order.

        Args:
            value (int): Value to convert.

        Returns:
            The corresponding array of bytes.
        """
        return struct.pack(">q", value)[4:8]

    @classmethod
    def uint16_to_bytes(self, value):
        """Return the two bytes array corresponding to the unsigned short value
        in Big Endian base order.

        Args:
            value (int): Value to convert.

        Returns:
            The corresponding array of bytes.
        """
        return struct.pack(">I", value)[2:4]

    @classmethod
    def uint32_to_bytes(self, value):
        """Return the four bytes array corresponding to the unsigned integer
        value in Big Endian base order.

        Args:
            value (int): Value to convert.

        Returns:
            The corresponding array of bytes.
        """
        return struct.pack(">Q", value)[4:8]

    @classmethod
    def float_to_bytes(self, value):
        """Return the four bytes array corresponding to the floating point value
        in Big Endian base order.

        Args:
            value (int): Value to convert.

        Returns:
            The corresponding array of bytes.
        """
        return struct.pack(">f", value)
