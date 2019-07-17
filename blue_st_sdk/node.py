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


"""node

The node module is responsible for managing a Bluetooth Low Energy (BLE) device/
node and allocating the needed resources.
"""


# IMPORT

from abc import ABCMeta
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
from datetime import datetime
from bluepy.btle import Peripheral
from bluepy.btle import DefaultDelegate
from bluepy.btle import BTLEException
from enum import Enum
import struct
import itertools
import time

import blue_st_sdk.manager
from blue_st_sdk.advertising_data.blue_st_advertising_data_parser import BlueSTAdvertisingDataParser
from blue_st_sdk.utils.ble_node_definitions import Debug
from blue_st_sdk.utils.ble_node_definitions import FeatureCharacteristic
from blue_st_sdk.utils.ble_node_definitions import TIMESTAMP_OFFSET_BYTES
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidAdvertisingDataException
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidOperationException
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidDataException
from blue_st_sdk.utils.uuid_to_feature_map import UUIDToFeatureMap
from blue_st_sdk.utils.number_conversion import LittleEndian
from blue_st_sdk.utils.unwrap_timestamp import UnwrapTimestamp
from blue_st_sdk.debug_console import DebugConsole
from blue_st_sdk.utils.python_utils import lock


# CLASSES

class Node(Peripheral, object):
    """Bluetooth Low Energy device class.

    This class allows exporting features using Bluetooth Low Energy (BLE)
    transmission.
    """

    _NOTIFICATION_ON = struct.pack("BB", 0x01, 0x00)
    """Notifications ON."""

    _NOTIFICATION_OFF = struct.pack("BB", 0x00, 0x00)
    """Notifications OFF."""

    _NUMBER_OF_THREADS = 5
    """Number of threads to be used to notify the listeners."""

    def __init__(self, scan_entry):
        """Constructor.

        Args:
            scan_entry (ScanEntry): BLE device. It contains device information
                and advertising data. Refer to
                `ScanEntry <https://ianharvey.github.io/bluepy-doc/scanentry.html>`_
                for more information.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidAdvertisingDataException`
            is raised if the advertising data is not well formed.
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if the operation requested is not supported.
        """
        # Creating an un-connected "Peripheral" object.
        # It is needed to call the "connect()" method on this object (passing a
        # device address) before it will be usable.
        try:
            with lock(self):
                Peripheral.__init__(self)
        except BTLEException as e:
            raise BlueSTInvalidOperationException('Bluetooth invalid operation.')

        self._friendly_name = None
        """Friendly name."""

        self._last_rssi_update = None
        """Last update to the Received Signal Strength Indication."""

        self._status = NodeStatus.INIT
        """Status."""

        self._thread_pool = ThreadPoolExecutor(Node._NUMBER_OF_THREADS)
        """Pool of thread used to notify the listeners."""

        self._listeners = []
        """List of listeners to the node changes.
        It is a thread safe list, so a listener can subscribe itself through a
        callback."""

        self._available_features = []
        """List of all the available features as claimed by the advertising data.
        (No duplicates.)"""

        self._mask_to_feature_dic = {}
        """Mask to feature dictionary: there is an entry for each one-bit-high
        32-bit mask."""

        """UUID to list of external features dictionary: there is an entry for
        each list of exported external features.
        Note: A UUID may export more than one feature.
        Note: BlueSTSDK_Android: mExternalCharFeatures."""
        self._external_uuid_to_features_dic = UUIDToFeatureMap()

        self._update_char_handle_to_features_dict = {}
        """Characteristic's handle to list of features dictionary: it tells
        which features to update when new data from a characteristic are
        received.
        Note: A UUID may export more than one feature.
        Note: The same feature may be added to different list of features in
              case more characteristics have the same corresponding bit set to
              high.
        Note: BlueSTSDK_Android: mCharFeatureMap."""

        self._char_handle_to_characteristic_dict = {}
        """Characteristic's handle to characteristic dictionary."""

        self._unwrap_timestamp = UnwrapTimestamp()
        """Unwrap timestamp reference."""

        #self._characteristic_write_queue = Queue()
        """Queue of write jobs."""

        # Debug console used to read/write debug messages from/to the Bluetooth
        # device. None if the device doesn't export the debug service.
        self._debug_console = None

        # Advertising data.
        try:
            self._device = scan_entry
            """BLE device.
            Python's "ScanEntry" object, equivalent to Android's "BluetoothDevice"
            object."""

            with lock(self):
                self._advertising_data = BlueSTAdvertisingDataParser.parse(
                    scan_entry.getScanData())
                """Advertising data."""

            self._rssi = scan_entry.rssi
            """Received Signal Strength Indication."""
        except BlueSTInvalidAdvertisingDataException as e:
            raise e
        except BTLEException as e:
            raise BlueSTInvalidOperationException('Bluetooth invalid operation.')

        # Updating node.
        self._update_rssi(self._rssi)
        self._update_node_status(NodeStatus.IDLE)

        # Building available features.
        self._build_available_features()

    def _build_feature_from_class(self, feature_class):
        """Get a feature object from the given class.

        Args:
            feature_class (class): Feature class to instantiate.
        
        Returns:
            :class:`blue_st_sdk.feature.Feature`: The feature object built if
            the feature class is valid, "None" otherwise.
        """
        return feature_class(self) if feature_class else None

    def _build_features(self, characteristic):
        """Build the exported features of a BLE characteristic.

        After building the features, add them to the dictionary of the features
        to be updated.

        Args:
            characteristic (Characteristic): The BLE characteristic. Refer to
                `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                for more information.
        """
        try:
            # Extracting the feature mask from the characteristic's UUID.
            feature_mask = FeatureCharacteristic.extract_feature_mask(
                characteristic.uuid)
            # Looking for the exported features in reverse order to get them in
            # the correct order in case of characteristic that exports multiple
            # features.
            features = []
            mask = 1 << 31
            for i in range(0, 32):
                if (feature_mask & mask) != 0:
                    if mask in self._mask_to_feature_dic:
                        feature = self._mask_to_feature_dic[mask]
                        if feature is not None:
                            feature.set_enable(True)
                            features.append(feature)
                mask = mask >> 1

            # If the features are valid, add an entry for the corresponding
            # characteristic.
            if features:
                with lock(self):
                    self._update_char_handle_to_features_dict[
                        characteristic.getHandle()] = features
        except BTLEException as e:
            self._node._unexpected_disconnect()

    def _build_features_known_uuid(self, characteristic, feature_classes):
        """Build the given features of a BLE characteristic.

        After building the features, add them to the dictionary of the features
        to be updated.

        Args:
            characteristic (Characteristic): The BLE characteristic. Refer to
                `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                for more information.
            feature_classes (list): The list of feature-classes to instantiate.
        """
        # Build the features.
        features = []
        for feature_class in feature_classes:
            feature = self._build_feature_from_class(feature_class)
            if feature is not None:
                feature.set_enable(True)
                features.append(feature)
                self._available_features.append(feature)

        # If the features are valid, add an entry for the corresponding
        # characteristic.
        try:
            if features:
                with lock(self):
                    self._update_char_handle_to_features_dict[
                        characteristic.getHandle()] = features
        except BTLEException as e:
            self._unexpected_disconnect()

    def _build_available_features(self):
        """Build available features as claimed by the advertising data.

        Build a list of possible features that this node can export by
        relying on the advertising data.
        """
        # Getting device identifier and feature mask from advertising data.
        device_id = self._advertising_data.get_device_id()
        feature_mask = self._advertising_data.get_feature_mask()

        # Getting the dictionary that maps feature-masks to feature-classes
        # related to the advertising data's device identifier.
        decoder = blue_st_sdk.manager.Manager.get_node_features(device_id)

        # Initializing list of available-features and mask-to-feature
        # dictionary.
        self._available_features = []
        self._mask_to_feature_dic = {}

        # Building features as claimed by the advertising data's feature-mask.
        mask = 1
        for i in range(0, 32):
            if feature_mask & mask != 0:
                feature_class = decoder.get(mask)
                if feature_class is not None:
                    feature = self._build_feature_from_class(feature_class)
                    if feature is not None:
                        self._available_features.append(feature)
                        self._mask_to_feature_dic[mask] = feature
                    else:
                        self._logger.warning('Impossible to build the feature \"'
                            + feature_class.get_simple_name() + '\".')
            mask = mask << 1

    def _set_features_characteristics(self):
        """For each feature stores a reference to its characteristic.

        It is useful to enable/disable notifications on the characteristic
        itself.

        By design, the characteristic that offers more features beyond the
        feature is selected.
        """
        for feature in self._available_features:
            features_size = 0
            for entry in self._update_char_handle_to_features_dict.items():
                char_handle = entry[0]
                features = entry[1]
                if feature in features:
                    if feature._characteristic is None:
                        feature._characteristic = \
                            self._char_handle_to_characteristic_dict[char_handle]
                        features_size = len(features)
                    else:
                        if len(features) > features_size:
                            feature._characteristic = \
                                self._char_handle_to_characteristic_dict[char_handle]
                            features_size = len(features)

    def _update_features(self, char_handle, data, notify_update=False):
        """Update the features related to a given characteristic.

        Args:
            char_handle (int): The characteristic's handle to look for.
            data (str): The data read from the given characteristic.
            notify_update (bool, optional): If True all the registered listeners
                are notified about the new data.

        Returns:
            bool: True if the characteristic has some features associated to it
            and they have been updated, False otherwise.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
                if the data array has not enough data to read.
        """
        # Getting the features corresponding to the given characteristic.
        features = self._get_corresponding_features(char_handle)
        if features is None:
            return False

        # Computing the timestamp.
        timestamp = self._unwrap_timestamp.unwrap(
            LittleEndian.bytes_to_uint16(data))

        # Updating the features.
        offset = TIMESTAMP_OFFSET_BYTES  # Timestamp sixe in bytes.
        try:
            for feature in features:
                offset += feature.update(timestamp, data, offset, notify_update)
        except BlueSTInvalidDataException as e:
            raise e
        return True

    def _get_corresponding_features(self, char_handle):
        """Get the features corresponding to the given characteristic.

        Args:
            char_handle (int): The characteristic's handle to look for.

        Returns:
            list: The list of features associated to the given characteristic,
            None if the characteristic does not exist.
        """
        if char_handle in self._update_char_handle_to_features_dict:
            return self._update_char_handle_to_features_dict[char_handle]
        return None

    def _update_node_status(self, new_status, unexpected=False):
        """Update the status of the node.

        Args:
            new_status (:class:`blue_st_sdk.node.NodeStatus`): New status.
            unexpected (bool, optional): True if the new status is unexpected,
                False otherwise.
        """
        old_status = self._status
        self._status = new_status
        for listener in self._listeners:
            # Calling user-defined callback.
            # self._thread_pool.submit(
            #     listener.on_status_change(
            #         self, new_status.value, old_status.value))
            if new_status == NodeStatus.CONNECTED:
                self._thread_pool.submit(
                    listener.on_connect(self))
            elif new_status == NodeStatus.IDLE:
                self._thread_pool.submit(
                    listener.on_disconnect(self, unexpected))

    def _update_rssi(self, rssi):
        """Update the RSSI value.

        Args:
            rssi (int): New RSSI value.
        """
        self._rssi = rssi
        self._last_rssi_update = datetime.now()
        #if self._status == NodeStatus.LOST:
        #    self._update_node_status(NodeStatus.IDLE)

    def _build_debug_console(self, debug_service):
        """Build a debug console used to read/write debug messages from/to the
        Bluetooth device.

        Args:
            debug_service (Service): The BLE service. Refer to
                `Service <https://ianharvey.github.io/bluepy-doc/service.html>`_
                for more information.

        Returns:
            :class:`blue_st_sdk.debug_console.DebugConsole`: A debug console
            used to read/write debug messages from/to the Bluetooth device.
            None if the device doesn't export the needed characteristics.
        """
        try:
            stdinout = None
            stderr = None
            with lock(self):
                characteristics = debug_service.getCharacteristics()
            for characteristic in characteristics:
                if str(characteristic.uuid) == \
                    str(Debug.DEBUG_STDINOUT_BLUESTSDK_SERVICE_UUID):
                    stdinout = characteristic
                elif str(characteristic.uuid) == \
                    str(Debug.DEBUG_STDERR_BLUESTSDK_SERVICE_UUID):
                    stderr = characteristic
                if stdinout and stderr:
                    return DebugConsole(self, stdinout, stderr)
            return None
        except BTLEException as e:
            self._unexpected_disconnect()

    def _unexpected_disconnect(self):
        """Handle an unexpected disconnection."""
        try:
            # Disconnecting.
            self._update_node_status(NodeStatus.UNREACHABLE)
            with lock(self):
                super(Node, self).disconnect()
            self._update_node_status(NodeStatus.IDLE, True)
        except BTLEException as e:
            pass

    def connect(self, user_defined_features=None):
        """Open a connection to the node.

        Please note that there is no supervision timeout API within the SDK,
        hence it is not possible to detect immediately an unexpected
        disconnection; it is detected and notified via listeners as soon as a
        read/write/notify operation is executed on the device (limitation
        intrinsic to the bluepy library).

        Args:
            user_defined_features (dict, optional): User-defined feature to be
                added.

        Returns:
            bool: True if the connection to the node has been successful, False
            otherwise.
        """
        try:
            if not self._status == NodeStatus.IDLE:
                return False

            # Creating a delegate object, which is called when asynchronous
            # events such as Bluetooth notifications occur.
            self.withDelegate(NodeDelegate(self))

            # Connecting.
            self._update_node_status(NodeStatus.CONNECTING)
            self.add_external_features(user_defined_features)
            with lock(self):
                super(Node, self).connect(self.get_tag(), self._device.addrType)

            # Getting services.
            with lock(self):
                services = self.getServices()
            if not services:
                self.disconnect()
                return False

            # Handling Debug, Config, and Feature characteristics.
            for service in services:
                if Debug.is_debug_service(str(service.uuid)):
                    # Handling Debug.
                    self._debug_console = self._build_debug_console(service)
                #elif Config.is_config_service(str(service.uuid)):
                    # Handling Config.
                #    pass
                #else:
                # Getting characteristics.
                with lock(self):
                    characteristics = service.getCharacteristics()
                for characteristic in characteristics:

                    # Storing characteristics' handle to characteristic mapping.
                    with lock(self):
                        self._char_handle_to_characteristic_dict[
                            characteristic.getHandle()] = characteristic

                    # Building characteristics' features.
                    if FeatureCharacteristic.is_base_feature_characteristic(
                        str(characteristic.uuid)):
                        self._build_features(characteristic)
                    elif FeatureCharacteristic.is_extended_feature_characteristic(
                        str(characteristic.uuid)):
                        self._build_features_known_uuid(
                            characteristic,
                            [FeatureCharacteristic.get_extended_feature_class(
                                characteristic.uuid)])
                    elif bool(self._external_uuid_to_features_dic) \
                        and characteristic.uuid in self._external_uuid_to_features_dic:
                        self._build_features_known_uuid(
                            characteristic,
                            [self._external_uuid_to_features_dic[
                            characteristic.uuid]])

            # For each feature store a reference to the characteristic offering the
            # feature, useful to enable/disable notifications on the characteristic
            # itself.
            self._set_features_characteristics()

            # Change node's status.
            self._update_node_status(NodeStatus.CONNECTED)

            return self._status == NodeStatus.CONNECTED
        except BTLEException as e:
            self._unexpected_disconnect()

    def disconnect(self):
        """Close the connection to the node.

        Returns:
            bool: True if the disconnection to the node has been successful,
            False otherwise.
        """
        try:
            if not self.is_connected():
                return False

            # Disconnecting.
            self._update_node_status(NodeStatus.DISCONNECTING)
            with lock(self):
                super(Node, self).disconnect()
            self._update_node_status(NodeStatus.IDLE)

            return self._status == NodeStatus.IDLE
        except BTLEException as e:
            self._unexpected_disconnect()

    def add_external_features(self, user_defined_features):
        """Add available features to an already discovered device.

        This method has effect only if called before connecting to the node.
        
        If a UUID is already known, it will be overwritten with the new list of
        available features.

        Otherwise, it is possible to add available features before performing
        the discovery process (see 
        :meth:`blue_st_sdk.manager.Manager.addFeaturesToNode()` method).

        Args:
            user_defined_features (dict): User-defined feature to be added.
        """

        # Example:
        # # Adding a 'FeatureHeartRate' feature to a Nucleo device and mapping
        # # it to the standard '00002a37-0000-1000-8000-00805f9b34fb' Heart Rate
        # # Measurement characteristic.
        # map = UUIDToFeatureMap()
        # map.put(uuid.UUID('00002a37-0000-1000-8000-00805f9b34fb'),
        #         feature_heart_rate.FeatureHeartRate)
        # node.add_external_features(map)
        # # Connecting to the node.
        # node.connect()

        if user_defined_features is not None:
            self._external_uuid_to_features_dic.put_all(user_defined_features)

    def get_tag(self):
        """Get the tag of the node.

        The tag is a unique identification, i.e. its MAC address.

        Returns:
            str: The MAC address of the node (hexadecimal string separated by
            colons).
        """
        try:
            return self._device.addr
        except BTLEException as e:
            self._unexpected_disconnect()

    def get_status(self):
        """Get the status of the node.

        Returns:
            :class:`blue_st_sdk.node.NodeStatus`: The status of the node.
        """
        return self._status

    def get_name(self):
        """Get the name of the node.

        Returns:
            str: The name of the node.
        """
        return self._advertising_data.get_name()

    def get_friendly_name(self):
        """Get a friendly name of the node.

        Returns:
            str: A friendly name of the node.
        """
        if self._friendly_name is None:
            tag = self.get_tag()
            if tag is not None and len(tag) > 0:
                tag_clean = tag.replace(":", "")
            self._friendly_name = self.get_name()\
                + " @"\
                + tag_clean.substring(
                    len(tag_clean) - min(6, tag_clean.length()),
                    len(tag_clean)
                )
        return self._friendly_name

    def get_type(self):
        """Get the type of the node.

        Returns:
            :class:`blue_st_sdk.node.NodeType`: The type of the node.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidAdvertisingDataException`
                if the device type is unknown.
        """
        return self._advertising_data.get_device_type()

    def get_type_id(self):
        """Get the type identifier of the node.

        Returns:
            int: The type identifier of the node.
        """
        return self._advertising_data.get_device_id()

    def get_protocol_version(self):
        """Get the device Protocol Version.
        
        Returns:
            int: The device Protocol Version.
        """
        return self._advertising_data.get_protocol_version()

    def get_features(self, feature_class=None):
        """Get the list of features.

        Get the list of available features in the advertising data, or the list
        of features of the specific type (class name) if given.

        Args:
            feature_class (class, optional): Type (class name) of the feature to
                search for.

        Returns:
            list: A list of features. An empty list if no features are found.
        """
        if feature_class is None:
            features = self._available_features
        else:
            features = []
            for feature in self._available_features:
                if isinstance(feature, feature_class):
                    features.append(feature)
        return features

    def get_feature(self, feature_class):
        """Get a feature of the given type (class name).

        Args:
            feature_class (class): Type (class name) of the feature to search
                for.

        Returns:
            The feature of the given type (class name) if exported by this node,
            "None" otherwise.
        """
        features = self.get_features(feature_class)
        if len(features) != 0:
            return features[0]
        return None

    def get_tx_power_level(self):
        """Get the node transmission power in mdb.

        Returns:
            int: The node transmission power in mdb.
        """
        return self._advertising_data.get_tx_power()

    def get_last_rssi(self):
        """Get the most recent value of RSSI.

        Returns:
            int: The last known RSSI value.
        """
        return self._rssi

    def get_last_rssi_update_date(self):
        """Get the time of the last RSSI update received.

        Returns:
            datetime: The time of the last RSSI update received. Refer to
            `datetime <https://docs.python.org/2/library/datetime.html>`_
            for more information.
        """
        return self._last_rssi_update

    def is_connected(self):
        """Check whether the node is connected.

        Returns:
            bool: True if the node is connected, False otherwise.
        """
        return self._status == NodeStatus.CONNECTED

    def is_sleeping(self):
        """Check whether the node is sleeping.

        Returns:
            bool: True if the node is sleeping, False otherwise.
        """
        return self._advertising_data.is_board_sleeping()

    def is_alive(self, rssi):
        """Check whether the node is alive.

        To be called whenever the :class:`blue_st_sdk.manager.Manager` class
        receives a new advertising data from this node.

        Args:
            rssi (int): The RSSI of the last advertising data.
        """
        self._update_rssi(rssi)

    def get_advertising_data(self):
        """Update advertising data.

        Returns:
            :class:`blue_st_sdk.advertising_data.blue_st_advertising_data.BlueSTAdvertisingData`:
            Formatted Blue ST Advertising Data object.
        """
        return self._advertising_data

    def update_advertising_data(self, advertising_data):
        """Update advertising data.

        Args:
            advertising_data (list): Advertising data. Refer to 'getScanData()'
                method of
                `ScanEntry <https://ianharvey.github.io/bluepy-doc/scanentry.html>`_
                class for more information.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidAdvertisingDataException`
            is raised if the advertising data is not well formed.
        """
        try:
            self._advertising_data = BlueSTAdvertisingDataParser.parse(
                advertising_data)
        except BlueSTInvalidAdvertisingDataException as e:
            raise e

    def equals(self, node):
        """Compare the current node with the given one.

        Returns:
            bool: True if the current node is equal to the given node, False
            otherwise.
        """
        return isinstance(node, Node)\
               and (node == self or self.get_tag() == node.get_tag())

    def characteristic_can_be_read(self, characteristic):
        """Check if a characteristics can be read.

        Args:
            characteristic (Characteristic): The BLE characteristic to check.
                Refer to
                `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                for more information.

        Returns:
            bool: True if the characteristic can be read, False otherwise.
        """
        try:
            if characteristic is not None:
                with lock(self):
                    return "READ" in characteristic.propertiesToString()
            return False
        except BTLEException as e:
            self._unexpected_disconnect()

    def characteristic_can_be_written(self, characteristic):
        """Check if a characteristics can be written.

        Args:
            characteristic (Characteristic): The BLE characteristic to check.
                Refer to
                `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                for more information.

        Returns:
            bool: True if the characteristic can be written, False otherwise.
        """
        try:
            if characteristic is not None:
                with lock(self):
                    return "WRITE" in characteristic.propertiesToString()
            return False
        except BTLEException as e:
            self._unexpected_disconnect()

    def characteristic_can_be_notified(self, characteristic):
        """Check if a characteristics can be notified.

        Args:
            characteristic (Characteristic): The BLE characteristic to check.
                Refer to
                `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                for more information.

        Returns:
            bool: True if the characteristic can be notified, False otherwise.
        """
        try:
            if characteristic is not None:
                with lock(self):
                    return "NOTIFY" in characteristic.propertiesToString()
            return False
        except BTLEException as e:
            self._unexpected_disconnect()

    def read_feature(self, feature):
        """Synchronous request to read a feature.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The feature to read.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
                if the data array has not enough data to read.
        """
        if not feature.is_enabled():
            raise BlueSTInvalidOperationException(
                ' The "' + feature.get_name() + '" feature is not enabled.')

        characteristic = feature.get_characteristic()
        if not self.characteristic_can_be_read(characteristic):
            raise BlueSTInvalidOperationException(
                ' The "' + feature.get_name() + '" feature is not readable.')

        # Reading data.
        try:
            with lock(self):
                char_handle = characteristic.getHandle()
                data = self.readCharacteristic(char_handle)

            # Calling on-read callback.
            if self._debug_console and \
                Debug.is_debug_characteristic(str(characteristic.uuid)):
                # Calling on-read callback for a debug characteristic.
                self._debug_console.on_update_characteristic(
                    characteristic, data)
            else:
                # Calling on-read callback for the other characteristics.
                self._update_features(char_handle, data, False)
        except BlueSTInvalidDataException as e:
            raise e
        except BTLEException as e:
            self._unexpected_disconnect()

    def write_feature(self, feature, data):
        """Synchronous request to write a feature.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The feature to
                write.
            data (str): The data to be written.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        if not feature.is_enabled():
            raise BlueSTInvalidOperationException(
                ' The "' + feature.get_name() + '" feature is not enabled.')

        characteristic = feature.get_characteristic()
        if not self.characteristic_can_be_written(characteristic):
            raise BlueSTInvalidOperationException(
                ' The "' + feature.get_name() + '" feature is not writeable.')

        try:
            with lock(self):
                char_handle = characteristic.getHandle()
                self.writeCharacteristic(char_handle, data, True)
        except BTLEException as e:
            self._unexpected_disconnect()

    def set_notification_status(self, characteristic, status):
        """Ask the node to set the notification status of the given
        characteristic.

        Args:
            characteristic (Characteristic): The BLE characteristic to check.
                Refer to
                `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                for more information.
            status (bool): True if the notifications have to be turned on, False
                otherwise.
        """
        try:
            with lock(self):
                self.writeCharacteristic(characteristic.getHandle() + 1,
                    self._NOTIFICATION_ON if status else self._NOTIFICATION_OFF, True)
        except BTLEException as e:
            self._unexpected_disconnect()

    def enable_notifications(self, feature):
        """Ask the node to notify when a feature updates its value.

        The received values are notified thought a feature listener.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The given feature.

        Returns:
            bool: False if the feature is not handled by this node, or it is
            disabled, or it is not possible to turn notifications on for it,
            True otherwise.
        """
        if not feature.is_enabled() or feature.get_parent_node() != self:
            return False
        characteristic = feature.get_characteristic()
        if self.characteristic_can_be_notified(characteristic):
            feature.set_notify(True)
            self.set_notification_status(characteristic, True)
            return True
        return False

    def disable_notifications(self, feature):
        """Ask the node to stop notifying when a feature updates its value.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The given feature.

        Returns:
            bool: False if the feature is not handled by this node, or it is
            disabled, or it is not possible to turn notifications off for it,
            True otherwise.
        """
        if not feature.is_enabled() or feature.get_parent_node() != self:
            return False
        characteristic = feature.get_characteristic()
        if self.characteristic_can_be_notified(characteristic):
            feature.set_notify(False)
            if not self.characteristic_has_other_notifying_features(
                    characteristic, feature):
                self.set_notification_status(characteristic, False)
            return True
        return False

    def notifications_enabled(self, feature):
        """Check whether notifications are enabled for a feature.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The given feature.

        Returns:
            bool: True if notifications are enabled, False otherwise.
        """
        return feature.is_notifying()

    def wait_for_notifications(self, timeout_s):
        """Block until a notification is received from the peripheral, or until
        the given timeout has elapsed.

        If a notification is received, the
        :meth:`blue_st_sdk.feature.FeatureListener.on_update` method of any
        added listener is called.

        Args:
            timeout_s (float): Time in seconds to wait before returning.

        Returns:
            bool: True if a notification is received before the timeout elapses,
            False otherwise.
        """
        try:
            if self.is_connected():
                with lock(self):
                    return self.waitForNotifications(timeout_s)
            return False
        except BTLEException as e:
            self._unexpected_disconnect()

    def characteristic_has_other_notifying_features(self, characteristic, feature):
        """Check whether a characteristic has other enabled features beyond the
        given one.

        Args:
            characteristic (Characteristic): The BLE characteristic to check.
                Refer to
                `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                for more information.
            feature (:class:`blue_st_sdk.feature.Feature`): The given feature.

        Returns:
            True if the characteristic has other enabled features beyond the
            given one, False otherwise.
        """
        with lock(self):
            features = self._get_corresponding_features(
                characteristic.getHandle())
        for feature_entry in features:
            if feature_entry == feature:
                pass
            elif feature_entry.is_notifying():
                return True
        return False

    def add_listener(self, listener):
        """Add a listener.
        
        Args:
            listener (:class:`blue_st_sdk.node.NodeListener`): Listener to
                be added.
        """
        if listener is not None:
            with lock(self):
                if not listener in self._listeners:
                    self._listeners.append(listener)

    def remove_listener(self, listener):
        """Remove a listener.

        Args:
            listener (:class:`blue_st_sdk.node.NodeListener`): Listener to
                be removed.
        """
        if listener is not None:
            with lock(self):
                if listener in self._listeners:
                    self._listeners.remove(listener)

    def get_debug(self):
        """Getting a debug console used to read/write debug messages from/to the
        Bluetooth device.

        Returns:
            :class:`blue_st_sdk.debug_console.DebugConsole`: A debug console
            used to read/write debug messages from/to the Bluetooth device.
            None if the device doesn't export the debug service.
        """
        return self._debug_console


class NodeDelegate(DefaultDelegate):
    """Delegate class for handling Bluetooth Low Energy devices' notifications."""

    def __init__(self, node):
        """Constructor.

        Args:
            node (:class:`blue_st_sdk.node.Node`): The node which sends
                notifications.
        """
        DefaultDelegate.__init__(self)

        self._node = node
        self._logger = logging.getLogger('BlueSTSDK')

    def handleNotification(self, char_handle, data):
        """It is called whenever a notification arises.

        Args:
            char_handle (int): The characteristic's handle to look for.
            data (str): The data notified from the given characteristic.
        """
        try:
            # Calling on-read callback.
            if self._node._debug_console:
                # Calling on-update callback for a debug characteristic.
                characteristic = \
                    self._node._char_handle_to_characteristic_dict[char_handle]
                if Debug.is_debug_characteristic(str(characteristic.uuid)):
                    self._node._debug_console.on_update_characteristic(
                        characteristic, data)
                    return

            # Calling on-read callback for the other characteristics.
            self._node._update_features(char_handle, data, True)
        except BlueSTInvalidDataException as e:
            self._logger.warning(str(e))
        except BTLEException as e:
            self._unexpected_disconnect()


