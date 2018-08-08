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


"""feature

The feature module represents a feature exported by a Bluetooth Low Energy (BLE)
device.
"""


# IMPORT

from abc import ABCMeta
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from blue_st_sdk.python_utils import lock
from blue_st_sdk.utils.blue_st_exceptions import InvalidOperationException


# CLASSES

class Feature(object):
    """This class contains description and data exported by a node.

    Adding a new sensor in a node implies extending this class and implementing
    the :meth:`blue_st_sdk.feature.Feature.extract_data()` method to extract the
    information from the raw data coming from the node.

    This class manages notifications and listeners' subscriptions.
    """

    _NUMBER_OF_THREADS = 5
    """Number of threads to be used to notify the listeners."""

    def __init__(self, name, node, description):
        """Constructor.

        Args:
            name (str): Name of the feature.
            node (:class:`blue_st_sdk.node.Node`): Node that will update the
                feature.
            description (list): Description of the data of the feature (list of
                :class:`blue_st_sdk.features.field.Field` objects).
        """

        # Feature name.
        self._name = name

        # Node that will update the feature.
        self._parent = node

        # List of feature's fields.
        # Fields are described by name, unit, type, and minimum/maximum values.
        self._description = description

        # Tells whether the feature is enabled or not.
        self._is_enabled = False

        # Tells whether the feature's notifications are enabled or not
        self._notify = False

        # Pool of thread used to notify the listeners.
        self._thread_pool = ThreadPoolExecutor(Feature._NUMBER_OF_THREADS)

        # List of listeners to the feature changes.
        # It is a thread safe list, so a listener can subscribe itself through a
        # callback.
        self._listeners = []

        # List of listeners to log the received data.
        # It is a thread safe list, so a listener can subscribe itself through a
        # callback.
        self._loggers = []

        # Local time of the last update.
        self._last_update = None

        # Last data received from the node.
        self._last_sample = None

        # Reference to the characteristic that offers the feature.
        # Note: By design, it is the characteristic that offers more features
        #       beyond the current one, among those offering the current one.
        self._characteristic = None

    def add_listener(self, listener):
        """Add a listener.
        
        Args:
            listener (:class:`blue_st_sdk.feature.FeatureListener`): Listener to
                be added.
        """
        if listener is not None:
            with lock(self):
                if not listener in self._listeners:
                    self._listeners.append(listener)

    def remove_listener(self, listener):
        """Remove a listener.
        
        Args:
            listener (:class:`blue_st_sdk.feature.FeatureListener`): Listener to
                be removed.
        """
        if listener is not None:
            with lock(self):
                if listener in self._listeners:
                    self._listeners.remove(listener)

    def add_logger(self, logger):
        """Add a logger.
        
        Args:
            logger (:class:`blue_st_sdk.feature.FeatureLogger`): Logger to
                be added.
        """
        if logger is not None:
            with lock(self):
                if not logger in self._loggers:
                    self._loggers.append(logger)

    def remove_logger(self, logger):
        """Remove a logger.
        
        Args:
            logger (:class:`blue_st_sdk.feature.FeatureLogger`): Logger to
                be removed.
        """
        if logger is not None:
            with lock(self):
                if logger in self._loggers:
                    self._loggers.remove(logger)

    def get_last_update(self):
        """Get the time of the last update.

        Returns:
            datetime: The time of the last update received. Refer to
            `datetime <https://docs.python.org/2/library/datetime.html>`_
            for more information.
        """
        return self._last_update

    def get_name(self):
        """Get the feature name.

        Returns:
            str: The feature name.
        """
        return self._name

    def get_parent_node(self):
        """Get the node that updates the feature.

        Return:
            :class:`blue_st_sdk.node.Node`: The node that updates the feature.
        """
        return self._parent

    def get_characteristic(self):
        """Get the characteristic that offers the feature.

        Note:
            By design, it is the characteristic that offers more features beyond
            the current one, among those offering the current one.

        Returns:
            characteristic: The characteristic that offers the feature. Refer to
            `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
            for more information.
        """
        return self._characteristic

    def get_fields_description(self):
        """"Get the description of the data fields of the feature.

        Returns:
            list: The description of the data fields of the feature (list of
            :class:`blue_st_sdk.features.field.Field` objects).
        """
        return self._description

    def get_sample(self):
        """Return a sample containing the last timestamp and data received from
        the device.
        
        Returns:
            :class:`blue_st_sdk.feature.Sample`: The last sample received, None
            if missing.
        """
        if self._last_sample is not None:
            return Sample.from_sample(self._last_sample)
        return None

    def set_enable(self, flag):
        """Set the enable status of the feature.

        Args:
            flag (bool): New enable status: True to enable, False otherwise.
        """
        self._is_enabled = flag

    def is_enabled(self):
        """Checking whether the node exports the data of the feature.

        A node can export a feature in the advertising data without having the
        equivalent characteristic.

        Returns:
            bool: True if the node exports the data of the feature, False
            otherwise.
        """
        return self._is_enabled

    def set_notify(self, flag):
        """Set the notification status of the feature.

        Args:
            flag (bool): New notification status: True to enable, False
            otherwise.
        """
        self._notify = flag

    def is_notifying(self):
        """Checking whether the notifications for the feature are enabled.

        Returns:
            bool: True if the feature is notifying, False otherwise.
            """
        return self._notify

    def _notify_update(self, sample):
        """Notify each :class:`blue_st_sdk.feature.FeatureListener`that the
        feature has been updated.

        Each call runs in a different thread.

        Overwriting the method :meth:`blue_st_sdk.feature.Feature.update()`
        implies calling this method to notify the user about the new sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.
        """
        for listener in self._listeners:
            # Calling user-defined callback.
            self._thread_pool.submit(listener.on_update(self, sample))

    def _log_update(self, raw_data, sample):
        """Notify each :class:`blue_st_sdk.feature.FeatureLogger` that the
        feature has been updated.

        Each call runs in a different thread.

        Overwriting the method :meth:`blue_st_sdk.feature.Feature.update()`
        implies calling this method to log a feature's update.

        Args:
            raw_data: Raw data used to extract the feature field. It can be
                "None".
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data to log.
        """
        for logger in self._loggers:
            # Calling user-defined callback.
            self._thread_pool.submit(logger.log_update(self, raw_data, sample))

    def update(self, timestamp, data, offset, notify_update=False):
        """Update feature's internal data through an atomic operation, and
        notify the registered listeners about the update, if needed.

        This method has to be called by a node whenever it receives new data
        from the feature, not by the application.

        When overriding this method, please remember to update the timestamp and
        the last-updated value, and to acquire the write-lock.

        Args:
            timestamp (int): Package's timestamp.
            data (list): Feature's data.
            offset (int): Offset position to start reading data.
            notify_update (bool, optional): If True all the registered listeners
                are notified about the new data.

        Returns:
            int: The number of bytes read.
        """
        # Update the feature's internal data
        sample = None
        with lock(self):
            extracted_data = self.extract_data(timestamp, data, offset)
            sample = self._last_sample = extracted_data.get_sample()
            read_bytes = extracted_data.get_read_bytes()
            self._last_update = datetime.now()

        if notify_update:
            # Notify all the registered listeners about the new data.
            self._notify_update(sample)

        # Log the new data through all the registered loggers.
        self._log_update(data[offset:offset + read_bytes], sample)

        return read_bytes

    @classmethod
    def has_valid_index(self, sample, index):
        """Check whether the sample has valid data at the index position.
        
        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.
            index (int): Position to be tested.
        
        Returns:
            bool: True if the sample is not null and has a non null value at the
            index position, False otherwise.
        """
        return sample is not None \
            and len(sample._data) > index \
            and sample._data[index] is not None

    def read_data(self):
        """Read data from the feature.

        Returns:
            str: The raw data read.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        try:
            return self._parent.read_feature(self)
        except InvalidOperationException as e:
            raise e

    def write_data(self, data):
        """Write data to the feature.

        Args:
            data (str): Raw data to write.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.InvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        try:
            self._parent.write_feature(self, data)
        except InvalidOperationException as e:
            raise e

    @abstractmethod
    def extract_data(self, timestamp, data, offset):
        """Extract the data from the feature's raw data.
        
        You have to parse the data inside the "data" field and skip the first
        "offset" byte.

        This method has to extract the data, create a
        :class:`blue_st_sdk.feature.Sample` object, and return an
        :class:`blue_st_sdk.feature.ExtractedData` object containing it.

        The method that calls this one has to manage the lock
        acquisition/release and to notify the user about the new sample.

        Args:
            timestamp (int): Data's timestamp.
            data (str): The data read from the feature.
            offset (int): Offset where to start reading data.
        
        Returns:
            :class:`blue_st_sdk.feature.ExtractedData`: An object containing the
            number of bytes read and the extracted data.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
            :exc:`Exception` if the data array has not enough data to read.
        """
        raise NotImplementedError(
            'You must implement "extract_data()" to use the "Feature" class.')

    def __str__(self):
        """Get a string representing the last sample.

        Return:
            str: A string representing the last sample.
        """
        with lock(self):
            sample = self._last_sample

        if sample is None:
            return self._name + ': Unknown'
        if not sample._data:
            return self._name + ': Unknown'

        if len(sample._data) == 1:
            result = '%s(%d): %s %s' \
                % (self._name,
                   sample._timestamp,
                   str(sample._data[0]),
                   self._description[0]._unit)
            return result

        result = '%s(%d): ( ' % (self._name, sample._timestamp)
        i = 0
        while i < len(sample._data):
            result += '%s: %s %s%s' \
                % (self._description[i]._name,
                   str(sample._data[i]),
                   self._description[i]._unit,
                   '    ' if i < len(sample._data) - 1 else ' )')
            i += 1
        return result


