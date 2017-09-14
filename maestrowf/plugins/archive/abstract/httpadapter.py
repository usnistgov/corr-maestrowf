"""
HTTP Adapter Interface for defining the API for interacting with HTTP requests.
"""
from abc import ABCMeta, abstractmethod
import logging
import six
import json
import httplib2

LOGGER = logging.getLogger(__name__)

@six.add_metaclass(ABCMeta)
class HttpAdapter(object):
    """
    Abstract class representing the interface for interacting with HTTP.
    """

    def __init__(self, disable_ssl_certificate_validation=True):
        self.client = httplib2.Http('.cache',
            disable_ssl_certificate_validation=disable_ssl_certificate_validation)

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

    def _check_response_content(self, url, response, content, response_code=200,
                                content_code=200):
        """
        Used to check if the response code and the content code match the given
        codes.

        :param url: The URL used for the HTTP request.
        :param response: An HTTP Response to check.
        :param content: An HTTP content to check.
        :param response_code: The response code to check response against.
            Default 200.
        :param content_code: The content code to check content against. Default
            200.
        :raises StandardError: If the response status does not match the
            inputed response_code or if the content code does not match the
            inputed content_code.
        """
        LOGGER.debug('Checking response and content codes.')
        if response.status != response_code:
            msg = ('URL <{}>\nProvided bad response status: {}\nContent: {}'\
                ''.format(url, response.status, content))
            LOGGER.exception(msg)
            raise ValueError(msg)
        else:
            code = json.loads(content)['code']
            if code != content_code:
                msg = ('URL <{}>\nProvided bad content code status: {}\n'\
                    'Expected content code: {}\nContent: {}'.format(url, code,
                        content_code, content))
                LOGGER.exception(msg)
                raise ValueError(msg)

    def _type(self):
        return self.__class__.__name__
