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

################################################################################
# Author:  Davide Aliprandi, STMicroelectronics                                #
################################################################################


# DESCRIPTION
#
# This application example shows how to connect to a Bluetooth Low Energy (BLE)
# device that exports "Debug" service and features, and supports the "Firmware
# Update" capability, and how to upgrade the device's firmware.
#
# Please set the "IOT_DEVICE_NAME" variable and the "Firmware file paths"
# section properly to fit your setup.


# IMPORT

from __future__ import print_function
import sys
import os
import time
import getopt
from abc import abstractmethod

from blue_st_sdk.manager import Manager
from blue_st_sdk.manager import ManagerListener
from blue_st_sdk.node import NodeListener
from blue_st_sdk.feature import FeatureListener
from blue_st_sdk.firmware_upgrade.firmware_upgrade_nucleo import FirmwareUpgradeNucleo
from blue_st_sdk.firmware_upgrade.firmware_upgrade import FirmwareUpgradeListener
from blue_st_sdk.firmware_upgrade.utils.firmware_file import FirmwareFile
from blue_st_sdk.features import *


# PRECONDITIONS
#
# In case you want to modify the SDK, clone the repository and add the location
# of the "BlueSTSDK_Python" folder to the "PYTHONPATH" environment variable.
#
# On Linux:
#   export PYTHONPATH=/home/<user>/BlueSTSDK_Python


# CONSTANTS

# Presentation message.
INTRO = """##################
# BlueST Example #
##################"""

# Bluetooth Scanning time in seconds (optional).
SCANNING_TIME_s = 5

# Number of notifications to get before disabling them.
NOTIFICATIONS = 10

# Bluetooth Low Energy devices' name.
IOT_DEVICE_NAME = 'TAI_110'

# Firmware file paths.
FIRMWARE_FOLDER = '/home/_user_/LinuxGW/SensorTile_Binaries/AI/'
FIRMWARE_EXTENSION = '.bin'
FIRMWARE_FILENAMES = [
    'SENSING1_ASC', \
    'SENSING1_HAR_GMP'
]


# FUNCTIONS

#
# Printing intro.
#
def print_intro():
    print('\n' + INTRO + '\n')


# INTERFACES

#
# Implementation of the interface used by the Manager class to notify that a new
# node has been discovered or that the scanning starts/stops.
#
class MyManagerListener(ManagerListener):

    #
    # This method is called whenever a discovery process starts or stops.
    #
    # @param manager Manager instance that starts/stops the process.
    # @param enabled True if a new discovery starts, False otherwise.
    #
    def on_discovery_change(self, manager, enabled):
        print('Discovery %s.' % ('started' if enabled else 'stopped'))
        if not enabled:
            print()

    #
    # This method is called whenever a new node is discovered.
    #
    # @param manager Manager instance that discovers the node.
    # @param node    New node discovered.
    #
    def on_node_discovered(self, manager, node):
        print('New device discovered: %s.' % (node.get_name()))


#
# Implementation of the interface used by the Node class to notify that a node
# has updated its status.
#
class MyNodeListener(NodeListener):

    #
    # To be called whenever a node connects to a host.
    #
    # @param node Node that has connected to a host.
    #
    def on_connect(self, node):
        print('Device %s connected.' % (node.get_name()))

    #
    # To be called whenever a node disconnects from a host.
    #
    # @param node       Node that has disconnected from a host.
    # @param unexpected True if the disconnection is unexpected, False otherwise
    #                   (called by the user).
    #
    def on_disconnect(self, node, unexpected=False):
        print('Device %s disconnected%s.' % \
            (node.get_name(), ' unexpectedly' if unexpected else ''))


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
    def on_update(self, feature, sample):
        print(feature)


#
# Implementation of the interface used by the FirmwareUpgrade class to notify
# changes when upgrading the firmware.
#
class MyFirmwareUpgradeListener(FirmwareUpgradeListener):

    #
    # To be called whenever the firmware has been upgraded correctly.
    #
    # @param debug_console Debug console.
    # @param firmware_file Firmware file.
    # @param bytes_sent    Data sent in bytes.
    #
    def on_upgrade_firmware_complete(self, debug_console, firmware_file, \
        bytes_sent):
        global firmware_upgrade_completed

        print('%d bytes out of %d sent...' % (bytes_sent, bytes_sent))
        print('Firmware upgrade completed successfully.')
        firmware_upgrade_completed = True

    #
    # To be called whenever there is an error in upgrading the firmware.
    #
    # @param debug_console Debug console.
    # @param firmware_file Firmware file.
    # @param error         Error code.
    #
    def on_upgrade_firmware_error(self, debug_console, firmware_file, error):
        print('Firmware upgrade error: %s.' % (str(error)))
        firmware_upgrade_completed = True

    #
    # To be called whenever there is an update in upgrading the firmware, i.e. a
    # block of data has been correctly sent and it is possible to send a new one.
    #
    # @param debug_console Debug console.
    # @param firmware_file Firmware file.
    # @param bytes_sent    Data sent in bytes.
    # @param bytes_to_send Data to send in bytes.
    #
    def on_upgrade_firmware_progress(self, debug_console, firmware_file, \
        bytes_sent, bytes_to_send):
        print('%d bytes out of %d sent...' % (bytes_sent, bytes_to_send))


