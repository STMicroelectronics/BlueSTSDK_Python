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

import struct


# CLASSES

# 
# This class helps to convert array of bytes to different formats, and viceversa.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#  
class NumberConversion(object):

	# 
	# Returns the short value that contains the unsigned byte value of the byte
	# in position "index".
	#
	# @param data   Array of bytes that contains the value to convert.
	# @param index Position of the value to convert.
	# @return The unsigned byte value converted.
	#	  
	@classmethod
	def byteToUInt8(self, data, index = 0):
		return int((data[index] & 0xFF))


#
# This class implements the conversion from array of bytes to different
# formats, and viceversa, in Little Endian base order.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class LittleEndian(object):

	#
	# Return the signed short value of two bytes of the array in Little
	# Endian base order.
	#
	# @param data  Input array of bytes that contains the value to convert.
	# @param start Start index in the array of the value to convert.
	# @return The corresponding value.
	#
	@classmethod
	def bytesToInt16(self, data, start = 0):
		#return ByteBuffer.wrap(data, start, 2).order(ByteOrder.LITTLE_ENDIAN).getShort()
		return struct.unpack("<h", struct.pack('cc', *data[start : start + 2]))[0]

	#
	# Return the signed integer value of four bytes of the array in Little
	# Endian base order.
	#
	# @param data  Input array of bytes that contains the value to convert.
	# @param start Start index in the array of the value to convert.
	# @return The corresponding value.
	#
	@classmethod
	def bytesToInt32(self, data, start = 0):
		#return ByteBuffer.wrap(data, start, 4).order(ByteOrder.LITTLE_ENDIAN).getInt()
		return struct.unpack("<i", struct.pack('cccc', *data[start : start + 4]))[0]

	#
	# Return the unsigned short value of two bytes of the array in Little
	# Endian base order.
	#
	# @param data  Input array of bytes that contains the value to convert.
	# @param start Start index in the array of the value to convert.
	# @return The corresponding value.
	#
	@classmethod
	def bytesToUInt16(self, data, start = 0):
		#return ByteBuffer.wrap(data, start, 2).order(ByteOrder.LITTLE_ENDIAN).getShort() & 0xFFFF
		return struct.unpack("<H", struct.pack('cc', *data[start : start + 2]))[0]

	#
	# Return the unsigned integer value of four bytes of the array in Little
	# Endian base order.
	#
	# @param data  Input array of bytes that contains the value to convert.
	# @param start Start index in the array of the value to convert.
	# @return The corresponding value.
	#
	@classmethod
	def bytesToUInt32(self, data, start = 0):
		#return ((long(ByteBuffer.wrap(data, start, 4).order(ByteOrder.LITTLE_ENDIAN).getInt())) & 0xFFFFFFFFL)
		return struct.unpack("<I", struct.pack('cccc', *data[start : start + 4]))[0]

	#
	# Return the floating point value of four bytes of the array in Little
	# Endian base order.
	#
	# @param data  Input array of bytes that contains the value to convert.
	# @param start Start index in the array of the value to convert.
	# @return The corresponding value.
	#
	@classmethod
	def bytesToFloat(self, data, start = 0):
		#return Float.intBitsToFloat(self.bytesToInt32(data, start))
		return struct.unpack("<f", struct.pack('cccc', *data[start : start + 4]))[0]

	#
	# Return the two bytes array corresponding to the signed short value
	# in Little Endian base order.
	#
	# @param value The value to convert.
	# @return The corresponding array of bytes.
	#
	@classmethod
	def int16ToBytes(self, value):
		#return ByteBuffer.allocate(2).order(ByteOrder.LITTLE_ENDIAN).putShort(value).array()
		return struct.pack("<i", value)[0:2]

	#
	# Return the four bytes array corresponding to the signed integer value
	# in Little Endian base order.
	#
	# @param value The value to convert.
	# @return The corresponding array of bytes.
	#
	@classmethod
	def int32ToBytes(self, value):
		#return ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt(value).array()
		return struct.pack("<q", value)[0:4]

	#
	# Return the two bytes array corresponding to the unsigned short value
	# in Little Endian base order.
	#
	# @param value The value to convert.
	# @return The corresponding array of bytes.
	#
	@classmethod
	def uint16ToBytes(self, value):
		#return ByteBuffer.allocate(2).order(ByteOrder.LITTLE_ENDIAN).putShort(int((value & 0xFFFF))).array()
		return struct.pack("<I", value)[0:2]

	#
	# Return the four bytes array corresponding to the unsigned integer
	# value in Little Endian base order.
	#
	# @param value The value to convert.
	# @return The corresponding array of bytes.
	#
	@classmethod
	def uint32ToBytes(self, value):
		#return ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt(int((value & 0xFFFFFFFFL))).array()
		return struct.pack("<Q", value)[0:4]

	#
	# Return the four bytes array corresponding to the floating point value
	# in Little Endian base order.
	#
	# @param value The value to convert.
	# @return The corresponding array of bytes.
	#
	@classmethod
	def floatToBytes(self, value):
		#return ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putFloat(value).array()
		return struct.pack("<f", value)


