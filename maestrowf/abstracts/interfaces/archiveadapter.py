"""Archive Adapter Interface for sending a specification to data storage."""
from abc import ABCMeta, abstractmethod
import logging
import os
import six
import stat


LOGGER = logging.getLogger(__name__)

@six.add_metaclass(ABCMeta)
class ArchiveAdapter(object):

    def submit_data(self):
        pass

    def transform(self):
        pass
