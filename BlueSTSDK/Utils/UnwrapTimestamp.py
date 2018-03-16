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

from BlueSTSDK.PythonUtils import synchronized


# CLASSES

#
# Class that unwraps the timestamp.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#  
class UnwrapTimestamp(object):

	NEAR_TO_END_TH = (1 << 16) - 100

	#
	# Constructor.
	#
	def __init__(self):
		# Number of times the timestamp has reset.
		# The timestamp is reset whenever the received timestamp has a value
		# greater than "2^16 - 100" and it is followed by a package with a
		# smaller value.
		self._reset_times = 0

		# Last raw timestamp received from the board.
		# It is a number between "0" and "2^16-1".
		self._last_timestamp = 0

	# 
	# Add a multiple of (1&lt;&lt;16) to the timestamp reset, if needed.
	#
	# @param  timestamp Timestamp.
	# @return The unwrapped timestamp.
	#	  
	@synchronized
	def unwrap(self, timestamp):
		if self._last_timestamp > self.NEAR_TO_END_TH and self._last_timestamp > timestamp:
			self._reset_times += 1
		self._last_timestamp = timestamp
		return long(self._reset_times) * (1 << 16) + long(timestamp)
