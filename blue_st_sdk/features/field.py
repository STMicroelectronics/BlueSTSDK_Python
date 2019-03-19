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


class Field(object):
    """Class that describes a feature data field.
    """

    def __init__(self, name_, unit_, type_, max_, min_):
        """Constructor.

        Args:
            name_ (str): Name.
            unit_ (str): Unit.
            type_ (:class:`blue_st_sdk.features.field.FieldType`): Type.
            max_: Maximum value. 
            min_: Minimum value.
        """
        self._name = name_
        self._unit = unit_
        self._type = type_
        self._max  = max_
        self._min  = min_

    def get_name(self):
        """Get the name.

        Returns:
            str: The name.
        """
        return self._name

    def get_unit(self):
        """Get the unit.

        Returns:
            str: The unit.
        """
        return self._unit

    def get_type(self):
        """Get the type.

        Returns:
            :class:`blue_st_sdk.features.field.FieldType`: The type.
        """
        return self._type

    def get_max(self):
        """Get the maximum value.

        Returns:
            The maximum value.
        """
        return self._max

    def get_min(self):
        """Get the minimum value.

        Returns:
            The minimum value.
        """
        return self._min

class FieldType(Enum):
    """Type of field."""
    Float = u'Float'
    Int64 = u'Int64'
    UInt32 = u'UInt32'
    Int32 = u'Int32'
    UInt16 = u'UInt16'
    Int16 = u'Int16'
    UInt8 = u'UInt8'
    Int8 = u'Int8'
    ByteArray = u'ByteArray'
    DateTime = u'DateTime'
