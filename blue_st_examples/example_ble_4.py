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
# device exporting audio features, and to use it.


# IMPORT

from __future__ import print_function
import sys
import os
import time
import datetime
import click
from abc import abstractmethod
from threading import Thread
from bluepy.btle import BTLEException

from blue_st_sdk.manager import Manager
from blue_st_sdk.manager import ManagerListener
from blue_st_sdk.node import NodeListener
from blue_st_sdk.feature import FeatureListener
from blue_st_sdk.features.feature_audio_adpcm import FeatureAudioADPCM
from blue_st_sdk.features.feature_audio_adpcm_sync import FeatureAudioADPCMSync
from blue_st_sdk.utils.number_conversion import LittleEndian

###Audio Stream#########################################################
import alsaaudio
###Audio Stream#########################################################


# PRECONDITIONS
#
# In case you want to modify the SDK, clone the repository and add the location
# of the "BlueSTSDK_Python" folder to the "PYTHONPATH" environment variable.
#
# On Linux:
#   export PYTHONPATH=/home/<user>/BlueSTSDK_Python
#
# Moreover, install the following packages:
#   libasound:
#     sudo apt-get install libasound2-dev
#   pyalsaaudio:  
#     sudo pip install pyalsaaudio
# 
# Troubleshooting
#   Prevent audio out garbling caused by the audio out peripheral:
#      sudo bash -c "echo disable_audio_dither=1 >> /boot/config.txt"
#      sudo bash -c "echo pwm_mode=2 >> /boot/config.txt" 


# CONSTANTS

INTRO = """##################
# BlueST Example #
##################"""

# Paths and File names
AUDIO_DUMPS_PATH = "/home/pi/audioDumps/"
AUDIO_DUMP_SUFFIX = "_audioDump.raw"

# Notifications per second.
NPS = 200

# Number of channels.
CHANNELS = 1

# Sampling frequency.
SAMPLING_FREQ = 8000

# Global Audio Raw file.
audioFile=None
saveAudioFlag = 0

# Bluetooth Scanning time in seconds.
SCANNING_TIME_s = 5

# Global stream control index.
nIdx = 0

# Global audio features.
audioFeature = None
audioSyncFeature = None


# FUNCTIONS

# Printing intro
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
        global nIdx
        ###Audio Stream#################################################
        global stream
        ###Audio Stream#################################################
        ###Save Audio File##############################################
        global audioFile
        global saveAudioFlag
        ###Save Audio File##############################################
        shortData = sample._data
        if len(shortData) != 0:
            for d in shortData:
                byteData = LittleEndian.int16_to_bytes(d)
                ###Save Audio File######################################
                if saveAudioFlag == 'y' or saveAudioFlag == 'Y':
                    audioFile.write(byteData)
                ###Save Audio File######################################
                ###Audio Stream#########################################
                stream.write(byteData)
                ###Audio Stream#########################################
            nIdx += 1


#
# Implementation of the interface used by the Feature class to notify that a
# feature has updated its data.
#
class MyFeatureListenerSync(FeatureListener):

    #
    # To be called whenever the feature updates its data.
    #
    # @param feature Feature that has updated.
    # @param sample  Data extracted from the feature.
    #
    def on_update(self, feature, sample):
        global audioFeature
        if audioFeature is not None:
            audioFeature.set_audio_sync_parameters(sample)
                

# MAIN APPLICATION

