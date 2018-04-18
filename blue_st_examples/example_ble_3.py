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


# DESCRIPTION
#
# This application example shows how to connect to two Bluetooth Low Energy
# (BLE) devices exporting a "Switch" feature, and to get/set the status of the
# feature.


# IMPORT

from __future__ import print_function
import sys
import os
import time
import getopt
import json
import logging
from enum import Enum
from bluepy.btle import BTLEException

from blue_st_sdk.manager import Manager
from blue_st_sdk.manager import ManagerListener
from blue_st_sdk.node import NodeListener
from blue_st_sdk.feature import FeatureListener
from blue_st_sdk.features import *
from blue_st_sdk.utils.blue_st_exceptions import InvalidOperationException


# PRECONDITIONS
#
# Please remember to add to the "PYTHONPATH" environment variable the parent
# folder of the "blue_st_sdk" package.
#
# On Linux:
#   export PYTHONPATH=/home/pi/BlueSTSDK_Python


# CONSTANTS

INTRO = """##################
# BlueST Example #
##################"""


# BLUETOOTH DEVICES

# Put here the MAC address of your Bluetooth Low Energy and Switch enabled
# devices.
SWITCH_DEVICE_1_MAC = 'd7:90:95:be:58:7e'
SWITCH_DEVICE_2_MAC = 'd1:07:fd:84:30:8c'


# TIMEOUTS

SCANNING_TIME_s = 5


# SWITCH STATUS

class SwitchStatus(Enum):
    OFF = 0
    ON = 1


# UTILITY FUNCTIONS

# Printing intro
def print_intro():
    print('\n' + INTRO + '\n')


# LISTENERS

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
        print('Device %s went from %s to %s.' %
            (node.get_name(), str(old_status), str(new_status)))


#
# Implementation of the interface used by the Feature class to notify that a
# feature has updated its status.
#
class MyFeatureSwitchDevice1Listener(FeatureListener):

    def on_update(self, feature, sample):
        global switch_device_2, switch_device_2_feature, switch_device_2_status

        toggle_switch_status = feature_switch.FeatureSwitch.get_switch_status(sample)
        if toggle_switch_status:

            # Toggle switch status.
            switch_device_2_status = SwitchStatus.ON if switch_device_2_status == SwitchStatus.OFF else SwitchStatus.OFF 
            
            # Writing switch status.
            switch_device_2.disable_notifications(switch_device_2_feature)
            switch_device_2_feature.write_switch_status(switch_device_2_status.value)
            switch_device_2.enable_notifications(switch_device_2_feature)


#
# Implementation of the interface used by the Feature class to notify that a
# feature has updated its status.
#
class MyFeatureSwitchDevice2Listener(FeatureListener):

    def on_update(self, feature, sample):
        global switch_device_1, switch_device_1_feature, switch_device_1_status

        toggle_switch_status = feature_switch.FeatureSwitch.get_switch_status(sample)
        if toggle_switch_status:

            # Toggle switch status.
            switch_device_1_status = SwitchStatus.ON if switch_device_1_status == SwitchStatus.OFF else SwitchStatus.OFF 
            
            # Writing switch status.
            switch_device_1.disable_notifications(switch_device_1_feature)
            switch_device_1_feature.write_switch_status(switch_device_1_status.value)
            switch_device_1.enable_notifications(switch_device_1_feature)


# MAIN APPLICATION

# This application example connects to two Bluetooth Low Energy devices and
# allows each of the two devices to turn ON/OFF the LED of the other device by
# pressing the user button.
def main(argv):

    # Global variabbles.
    global switch_device_1, switch_device_2
    global switch_device_1_feature, switch_device_2_feature
    global switch_device_1_status, switch_device_2_status

    # Initial state.
    switch_device_1_status = SwitchStatus.OFF
    switch_device_2_status = SwitchStatus.OFF

    # Printing intro.
    print_intro()

    try:
        # Creating Bluetooth Manager.
        manager = Manager.instance()
        manager_listener = MyManagerListener()
        manager.add_listener(manager_listener)

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
        devices = []
        for discovered in discovered_devices:
            if discovered.get_tag() == SWITCH_DEVICE_1_MAC:
                switch_device_1 = discovered
                devices.append(switch_device_1)
            elif discovered.get_tag() == SWITCH_DEVICE_2_MAC:
                switch_device_2 = discovered
                devices.append(switch_device_2)
            if len(devices) == 2:
                break
        if len(devices) < 2:
            print('\nBluetooth setup incomplete. Exiting...\n')
            sys.exit(0)

        # Connecting to the devices.
        for device in devices:
            device.add_listener(MyNodeListener())
            print('Connecting to %s...' % (device.get_name()))
            device.connect()
            print('Connection done.')

        # Getting features.
        print('\nGetting features...')
        switch_device_1_feature = switch_device_1.get_feature(feature_switch.FeatureSwitch)
        switch_device_2_feature = switch_device_2.get_feature(feature_switch.FeatureSwitch)

        # Resetting switches.
        print('Resetting switches...')
        switch_device_1_feature.write_switch_status(switch_device_1_status.value)
        switch_device_2_feature.write_switch_status(switch_device_2_status.value)

        # Handling sensing and actuation of switch devices.
        switch_device_1_feature.add_listener(MyFeatureSwitchDevice1Listener())
        switch_device_2_feature.add_listener(MyFeatureSwitchDevice2Listener())

        # Enabling notifications.
        print('Enabling Bluetooth notifications...')
        switch_device_1.enable_notifications(switch_device_1_feature)
        switch_device_2.enable_notifications(switch_device_2_feature)

        # Bluetooth setup complete.
        print('\nBluetooth setup complete.')

        # Demo running.
        print('\nDemo running...\n')

        # Infinite loop.
        while True:

            # Getting notifications.
            if switch_device_1.wait_for_notifications(0.05) or switch_device_2.wait_for_notifications(0.05):
                continue

    except InvalidOperationException as e:
        print(e)
    except BTLEException as e:
        print(e)
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

    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