# MAIN APPLICATION

#
# Main application.
#
def main(argv):
    global firmware_upgrade_completed

    # Printing intro.
    print_intro()

    try:
       # Creating Bluetooth Manager.
        manager = Manager.instance()
        manager_listener = MyManagerListener()
        manager.add_listener(manager_listener)

        while True:
            # Synchronous discovery of Bluetooth devices.
            print('Scanning Bluetooth devices...\n')
            manager.discover(SCANNING_TIME_s)

            # Getting discovered devices.
            discovered_devices = manager.get_nodes()
            if not discovered_devices:
                print('No Bluetooth devices found. Exiting...\n')
                sys.exit(0)

            # Checking discovered devices.
            device = None
            for discovered in discovered_devices:
                if discovered.get_name() == IOT_DEVICE_NAME:
                    device = discovered
                    break
            if not device:
                print('Bluetooth setup incomplete. Exiting...\n')
                sys.exit(0)

            # Connecting to the devices.
            node_listener = MyNodeListener()
            device.add_listener(node_listener)
            print('Connecting to %s...' % (device.get_name()))
            if not device.connect():
                print('Connection failed.\n')
                print('Bluetooth setup incomplete. Exiting...\n')
                sys.exit(0)
            print('Connection done.')

            # Getting features.
            print('\nFeatures:')
            i = 1
            features = []
            for desired_feature in [
                feature_audio_scene_classification.FeatureAudioSceneClassification,
                feature_activity_recognition.FeatureActivityRecognition]:
                feature = device.get_feature(desired_feature)
                if feature:
                    features.append(feature)
                    print('%d) %s' % (i, feature.get_name()))
                    i += 1
            if not features:
                print('No features found.')
            print('%d) Firmware upgrade' % (i))

            # Selecting an action.
            while True:
                choice = int(input('\nSelect an action '
                                   '(\'0\' to quit): '))
                if choice >= 0 and choice <= len(features) + 1:
                    break

            if choice == 0:
                # Disconnecting from the device.
                print('\nDisconnecting from %s...' % (device.get_name()))
                device.disconnect()
                print('Disconnection done.')
                device.remove_listener(node_listener)
                # Exiting.
                manager.remove_listener(manager_listener)
                print('Exiting...\n')
                sys.exit(0)

            elif choice == i:
                try:
                    # Selecting firmware.
                    i = 1
                    for filename in FIRMWARE_FILENAMES:
                        print('%d) %s' % (i, filename))
                        i += 1
                    while True:
                        choice = int(input("\nSelect a firmware (\'0\' to cancel): "))
                        if choice >= 0 and choice <= len(FIRMWARE_FILENAMES):
                            break

                    # Upgrading firmware.
                    if choice != 0:
                        print('\nUpgrading firmware...')
                        upgrade_console = FirmwareUpgradeNucleo.get_console(device)
                        upgrade_console_listener = MyFirmwareUpgradeListener()
                        upgrade_console.add_listener(upgrade_console_listener)
                        firmware = FirmwareFile(
                            FIRMWARE_FOLDER +
                            FIRMWARE_FILENAMES[choice - 1] +
                            FIRMWARE_EXTENSION)
                        upgrade_console.upgrade_firmware(firmware)

                        # Getting notifications about firmware upgrade process.
                        while not firmware_upgrade_completed:
                            if device.wait_for_notifications(0.05):
                                continue

                except (OSError, ValueError) as e:
                    print(e)

                finally:
                    # Disconnecting from the device.
                    if 'upgrade_console' in locals():
                        upgrade_console.remove_listener(upgrade_console_listener)
                    print('\nDisconnecting from %s...' % (device.get_name()))
                    device.disconnect()
                    print('Disconnection done.')
                    device.remove_listener(node_listener)
                    print('\nDevice is rebooting...\n')
                    time.sleep(20)

            else:
                # Testing features.
                feature = features[choice - 1]

                # Enabling notifications.
                feature_listener = MyFeatureListener()
                feature.add_listener(feature_listener)
                device.enable_notifications(feature)

                # Getting notifications.
                n = 0
                while n < NOTIFICATIONS:
                    if device.wait_for_notifications(0.05):
                        n += 1

                # Disabling notifications.
                device.disable_notifications(feature)
                feature.remove_listener(feature_listener)

                # Disconnecting from the device.
                print('\nDisconnecting from %s...' % (device.get_name()))
                device.disconnect()
                print('Disconnection done.\n')
                device.remove_listener(node_listener)

    except KeyboardInterrupt:
        try:
            # Exiting.
            print('\nExiting...\n')
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == "__main__":

    firmware_upgrade_completed = False
    main(sys.argv[1:])
