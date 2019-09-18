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
# This application example shows how to connect to a Bluetooth Low Energy (BLE)
# device that exports "Debug" service and features, and supports the "GetAIAlgos"
# and "SetAIAlgo" BLE commands capability.
#
# Please set the "IOT_DEVICE_NAME" variable section properly to fit your setup.


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
from blue_st_sdk.ai_algos.ai_algos import AIAlgos, AIAlgosDebugConsoleListener
from blue_st_sdk.utils.message_listener import MessageListener

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
IOT_DEVICE_NAME = 'NAI_300' #BLE Nucleo Stack FP-Sensing withh AIAlgo


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
        print("on_update::")
        print(feature)


#
# Implementation of the interface used by the MessageListener class to notify
# message rcv and send completion.
#
class MyMessageListener(MessageListener):
    
    def on_message_send_complete(self, debug_console, msg, bytes_sent):
        global AIAlgo_msg_completed, AI_msg        
        AI_msg = msg
        AIAlgo_msg_completed = True
        print(msg)
    
    def on_message_send_error(self, debug_console, msg, error):
        print("msg send error!")

    def on_message_rcv_complete(self, debug_console, msg, bytes_sent):
        print("msg rcv complete!")
    
    def on_message_rcv_error(self, debug_console, msg, error):
        print("msg rcv error!")


#
# Main application.
#
def main(argv):
    global AIAlgo_msg_completed, AI_msg

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
            print('%d) Get/Set Algos' % (i))

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
                    if choice != 0:
                        # Sending messages through debug console
                        AI_console = AIAlgos.get_console(device)
                        AI_msg_listener = MyMessageListener()
                        AI_console.add_listener(AI_msg_listener)
                    
                        i = 1
                        actions = ["Get Algo", "Set Algo", "Start HAR Algo", "Start ASC Algo"]
                        for action in actions:
                            print('%d) %s' % (i, action))
                            i += 1
                        while True:
                            choice = int(input("\nSelect an action (\'0\' to cancel): "))
                            if choice >= 0 and choice <= len(actions):
                                break

                        if choice == 1:
                            AI_console.getAIAlgos()
                        elif choice == 2:
                            _har = None
                            __algo =int(input("\nSelect algo to run(\'1:asc\', \'2\':har: "))                            
                            if __algo == 2:
                                while True:
                                    _algo = int(input("\nSelect HAR algo (\'1:GMP\', \'2\':IGN, \'3\':IGN_WSDM): "))
                                    if _algo <= 0 and _algo > 3:
                                        continue
                                    elif _algo == 1:
                                        _har = "gmp"
                                    elif _algo == 2:
                                        _har = "ign"
                                    elif _algo == 3:
                                        _har = "ign_wsdm"        
                                    break
                            if __algo == 1:
                                _algo = 1
                                AI_console.setAIAlgo(_algo, _har, 'asc')
                            elif __algo ==2:
                                AI_console.setAIAlgo(_algo, _har, 'har')
                        elif choice==3:
                            while True:
                                _algo = int(input("\nSelect HAR algo (\'1:GMP\', \'2\':IGN, \'3\':IGN_WSDM): "))
                                if _algo <= 0 and _algo > 3:
                                    continue
                                elif _algo == 1:
                                    _har = "gmp"
                                elif _algo == 2:
                                    _har = "ign"
                                elif _algo == 3:
                                    _har = "ign_wsdm"        
                                break
                            feature = features[1]

                            # Enabling notifications.
                            feature_listener = MyFeatureListener()
                            feature.add_listener(feature_listener)
                            device.enable_notifications(feature)
                            AI_console.startHARAlgo(_har)
                        elif choice==4:
                            feature = features[0]

                            # Enabling notifications.
                            feature_listener = MyFeatureListener()
                            feature.add_listener(feature_listener)
                            device.enable_notifications(feature)
                            AI_console.startASCAlgo()
                        elif choice == 0:
                            break
                    
                        # Getting notifications about firmware upgrade process.
                        while True:
                            if device.wait_for_notifications(0.05):
                                continue
                            elif AIAlgo_msg_completed:
                                if choice == 1:
                                    print("Algos received:" + AI_msg)
                                    break
                                elif choice == 2:
                                    continue
                        
                        print("Finished example")
                        print('Exiting...')
                        sys.exit(0)
                except (OSError, ValueError) as e:
                    print(e)

                finally:
                    # Disconnecting from the device.
                    if 'AI_console' in locals():
                        AI_console.remove_listener(AI_msg_listener)
                    print('\nDisconnecting from %s...' % (device.get_name()))
                    device.disconnect()
                    print('Disconnection done.')
                    device.remove_listener(node_listener)
                    print('\nDevice is rebooting...\n')
                    time.sleep(1)

            else:
                print("Testing Features")
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

    AIAlgo_msg_completed = False
    main(sys.argv[1:])