# This application example connects to a Bluetooth Low Energy device, retrieves
# its exported features, and let the user get data from those supporting
# notifications.
def main(argv):
    
    global nIdx
 
    ###Audio Stream#####################################################
    global stream
    ###Audio Stream#####################################################
    ###Save Audio File##################################################
    global audioFile
    global saveAudioFlag
    ###Save Audio File##################################################
    
    global audioFeature
    global audioSyncFeature
    
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
            devices = manager.get_nodes()

            # Listing discovered devices.
            if not devices:
                print('\nNo Bluetooth devices found.')
                sys.exit(0)
            print('\nAvailable Bluetooth devices:')
            i = 1
            for device in devices:
                print('%d) %s: [%s]' % (i, device.get_name(), device.get_tag()))
                i += 1

            # Selecting a device.
            while True:
                choice = int(input("\nSelect a device (\'0\' to quit): "))
                if choice >= 0 and choice <= len(devices):
                    break
            if choice == 0:
                # Exiting.
                manager.remove_listener(manager_listener)
                print()
                sys.exit(0)
            device = devices[choice - 1]
            
            hasAudioFeats = [False,False]
            
            i = 1
            features = device.get_features()
            for feature in features:
                if feature.get_name() == FeatureAudioADPCM.FEATURE_NAME:
                    audioFeature = feature
                    hasAudioFeats[0]=True
                elif feature.get_name() == FeatureAudioADPCMSync.FEATURE_NAME:
                    audioSyncFeature = feature
                    hasAudioFeats[1]=True
                i += 1
            
            if all(hasAudioFeats):
                # Connecting to the device.
                node_listener = MyNodeListener()
                device.add_listener(node_listener)
                print('\nConnecting to %s...' % (device.get_name()))
                device.connect()
                print('Connection done.')
                
                while True:
                    
                    saveAudioFlag = raw_input('\nDo you want to save the audio stream?'
                                               '\'y\' - Yes, \'n\' - No (\'0\' to quit): ')
                    
                    if saveAudioFlag == 'y' or saveAudioFlag == 'Y' or saveAudioFlag == 'n' or saveAudioFlag == 'N':
                        if saveAudioFlag == 'y' or saveAudioFlag == 'Y':
                            ts = time.time()
                            st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')
                            if not os.path.exists(AUDIO_DUMPS_PATH):
                                os.makedirs(AUDIO_DUMPS_PATH)
                            fileName = AUDIO_DUMPS_PATH + st + AUDIO_DUMP_SUFFIX
                            audioFile = open(fileName,"w+")
                        
                        nOfSeconds = int(input('\nHow many seconds do you want to stream?'
                                                   ' Value must be > 0 (\'0\' to quit): '))
                        
                        nOfNotifications = nOfSeconds * NPS             

                        if nOfSeconds > 0:                        
                            print("Streaming Started")
                            
                            ###Audio Stream#####################################
                            stream = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NONBLOCK,'default')
                            stream.setformat(alsaaudio.PCM_FORMAT_S16_LE)
                            stream.setchannels(CHANNELS)
                            stream.setrate(SAMPLING_FREQ)
                            ###Audio Stream#####################################
                            
                            #Enabling Notifications
                            audioFeature_listener = MyFeatureListener()
                            audioFeature.add_listener(audioFeature_listener)
                            device.enable_notifications(audioFeature)
                            audioSyncFeature_listener = MyFeatureListenerSync()
                            audioSyncFeature.add_listener(audioSyncFeature_listener)
                            device.enable_notifications(audioSyncFeature)
                            
                            nIdx = 0
                            while nIdx < nOfNotifications:
                                device.wait_for_notifications(0.05)
                                    
                            print("End of Streaming")
                            # Disabling notifications.
                            device.disable_notifications(audioFeature)
                            audioFeature.remove_listener(audioFeature_listener)
                            device.disable_notifications(audioSyncFeature)
                            audioSyncFeature.remove_listener(audioSyncFeature_listener)
                            ###Save Audio File##################################
                            if saveAudioFlag == 'y' or saveAudioFlag == 'Y':
                                audioFile.close()
                            ###Save Audio File##################################
                            ###Audio Stream#####################################
                            stream.close()
                            ###Audio Stream#####################################
                        elif nOfSeconds == 0:
                            # Disabling notifications.
                            if audioFeature.is_notifying():
                                device.disable_notifications(audioFeature)
                                audioFeature.remove_listener(audioFeature_listener)
                            if audioSyncFeature.is_notifying():
                                device.disable_notifications(audioSyncFeature)
                                audioSyncFeature.remove_listener(audioSyncFeature_listener)
                            ###Save Audio File##################################
                            if saveAudioFlag == 'y' or saveAudioFlag == 'Y':
                                audioFile.close()
                            ###Save Audio File##################################
                            # Disconnecting from the device.
                            print('\nDisconnecting from %s...' % (device.get_name()))
                            device.disconnect()
                            print('Disconnection done.')
                            device.remove_listener(node_listener)
                            # Reset discovery.
                            manager.reset_discovery()
                            # Going back to the list of devices.
                            break
                    elif saveAudioFlag == '0':
                        # Disconnecting from the device.
                        print('\nDisconnecting from %s...' % (device.get_name()))
                        device.disconnect()
                        print('Disconnection done.')
                        device.remove_listener(node_listener)
                        # Reset discovery.
                        manager.reset_discovery()
                        # Going back to the list of devices.
                        break
            else:
                print("No Audio Features are Exposed from your BLE Node!")
                while True:
                    restartDiscovery = int(input('\nPress \'1\' to restart scanning for BLE devices '
                                           '(\'0\' to quit): '))
                    if restartDiscovery == 1:
                        # Reset discovery.
                        manager.reset_discovery()
                        break;
                    elif restartDiscovery == 0:
                        # Exiting.
                        print('\nExiting...\n')
                        sys.exit(0)
                        
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
