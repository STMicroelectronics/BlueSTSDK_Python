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
# Please set the "Firmware file paths" section to fit your setup.


# IMPORT

from __future__ import print_function
import sys
import os
import time
from abc import abstractmethod
from bluepy.btle import BTLEException

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
# Please remember to add to the "PYTHONPATH" environment variable the location
# of the "BlueSTSDK_Python" SDK.
#
# On Linux:
#   export PYTHONPATH=/home/<user>/BlueSTSDK_Python


# CONSTANTS

# Presentation message.
INTRO = """##################
# BlueST Example #
##################"""

# Bluetooth Scanning time in seconds.
SCANNING_TIME_s = 5

# Number of notifications to get before disabling them.
NOTIFICATIONS = 10

# Bluetooth Low Energy devices' name.
IOT_DEVICE_NAME = 'TAI_110'

# Firmware file paths.
FIRMWARE_PATH = '/home/pi/AI_SensorTile_Binaries/'
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
    # To be called whenever a node changes its status.
    #
    # @param node       Node that has changed its status.
    # @param new_status New node status.
    # @param old_status Old node status.
    #
    def on_status_change(self, node, new_status, old_status):
        print('Device %s from %s to %s.' %
            (node.get_name(), str(old_status), str(new_status)))


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
    #
    def on_upgrade_firmware_complete(self, debug_console, firmware_file):
        global firmware_upgrade_completed

        print('Firmware upgrade completed. Device is rebooting...')
        time.sleep(10)
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
        time.sleep(5)
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
            # Synchronous discovery.
            #manager.discover(False, SCANNING_TIME_s)
            # Asynchronous discovery.
            manager.start_discovery(False, SCANNING_TIME_s)
            time.sleep(SCANNING_TIME_s)
            manager.stop_discovery()

            # Getting discovered devices.
            discovered_devices = manager.get_nodes()
            if not discovered_devices:
                print('\nNo Bluetooth devices found. Exiting...\n')
                sys.exit(0)

            # Checking discovered devices.
            iot_device = None
            for discovered in discovered_devices:
                if discovered.get_name() == IOT_DEVICE_NAME:
                    iot_device = discovered
                    break
            if not iot_device:
                print('\nBluetooth setup incomplete. Exiting...\n')
                sys.exit(0)

            # Connecting to the devices.
            node_listener = MyNodeListener()
            iot_device.add_listener(node_listener)
            print('Connecting to %s...' % (iot_device.get_name()))
            iot_device.connect()
            print('Connection done.')

            # Getting features.
            print('\nFeatures:')
            i = 1
            features = []
            for desired_feature in [
                feature_audio_scene_classification.FeatureAudioSceneClassification,
                feature_activity_recognition.FeatureActivityRecognition]:
                feature = iot_device.get_feature(desired_feature)
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
                print('\nDisconnecting from %s...' % (iot_device.get_name()))
                iot_device.disconnect()
                print('Disconnection done.')
                iot_device.remove_listener(node_listener)
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
                        upgrade_console = FirmwareUpgradeNucleo.get_console(iot_device)
                        upgrade_console_listener = MyFirmwareUpgradeListener()
                        upgrade_console.add_listener(upgrade_console_listener)
                        firmware = FirmwareFile(
                            FIRMWARE_PATH +
                            FIRMWARE_FILENAMES[choice - 1] +
                            FIRMWARE_EXTENSION)
                        upgrade_console.upgrade_firmware(firmware)

                        # Getting notifications about firmware upgrade process.
                        while not firmware_upgrade_completed:
                            if iot_device.wait_for_notifications(0.05):
                                continue

                except (OSError, ValueError) as e:
                    print(e)

                finally:
                    # Disconnecting from the device.
                    if 'upgrade_console' in locals():
                        upgrade_console.remove_listener(upgrade_console_listener)
                    print('\nDisconnecting from %s...' % (iot_device.get_name()))
                    iot_device.disconnect()
                    print('Disconnection done.\n')
                    iot_device.remove_listener(node_listener)

            else:
                # Testing features.
                feature = features[choice - 1]

                # Enabling notifications.
                feature_listener = MyFeatureListener()
                feature.add_listener(feature_listener)
                iot_device.enable_notifications(feature)

                # Getting notifications.
                n = 0
                while n < NOTIFICATIONS:
                    if iot_device.wait_for_notifications(0.05):
                        n += 1

                # Disabling notifications.
                iot_device.disable_notifications(feature)
                feature.remove_listener(feature_listener)

                # Disconnecting from the device.
                print('\nDisconnecting from %s...' % (iot_device.get_name()))
                iot_device.disconnect()
                print('Disconnection done.\n')
                iot_device.remove_listener(node_listener)

    except BTLEException as e:
        print(e)
        # Exiting.
        print('Exiting...\n')
        sys.exit(0)
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
