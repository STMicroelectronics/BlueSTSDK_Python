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


"""blue_st_exceptions

The blue_st_exceptions module defines exceptions raised by the BlueSTSDK.
"""


# CLASSES

class BlueSTInvalidAdvertisingDataException(Exception):
    """Exception raised whenever an advertising data has a format not recognized
    by the BlueSTSDK."""

    def __init__(self, msg):
        """Constructor

        Args:
            msg (str): The message to raise.
        """
        super(BlueSTInvalidAdvertisingDataException, self).__init__(msg)


class BlueSTInvalidFeatureBitMaskException(Exception):
    """Exception raised whenever a bitmask has more than 1 bit set to "1"."""

    def __init__(self, msg):
        """Constructor

        Args:
            msg (str): The message to raise.
        """
        super(BlueSTInvalidFeatureBitMaskException, self).__init__(msg)


class BlueSTInvalidOperationException(Exception):
    """Exception raised whenever the operation requested is not supported."""

    def __init__(self, msg):
        """Constructor

        Args:
            msg (str): The message to raise.
        """
        super(BlueSTInvalidOperationException, self).__init__(msg)


class BlueSTInvalidDataException(Exception):
    """Exception raised whenever a feature's data are not complete."""

    def __init__(self, msg):
        """Constructor

        Args:
            msg (str): The message to raise.
        """
        super(BlueSTInvalidDataException, self).__init__(msg)