class FeatureListener(object):
    """Interface used by the :class:`blue_st_sdk.feature.Feature` class to
    notify changes of a feature's data.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_update(self, feature, sample):
        """To be called whenever the feature updates its data.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): Feature that has
                updated.
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data extracted
                from the feature.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError(
            'You must implement "on_update()" to use the "FeatureListener" class.')

#
# Interface used to dump the feature's data, both in raw format (as received
# from the node) and after parsing it.
#
# @author STMicroelectronics - Central Labs.
# @version 1.0
#
class FeatureLogger(object):
    """Interface used by the :class:`blue_st_sdk.feature.Feature` class to
    log changes of a feature's data.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def log_update(self, feature, raw_data, sample):
        """To be called to log the updates of the feature.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): Feature that has
                updated.
            raw_data (str): Raw data used to update the feature.
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data extracted
                from the feature.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError(
            'You must implement "log_update()" to use the "FeatureLogger" class.')


class ExtractedData(object):
    """Class used to return the data and the number of bytes read after
    extracting data with the :meth:`blue_st_sdk.feature.Feature.extract_data()`
    method."""

    def __init__(self, sample, read_bytes):
        """Constructor.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): A sample object.
            read_bytes (int): The number of bytes read after extracting data.
        """

        # Data extracted from the byte stream.
        self._sample = sample

        # Number of bytes read.
        self._read_bytes = read_bytes

    def get_read_bytes(self):
        """Get the number of bytes read.

        Returns:
            int: The number of bytes read.
        """
        return self._read_bytes

    def get_sample(self):
        """Get the data extracted from the byte stream.

        Returns:
            :class:`blue_st_sdk.feature.Sample`: The data extracted from the
            byte stream.
        """
        return self._sample


