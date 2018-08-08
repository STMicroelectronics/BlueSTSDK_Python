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
from datetime import datetime
from bluepy.btle import Peripheral
from bluepy.btle import DefaultDelegate
from enum import Enum
import struct
import itertools
import logging

import blue_st_sdk.manager
from blue_st_sdk.python_utils import lock
from blue_st_sdk.utils.ble_node_definitions import FeatureCharacteristic
from blue_st_sdk.utils.ble_node_definitions import TIMESTAMP_OFFSET_BYTES
from blue_st_sdk.utils.ble_advertising_data_parser import BLEAdvertisingDataParser
from blue_st_sdk.utils.blue_st_exceptions import InvalidBLEAdvertisingDataException
from blue_st_sdk.utils.blue_st_exceptions import InvalidOperationException
from blue_st_sdk.utils.uuid_to_feature_map import UUIDToFeatureMap
from blue_st_sdk.utils.number_conversion import LittleEndian
from blue_st_sdk.utils.unwrap_timestamp import UnwrapTimestamp


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
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidBLEAdvertisingDataException`
                is raised if the advertising data is not well formed.
        """
        # Creating an un-connected "Peripheral" object.
        # It is needed to call the "connect()" method on this object (passing a
        # device address) before it will be usable.
        Peripheral.__init__(self)
        self.withDelegate(NodeDelegate(self))

        # Advertising data.
        try:
            self._advertising_data = BLEAdvertisingDataParser(
                scan_entry.getScanData())
        except InvalidBLEAdvertisingDataException as e:
            raise e

        # BLE device.
        # Python's "ScanEntry" object, equivalent to Android's "BluetoothDevice"
        # object.
        self._device = scan_entry

        # Friendly name.
        self._friendly_name = None

        # Received Signal Strength Indication.
        self._rssi = scan_entry.rssi

        # Last update to the Received Signal Strength Indication.
        self._last_rssi_update = None

        # Status.
        self._status = NodeStatus.INIT

        # Pool of thread used to notify the listeners.
        self._thread_pool = ThreadPoolExecutor(Node._NUMBER_OF_THREADS)

        # List of listeners to the node changes.
        # It is a thread safe list, so a listener can subscribe itself through a
        # callback.
        self._listeners = []

        # List of all the available features as claimed by the advertising data.
        # (No duplicates.)
        self._available_features = []

        # Mask to feature dictionary: there is an entry for each one-bit-high
        # 32-bit mask.
        self._mask_to_feature_dic = {}

        # UUID to list of external features dictionary: there is an entry for
        # each list of exported external features.
        # Note: A UUID may export more than one feature.
        # BlueSTSDK_Android: mExternalCharFeatures
        self._external_uuid_to_features_dic = UUIDToFeatureMap()

        # Characteristic's handle to list of features dictionary: it tells which
        # features to update when new data from a characteristic are received.
        # Note: A UUID may export more than one feature.
        # Note: The same feature may be added to different list of features in
        #       case more characteristics have the same corresponding bit set to
        #       high.
        # BlueSTSDK_Android: mCharFeatureMap
        self._update_char_handle_to_features_dict = {}

        # Characteristic's handle to characteristic dictionary.
        self._char_handle_to_characteristic_dict = {}

        # Unwrap timestamp reference.
        self._unwrap_timestamp = UnwrapTimestamp()

        # Updating node.
        self._update_rssi(self._rssi)
        self._update_node_status(NodeStatus.IDLE)

        # Building available features.
        self._build_available_features()

    def connect(self, user_defined_features=None):
        """Open a connection to the node.

        Args:
            user_defined_features (dict, optional): User-defined feature to be
                added.
        """
        self._update_node_status(NodeStatus.CONNECTING)
        self.add_external_features(user_defined_features)
        super(Node, self).connect(self.get_tag(), self._device.addrType)

        # Getting services.
        services = self.getServices()
        if not services:
            self._update_node_status(NodeStatus.DEAD)
            return

        # Handling Debug, Config, and Feature characteristics.
        for service in services:
            # TBD
            # if service.uuid == Debug.DEBUG_BLUESTSDK_SENSOR_SERVICE_UUID:
                # Handling Debug.
            #    pass
            # elif service.uuid == Config.CONFIG_BLUESTSDK_SENSOR_SERVICE_UUID:
                # Handling Config.
            #    pass
            # else:
            # Getting characteristics.
            characteristics = service.getCharacteristics()
            for characteristic in characteristics:

                # Storing characteristics' handle to characteristic mapping.
                self._char_handle_to_characteristic_dict[
                    characteristic.getHandle()] = characteristic

                # Building characteristics' features.
                if FeatureCharacteristic.is_feature_characteristic(
                    characteristic.uuid):
                    self._build_features(characteristic)
                elif bool(self._external_uuid_to_features_dic) \
                    and characteristic.uuid in self._external_uuid_to_features_dic:
                    self._build_features_known_uuid(
                        characteristic,
                        self._external_uuid_to_features_dic[characteristic.uuid])

        # For each feature store a reference to the characteristic offering the
        # feature, useful to enable/disable notifications on the characteristic
        # itself.
        self._set_features_characteristics()

        # Change node's status.
        self._update_node_status(NodeStatus.CONNECTED)

    def disconnect(self):
        """Close the connection to the node."""
        if not self.is_connected():
            return
        self._update_node_status(NodeStatus.DISCONNECTING)
        super(Node, self).disconnect()
        self._update_node_status(NodeStatus.IDLE)

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

    def _build_feature_from_class(self, feature_class):
        """Get a feature object from the given class.

        Args:
            feature_class (class): Feature class to instantiate.
        
        Returns:
            :class:`blue_st_sdk.feature.Feature`: The feature object built.
        """
        return feature_class(self)

    def _build_features(self, characteristic):
        """Build the exported features of a BLE characteristic.

        After building the features, add them to the dictionary of the features
        to be updated.

        Args:
            characteristic (Characteristic): The BLE characteristic. Refer to
                `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                for more information.
        """
        # Extracting the feature mask from the characteristic's UUID.
        feature_mask = FeatureCharacteristic.extract_feature_mask(
            characteristic.uuid)
        # Looking for the exported features in reverse order to get them in the
        # correct order in case of characteristic that exports multiple
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
            self._update_char_handle_to_features_dict[
                characteristic.getHandle()] = features

    def _build_features_known_uuid(self, characteristic, features_class):
        """Build the given features of a BLE characteristic.

        After building the features, add them to the dictionary of the features
        to be updated.

        Args:
            characteristic (Characteristic): The BLE characteristic. Refer to
                `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
                for more information.
            features_class (list): The list of features-classes to instantiate.
        """
        # Build the features.
        features = []
        for feature_class in features_class:
            feature = self._build_feature_from_class(feature_class)
            if feature is not None:
                feature.set_enable(True)
                features.append(feature)
                self._available_features.append(feature)

        # If the features are valid, add an entry for the corresponding
        # characteristic.
        if features:
            self._update_char_handle_to_features_dict[
                characteristic.getHandle()] = features

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
                        logging.error('Impossible to build the feature \"'
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
        """
        # Getting the features corresponding to the given characteristic.
        features = self._get_corresponding_features(char_handle)
        if features is None:
            return False

        # Computing the timestamp.
        timestamp = self._unwrap_timestamp.unwrap(
            LittleEndian.bytesToUInt16(data))

        # Updating the features.
        offset = TIMESTAMP_OFFSET_BYTES  # Timestamp's bytes.
        for feature in features:
            offset += feature.update(timestamp, data, offset, notify_update)
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

    def get_tag(self):
        """Get the tag of the node.

        The tag is a unique identification, i.e. its MAC address.

        Returns:
            str: The MAC address of the node (hexadecimal string separated by
            colons).
        """
        return self._device.addr

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
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidBLEAdvertisingDataException`
                if the board type is unknown.
        """
        return self._advertising_data.get_board_type()

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
            None otherwise.
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

    def _update_rssi(self, rssi):
        """Update the RSSI value.

        Args:
            rssi (int): New RSSI value.
        """
        self._rssi = rssi
        self._last_rssi_update = datetime.now()
        if self._status == NodeStatus.LOST:
            self._update_node_status(NodeStatus.IDLE)

    def get_last_rssi_update_date(self):
        """Get the time of the last RSSI update received.

        Returns:
            datetime: The time of the last RSSI update received. Refer to
            `datetime <https://docs.python.org/2/library/datetime.html>`_
            for more information.
        """
        return self._last_rssi_update

    def _update_node_status(self, new_status):
        """Update the status of the node.

        Args:
            new_status (:class:`blue_st_sdk.node.NodeStatus`): New status.
        """
        old_status = self._status
        self._status = new_status
        for listener in self._listeners:
            # Calling user-defined callback.
            self._thread_pool.submit(
                listener.on_status_change(
                    self, new_status.value, old_status.value))

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
        return self._advertising_data.get_board_sleeping()

    def is_alive(self, rssi):
        """Check whether the node is alive.

        To be called whenever the :class:`blue_st_sdk.manager.Manager` class
        receives a new advertising data from this node.

        Args:
            rssi (int): The RSSI of the last advertising data.
        """
        self._update_rssi(rssi)

    def update_advertising_data(self, advertising_data):
        """Update advertising data.

        Args:
            advertising_data (list): Advertising data. Refer to 'getScanData()'
                method of
                `ScanEntry <https://ianharvey.github.io/bluepy-doc/scanentry.html>`_
                class for more information.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidBLEAdvertisingDataException`
                is raised if the advertising data is not well formed.
        """
        try:
            self._advertising_data = BLEAdvertisingDataParser(advertising_data)
        except InvalidBLEAdvertisingDataException as e:
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
        if characteristic is not None:
            return "READ" in characteristic.propertiesToString()
        return False

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
        if characteristic is not None:
            return "WRITE" in characteristic.propertiesToString()
        return False

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
        if characteristic is not None:
            return "NOTIFY" in characteristic.propertiesToString()
        return False

    def read_feature(self, feature):
        """Synchronous request to read a feature.

        The read value is returned.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The feature to read.

        Returns:
            str: The raw data read.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        if not feature.is_enabled():
            raise InvalidOperationException(
                ' The "' + feature.get_name() + '" feature is not enabled.')

        characteristic = feature.get_characteristic()
        if not self.characteristic_can_be_read(characteristic):
            raise InvalidOperationException(
                ' The "' + feature.get_name() + '" cannot be read.')

        char_handle = characteristic.getHandle()
        data = self.readCharacteristic(char_handle)
        self._update_features(char_handle, data, False)

        return data

    def write_feature(self, feature, data):
        """Synchronous request to write a feature.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The feature to
                write.
            data (str): The data to be written.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        if not feature.is_enabled():
            raise InvalidOperationException(
                ' The "' + feature.get_name() + '" feature is not enabled.')

        characteristic = feature.get_characteristic()
        if not self.characteristic_can_be_written(characteristic):
            raise InvalidOperationException(
                ' The "' + feature.get_name() + '" cannot be written.')

        char_handle = characteristic.getHandle()
        self.writeCharacteristic(char_handle, data, True)

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
            self.writeCharacteristic(characteristic.getHandle() + 1,
                self._NOTIFICATION_ON, True)
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
                self.writeCharacteristic(characteristic.getHandle() + 1,
                    self._NOTIFICATION_OFF, True)
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
        """Blocks until a notification is received from the peripheral, or until
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
        return self.waitForNotifications(timeout_s)

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
        features = self._get_corresponding_features(characteristic.getHandle())
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

    def handleNotification(self, char_handle, data):
        """It is called whenever a notification arises.

        Args:
            char_handle (int): The characteristic's handle to look for.
            data (str): The data notiffied from the given characteristic.

        """
        self._node._update_features(char_handle, data, True)


class NodeType(Enum):
    """Type of node."""

    # Unknown board type.
    GENERIC = 0x00

    # STEVAL-WESU1 board.
    STEVAL_WESU1 = 0x01

    # SensorTile board.
    SENSOR_TILE = 0x02

    # BlueCoin board.
    BLUE_COIN = 0x03

    # BlueNRG1 / BlueNRG2 STEVAL board.
    STEVAL_IDB008VX = 0x04

    # NUCLEO-based board.
    NUCLEO = 0x05


class NodeStatus(Enum):
    """Status of the node."""

    # Dummy initial status.
    INIT = 'INIT'

    # Waiting for a connection and sending advertising data.
    IDLE = 'IDLE'

    # Opening a connection with the node.
    CONNECTING = 'CONNECTING'

    # Connected to the node.
    # This status can be fired 2 times while doing a secure connection using
    # Bluetooth pairing.
    CONNECTED = 'CONNECTED'

    # Closing the connection to the node.
    DISCONNECTING = 'DISCONNECTING'

    # The advertising data has been received for some time, but not anymore.
    LOST = 'LOST'

    # The node disappeared without first disconnecting.
    UNREACHABLE = 'UNREACHABLE'

    # Dummy final status.
    DEAD = 'DEAD'


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
            node (Node): Node that has changed its status.
            new_status (:class:`blue_st_sdk.node.NodeStatus`): New status.
            old_status (:class:`blue_st_sdk.node.NodeStatus`): Old status.

        Raises:
            'NotImplementedError' is raised if the method is not implemented.
        """
        raise NotImplementedError('You must define "on_status_change()" to use '
                                  'the "NodeListener" class.')
