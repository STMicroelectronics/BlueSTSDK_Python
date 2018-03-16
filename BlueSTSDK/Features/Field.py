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


# CLASSES

# 
# Class that describes a feature data field.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class Field(object):

	#
	# Constructor.
	# The value field is set to None.
	#
	# @param _name Name.
	# @param _unit Unit.
	# @param _type Type.
	# @param _max  Maximum value.
	# @param _min  Minimum value.
	#
	def __init__(self, _name, _unit, _type, _max, _min):
		self._name = _name
		self._unit = _unit
		self._type = _type
		self._max  = _max
		self._min  = _min

	# 
	# Get the unit.
	# @return The unit.
	#	
	def getUnit(self):
		return self._unit

	# 
	# Get the name.
	# @return The name.
	#	
	def getName(self):
		return self._name

	# 
	# Get the type.
	# @return The type.
	#	
	def getType(self):
		return self._type

	# 
	# Get the maximum value.
	# @return The maximum value.
	#	
	def getMax(self):
		return self._max

	# 
	# Get the minimum value.
	# @return The minimum value.
	#	
	def getMin(self):
		return self._min

#
# Type of field.
#
class FieldType(Enum):
	Float = u'Float'
	Int64 = u'Int64'
	UInt32 = u'UInt32'
	Int32 = u'Int32'
	UInt16 = u'UInt16'
	Int16 = u'Int16'
	UInt8 = u'UInt8'
	Int8 = u'Int8'
	ByteArray = u'ByteArray'
