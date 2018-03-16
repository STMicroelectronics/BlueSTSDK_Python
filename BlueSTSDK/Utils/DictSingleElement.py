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

import collections


# CLASSES

#
# Utility class to map keys to list of elements. It works like a dictionary with
# an exception: the "put()" method inserts a single element at a time instead of
# a list of elements.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class DictSingleElement(collections.MutableMapping):

	def __init__(self, *args, **kwargs):
		self._data = dict()
		self.update(dict(*args, **kwargs))

	def __getitem__(self, key):
		if key in self._data:
			return self._data[key]
		else:
			return None

	def __setitem__(self, key, value):
		if isinstance(value, list):
			self._data[key] = value
		else:
			self._data[key] = [value]

	def __delitem__(self, key):
		del self._data[key]

	def __iter__(self):
		return iter(self._data)

	def __len__(self):
		return len(self._data)

	#
	# Add a single element to the list associated to the given key.
	#
	# @param key   Key.
	# @param value Element to be added to the list of elements associated to the
	#			   given key.
	#
	def put(self, key, value):
		if self.__getitem__(key) == None:
			self._data[key] = [value]
		else:
			self._data[key].append(value)

	#
	# Add a single element to the list associated to the given key.
	#
	# @param dictionary A dictionary of key-value pairs to be added.
	#
	def putAll(self, dictionary):
		for key in dictionary:
			self.put(key, dictionary[key])

	#
	# Substitute "key" with "self.__keytransform__(key)" to apply an arbitrary
	# key-altering function before accessing the keys.
	#
	#def __keytransform__(self, key):
	#	return key
	#	return key.lower()
