"""
HTTP Adapter Interface for defining the API for interacting with HTTP requests.
"""
from abc import ABCMeta, abstractmethod
import logging
import six


LOGGER = logging.getLogger(__name__)

@six.add_metaclass(ABCMeta)
class HttpAdapter(object):
    """
    Abstract class representing the interface for interacting with HTTP.
    """
    def _get(self, url):
        pass

    def _post(self, url, content):
        pass
