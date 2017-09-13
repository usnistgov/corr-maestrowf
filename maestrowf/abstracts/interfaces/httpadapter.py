"""
HTTP Adapter Interface for defining the API for interacting with HTTP requests.
"""
from abc import ABCMeta, abstractmethod
import logging
import six
import json

LOGGER = logging.getLogger(__name__)

@six.add_metaclass(ABCMeta)
class HttpAdapter(object):
    """
    Abstract class representing the interface for interacting with HTTP.
    """
    def _get(self, url):
        """
        Executes a HTTP Get on the given URL.

        :param url: The url to perform the HTTP Get on.
        :returns: A tuple containing the HTTP response and content.
        """
        LOGGER.debug('Performing HTTPGet on: {}'.format(url))
        headers = {'Accept': 'application/json'}
        response, content = self.client.request(url, headers=headers)
        return response, content

    def _post(self, url, content):
        """
        Executes a HTTP Post on the given URL.

        :param url: The url to perform the HTTP Get on.
        :param content: The content to POST with.
        :returns: A tuple containing the HTTP response and content.
        """
        LOGGER.debug('Performing HTTPPost on: {}\nwith content: {}'\
            ''.format(url, content))
        headers = {'Content-Type': 'application/json'}
        response, content = self.client.request(url, 'POST',
                                                json.dumps(content),
                                                headers=headers)
        return response, content
