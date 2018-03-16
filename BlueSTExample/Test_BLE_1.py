#!/usr/bin/env python

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

from __future__ import print_function
import sys
import os
import time
import getopt
import math
import binascii
import itertools
import uuid
import json
import unicodedata
from abc import ABCMeta, abstractmethod
from bluepy.btle import BTLEException, DefaultDelegate

from BlueSTSDK.Manager import Manager, ManagerListener
from BlueSTSDK.Node import NodeListener
from BlueSTSDK.Feature import FeatureListener


# PREREQUISITES
# Please remember to add to the "PYTHONPATH" environment variable the parent
# folder of the "BlueSTSDK" package.
# On Linux:
#   export PYTHONPATH=/home/<user>/.../<parent-of-BlueSTSDK>/


INTRO = """##################
# BlueST Example #
##################"""


# CONSTANTS

SCANNING_TIME_s = 5


# FUNCTIONS

# Printing intro
def print_intro():
	print('\n' + INTRO + '\n')


# INTERFACES

#
# Implementation of the interface used by the Manager class to notify that a new
# Node has been discovered or that the scanning starts/stops.
#
class MyManagerListener(ManagerListener):

	#
	# This method is called whenever a discovery process starts or stops.
	#
	# @param manager Manager that starts/stops the process.
	# @param enabled True if a new discovery starts, False otherwise.
	#
	def onDiscoveryChange(self, manager, enabled):
		print('Discovery %s.' % ('started' if enabled else 'stopped'))

	#
	# This method is call whenever the Manager discovers a new node.
	#
	# @param manager Manager that discovers the node.
	# @param node	New node discovered.
	#
	def onNodeDiscovered(self, manager, node):
		print('New device discovered: %s.' % (node.getName()))


#
# Implementation of the interface used by the Node class to notify that a node
# has updated its status.
#
class MyNodeListener(NodeListener):

	#
	# To be called whenever a node changes its status.
	#
	# @param node       Node that has changed its status.
	# @param new_status New node status.
	# @param old_status Old node status.
	#
	def onStatusChange(self, node, new_status, old_status):
		print('Device %s went from %s to %s.' %
			(node.getName(), str(old_status), str(new_status)))


#
# Implementation of the interface used by the Feature class to notify that a
# feature has updated its data.
#
class MyFeatureListener(FeatureListener):

	#
	# To be called whenever the feature updates its data.
	#
	# @param feature Feature that has updated.
	# @param sample  Data extracted from the feature.
	#
	def onUpdate(self, feature, sample):
		print(feature)


# MAIN APPLICATION

def main(argv):

	# Number of notifications to get before disabling them.
	NOTIFICATIONS = 10

	# Printing intro.
	print_intro()

	try:
		# Creating Bluetooth Manager.
		manager = Manager.instance()
		manager_listener = MyManagerListener()
		manager.addListener(manager_listener)

		while True:
			# Synchronous discovery of Bluetooth devices.
			print('\nScanning Bluetooth devices...\n')
			manager.discover(False, SCANNING_TIME_s)

			# Getting discovered nodes.
			nodes = manager.getNodes()

			# Listing discovered nodes.
			if not nodes:
				print('\nNo Bluetooth devices found.')
				sys.exit(0)
			print('\nAvailable Bluetooth devices:')
			i = 1
			for node in nodes:
				print('%d) %s: [%s]' % (i, node.getName(), node.getTag()))
				i += 1

			# Selecting a node.
			while True:
				choice = int(input("\nSelect a device (\'0\' to quit): "))
				if choice >= 0 and choice <= len(nodes):
					break
			if choice == 0:
				# Exiting.
				manager.removeListener(manager_listener)
				print()
				sys.exit(0)
			node = nodes[choice - 1]
			
			# Connecting to the node.
			node_listener = MyNodeListener()
			node.addListener(node_listener)
			print('\nConnecting to %s...' % (node.getName()))
			node.connect()
			print('Connection done.')

			while True:
				# Getting features.
				print('\nFeatures:')
				i = 1
				features = node.getFeatures()
				for feature in features:
					print('%d) %s' % (i, feature.getName()))
					i += 1

				# Selecting a feature.
				while True:
					choice = int(input('\nSelect a feature '
									   '(\'0\' to disconnect): '))
					if choice >= 0 and choice <= len(features):
						break
				if choice == 0:
					# Disconnecting from the node.
					print('\nDisconnecting from %s...' % (node.getName()))
					node.disconnect()
					print('Disconnection done.')
					node.removeListener(node_listener)
					# Reset discovery.
					manager.resetDiscovery()
					# Going back to the list of devices.
					break
				feature = features[choice - 1]

				# Enabling notifications.
				feature_listener = MyFeatureListener()
				feature.addListener(feature_listener)
				node.enableNotifications(feature)

				# Getting notifications.
				i = 0
				while True:
					if node.waitForNotifications(0.05):
						i += 1
						continue
					if i >= NOTIFICATIONS:
						break

				# Disabling notifications.
				node.disableNotifications(feature)
				feature.removeListener(feature_listener)

	except BTLEException as e:
		print(e)
		print('\nScanning requires root privilege, '
			  'so please run the script with \"sudo\".\n')
	except KeyboardInterrupt:
		try:
			sys.exit(0)
		except SystemExit:
			os._exit(0)


if __name__ == "__main__":

	main(sys.argv[1:])
