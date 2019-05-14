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
# device exporting a "Stepper Motor" feature, to get its status, and to send
# commands to it.


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
from blue_st_sdk.features import *
from blue_st_sdk.utils.blue_st_exceptions import InvalidOperationException
from blue_st_sdk.utils.blue_st_exceptions import InvalidDataException


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

# Bluetooth Low Energy devices' MAC address.
IOT_DEVICE_MAC = 'e8:83:80:11:e2:37'


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


# MAIN APPLICATION

#
# Main application.
#
def main(argv):

    # Printing intro.
    print_intro()

    try:
       # Creating Bluetooth Manager.
        manager = Manager.instance()
        manager_listener = MyManagerListener()
        manager.add_listener(manager_listener)

        # Synchronous discovery of Bluetooth devices.
        print('Scanning Bluetooth devices...\n')
        manager.discover(SCANNING_TIME_s)

        # Getting discovered devices.
        discovered_devices = manager.get_nodes()
        if not discovered_devices:
            print('\nNo Bluetooth devices found. Exiting...\n')
            sys.exit(0)

        # Checking discovered devices.
        iot_device = None
        for discovered in discovered_devices:
            if discovered.get_tag() == IOT_DEVICE_MAC:
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
        print('\nGetting features...')
        iot_device_feature_stepper_motor = \
            iot_device.get_feature(feature_stepper_motor.FeatureStepperMotor)
        print('\nStepper motor feature found.')

        try:
            # Managing feature.
            iot_device_feature_stepper_motor.write_motor_command(
                feature_stepper_motor.StepperMotorCommands.MOTOR_STOP_RUNNING_WITHOUT_TORQUE)
            print('\nStepper motor status:')
            print(iot_device_feature_stepper_motor.read_motor_status())
            print('\nStepper motor moving...')
            iot_device_feature_stepper_motor.write_motor_command(
                feature_stepper_motor.StepperMotorCommands.MOTOR_MOVE_STEPS_FORWARD,
                3000
            )
            print('\nStepper motor status:')
            print(iot_device_feature_stepper_motor.read_motor_status())
        except (InvalidOperationException, InvalidDataException) as e:
            print(e)
            # Exiting.
            print('Exiting...\n')
            sys.exit(0)

        # Disconnecting from the device.
        print('\nDisconnecting from %s...' % (iot_device.get_name()))
        iot_device.disconnect()
        print('Disconnection done.')
        iot_device.remove_listener(node_listener)
        print('\nExiting...\n')

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

    main(sys.argv[1:])