class Sample(object):
    """Class that contains the last data from the node."""

    def __init__(self, data, description, timestamp = 0):
        """Constructor.

        Args:
            data (list): Feature's data.
            description (list): Description of the data of the feature (list
                of :class:`blue_st_sdk.features.field.Field` objects).
            timestamp (int): Data's timestamp.
        """
        self._data = data
        self._description = description
        self._timestamp = timestamp
        self._notification_time = datetime.now()

    @classmethod
    def from_sample(self, copy_me):
        """Make a copy of a sample.
    
        Args:
            copy_me (:class:`blue_st_sdk.feature.Sample`): A given sample.
        """
        sample._data = copy_me._data.copy()
        sample._description = copy_me._description.copy()
        sample._timestamp = copy_me.timestamp
        sample._notification_time = copy_me.notification_time
        return sample

    def equals(self, sample):
        """Check the equality of the sample w.r.t. the given one.
    
        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): A sample object.

        Returns:
            bool: True if the objects are equal (timestamp and data), False
            otherwise.
        """
        if sample is None:
            return False
        if isinstance(sample, self.Sample):
            return sample._timestamp == self._timestamp \
                and sorted(sample._data) == sorted(self._data)
        return False

    def get_data(self):
        """Get the data.

        Returns:
            The data of the sample.
        """
        return self._data

    def get_description(self):
        """Get the description.

        Returns:
            list: A list of :class:`blue_st_sdk.features.field.Field` describing
            the sample.
        """
        return self._description

    def get_timestamp(self):
        """Get the timestamp.

        Returns:
            int: The timestamp of the sample.
        """
        return self._timestamp

    def get_notification_time(self):
        """Get the notification time.

        Returns:
            int: The notification time.
        """
        return self._notification_time

    def __str__(self):
        """Get a string representing the last sample.

        Return:
            str: A string representing the last sample.
        """
        return "Timestamp: " + str(self._timestamp) + " Data: " + str(self._data)