class NodeType(Enum):
    """Type of node."""

    GENERIC = 0x00
    """Unknown device type."""

    STEVAL_WESU1 = 0x01
    """STEVAL-WESU1."""

    SENSOR_TILE = 0x02
    """SensorTile."""

    BLUE_COIN = 0x03
    """BlueCoin."""

    STEVAL_IDB008VX = 0x04
    """BlueNRG1 / BlueNRG2 STEVAL."""

    STEVAL_BCN002V1 = 0x05
    """BlueNRG-Tile STEVAL."""
    
    SENSOR_TILE_BOX = 0x06
    """SensorTile.box."""

    DISCOVERY_IOT01A = 0x07
    """B-L475E-IOT01A."""

    NUCLEO = 0x08
    """NUCLEO-based."""


class NodeStatus(Enum):
    """Status of the node."""

    INIT = 'INIT'
    """Dummy initial status."""

    IDLE = 'IDLE'
    """Waiting for a connection and sending advertising data."""

    CONNECTING = 'CONNECTING'
    """Opening a connection with the node."""

    CONNECTED = 'CONNECTED'
    """Connected to the node.
    This status can be fired 2 times while doing a secure connection using
    Bluetooth pairing."""

    DISCONNECTING = 'DISCONNECTING'
    """Closing the connection to the node."""

    LOST = 'LOST'
    """The advertising data has been received for some time, but not anymore."""

    UNREACHABLE = 'UNREACHABLE'
    """The node disappeared without first disconnecting."""

    DEAD = 'DEAD'
    """Dummy final status."""


# INTERFACES

class NodeListener(object):
    """Interface used by the :class:`blue_st_sdk.node.Node` class to notify
    changes of a node's status.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_status_change(self, node, new_status, old_status):
        """To be called whenever a node changes its status.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that has changed its
                status.
            new_status (:class:`blue_st_sdk.node.NodeStatus`): New status.
            old_status (:class:`blue_st_sdk.node.NodeStatus`): Old status.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "on_status_change()" to '
                                  'use the "NodeListener" class.')

    @abstractmethod
    def on_connect(self, node):
        """To be called whenever a node connects to a host.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that has connected to a
                host.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "on_connect()" to '
                                  'use the "NodeListener" class.')

    @abstractmethod
    def on_disconnect(self, node, unexpected=False):
        """To be called whenever a node disconnects from a host.

        Args:
            node (:class:`blue_st_sdk.node.Node`): Node that has disconnected
                from a host.
            unexpected (bool, optional): True if the disconnection is unexpected,
                False otherwise (called by the user).

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "on_disconnect()" to '
                                  'use the "NodeListener" class.')