#
# This class implements the conversion from array of bytes to different
# formats, and viceversa, in Big Endian base order.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class BigEndian(object):

	#
	# Return the signed short value of two bytes of the array in Big
	# Endian base order.
	#
	# @param data  Input array of bytes that contains the value to convert.
	# @param start Start index in the array of the value to convert.
	# @return The corresponding value.
	#
	@classmethod
	def bytesToInt16(self, data, start = 0):
		#return ByteBuffer.wrap(data, start, 2).order(ByteOrder.BIG_ENDIAN).getShort()
		return struct.unpack(">h", struct.pack('cc', *data[start : start + 2]))[0]

	#
	# Return the signed integer value of four bytes of the array in Big
	# Endian base order.
	#
	# @param data  Input array of bytes that contains the value to convert.
	# @param start Start index in the array of the value to convert.
	# @return The corresponding value.
	#
	@classmethod
	def bytesToInt32(self, data, start = 0):
		#return ByteBuffer.wrap(data, start, 4).order(ByteOrder.BIG_ENDIAN).getInt()
		return struct.unpack(">i", struct.pack('cccc', *data[start : start + 4]))[0]

	#
	# Return the unsigned short value of two bytes of the array in Big
	# Endian base order.
	#
	# @param data  Input array of bytes that contains the value to convert.
	# @param start Start index in the array of the value to convert.
	# @return The corresponding value.
	#
	@classmethod
	def bytesToUInt16(self, data, start = 0):
		#return ByteBuffer.wrap(data, start, 2).order(ByteOrder.BIG_ENDIAN).getShort() & 0xFFFF
		return struct.unpack(">H", struct.pack('cc', *data[start : start + 2]))[0]

	#
	# Return the unsigned integer value of four bytes of the array in Big
	# Endian base order.
	#
	# @param data  Input array of bytes that contains the value to convert.
	# @param start Start index in the array of the value to convert.
	# @return The corresponding value.
	#
	@classmethod
	def bytesToUInt32(self, data, start = 0):
		#return ((long(ByteBuffer.wrap(data, start, 4).order(ByteOrder.BIG_ENDIAN).getInt())) & 0xFFFFFFFFL)
		return struct.unpack(">I", struct.pack('cccc', *data[start : start + 4]))[0]

	#
	# Return the floating point value of four bytes of the array in Big
	# Endian base order.
	#
	# @param data  Input array of bytes that contains the value to convert.
	# @param start Start index in the array of the value to convert.
	# @return The corresponding value.
	#
	@classmethod
	def bytesToFloat(self, data, start = 0):
		#return Float.intBitsToFloat(self.bytesToInt32(data, start))
		return struct.unpack(">f", struct.pack('cccc', *data[start : start + 4]))[0]

	#
	# Return the two bytes array corresponding to the signed short value
	# in Big Endian base order.
	#
	# @param value The value to convert.
	# @return The corresponding array of bytes.
	#
	@classmethod
	def int16ToBytes(self, value):
		#return ByteBuffer.allocate(2).order(ByteOrder.BIG_ENDIAN).putShort(value).array()
		return struct.pack(">i", value)[2:4]

	#
	# Return the four bytes array corresponding to the signed integer value
	# in Big Endian base order.
	#
	# @param value The value to convert.
	# @return The corresponding array of bytes.
	#
	@classmethod
	def int32ToBytes(self, value):
		#return ByteBuffer.allocate(4).order(ByteOrder.BIG_ENDIAN).putInt(value).array()
		return struct.pack(">q", value)[4:8]

	#
	# Return the two bytes array corresponding to the unsigned short value
	# in Big Endian base order.
	#
	# @param value The value to convert.
	# @return The corresponding array of bytes.
	#
	@classmethod
	def uint16ToBytes(self, value):
		#return ByteBuffer.allocate(2).order(ByteOrder.BIG_ENDIAN).putShort(int((value & 0xFFFF))).array()
		return struct.pack(">I", value)[2:4]

	#
	# Return the four bytes array corresponding to the unsigned integer
	# value in Big Endian base order.
	#
	# @param value The value to convert.
	# @return The corresponding array of bytes.
	#
	@classmethod
	def uint32ToBytes(self, value):
		#return ByteBuffer.allocate(4).order(ByteOrder.BIG_ENDIAN).putInt(int((value & 0xFFFFFFFFL))).array()
		return struct.pack(">Q", value)[4:8]

	#
	# Return the four bytes array corresponding to the floating point value
	# in Big Endian base order.
	#
	# @param value The value to convert.
	# @return The corresponding array of bytes.
	#
	@classmethod
	def floatToBytes(self, value):
		#return ByteBuffer.allocate(4).order(ByteOrder.BIG_ENDIAN).putFloat(value).array()
		return struct.pack(">f", value)
