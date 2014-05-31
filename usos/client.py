from urllib import urlencode, quote, splittype, splithost, splitport
import urlparse
import json
import time
import random
import socket
import ssl
import httplib
from collections import namedtuple

from .utils.object import sanitized_attr
from .utils.http import CA_CERTS_FILE, HTTPSVerifyingConnection


# Modify only at your own risk:
#   from usos import client
#   client.ALLOW_INSECURE_CONNECTIONS = True
ALLOW_INSECURE_CONNECTIONS = False

FILE_METHODS = frozenset(['services/users/photo', 'services/photos/photo'])
URLENCODED_METHODS = frozenset(['services/oauth/request_token', 'services/oauth/access_token'])


Consumer = namedtuple('Consumer', ['key', 'secret'])
Token = namedtuple('Token', ['key', 'secret'])


class ClientError(IOError):
    pass


class NetworkError(ClientError):
    """
    Indicates network communication failure (unknown host, host unreachable,
    timeout error etc.)
    """


class ProtocolError(ClientError):
    """
    Indicates protocol failure (SSL, HTTP, invalid JSON string, etc.)
    """


class HttpError(ClientError):
    """
    Raised when response status != 200.
    """

    def __init__(self, status, *args, **kwargs):
        super(HttpError, self).__init__(*args, **kwargs)
        self.status = status


class BadRequest(HttpError):
    def __init__(self, d):
        super(BadRequest, self).__init__(400, d['message'])
        self._d = d

    @property
    def message(self):
        return self._d['message']

    def __contains__(self, key):
        return key in self._d

    def __getitem__(self, key):
        return self._d[key]

    def get(self, key, default=None):
        return self._d.get(key, default)


class Unauthorized(HttpError):
    def __init__(self, *args, **kwargs):
        super(Unauthorized, self).__init__(401, *args, **kwargs)


class FileWrapper(object):
    def __init__(self, response):
        self._response = response
        self.content_type = response.getheader('content-type')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.closed:
            self.close()

    @property
    def closed(self):
        return self._response.isclosed()

    def close(self):
        self._response.close()

    # read(self, [size])
    def read(self, *args):
        return self._response.read(*args)

    def fileno(self):
        return self._response.fileno()


class Client(object):
    def __init__(self, base_url, consumer=None, token=None):
        self.base_url = base_url
        self.consumer = consumer
        self.token = token
        self.services = MethodProxy(self, 'services')

    @sanitized_attr
    def base_url(self, value):
        if not ALLOW_INSECURE_CONNECTIONS and not value.startswith('https://'):
            scheme, rest = splittype(value)
            host, path = splithost(rest)
            _, port = splitport(host)
            if scheme != 'http':
                raise ValueError('Invalid base_url scheme: {0!r}'.format(scheme))
            if port:
                raise ValueError('Invalid base_url (should start with https://): {0!r}'.format(value))
            value = 'https' + value[4:]
        if not value.endswith('/'):
            value += '/'
        return value

    @sanitized_attr
    def consumer(self, value):
        if value is None or isinstance(value, Consumer):
            return value
        else:
            key, secret = value
            return Consumer(key, secret)

    @sanitized_attr
    def token(self, value):
        if value is None or isinstance(value, Token):
            return None
        else:
            key, secret = value
            return Token(key, secret)

    def _get_auth_params(self):
        if self.consumer is None:
            return None

        params = dict(
            oauth_consumer_key=self.consumer.key,
            oauth_signature_method='PLAINTEXT',
            oauth_signature=self.consumer.secret + '&',
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=str(random.randint(0, 1000000000)),
            oauth_version='1.0',
        )

        if self.token is not None:
            params['oauth_token'] = self.token.key
            params['oauth_signature'] += self.token.secret

        return params

    def _prep_headers(self):
        params = self._get_auth_params()
        if not params:
            return {}
        else:
            return dict(
                Authorization='OAuth ' + ', '.join('{0}="{1}"'.format(k, quote(v)) for k, v in params.iteritems())
            )

    def _prep_request(self, path, params):
        return self.base_url + path, self._prep_headers(), urlencode(list(self._prep_params(params)))

    def call_method(self, path, params=None, mode=None):
        if mode is None:
            if path in FILE_METHODS:
                mode = 'file'
            elif path in URLENCODED_METHODS:
                mode = 'urlencoded'
            else:
                mode = 'format'
        return self._call_method(path, params, mode)

    def _call_method(self, path, params, mode):
        url, headers, body = self._prep_request(path, params)

        # It would be nice to use high-level network interface here, like urllib2, but there is no way
        # to distinguish whether URLError was caused by network failure or protocol (HTTP, SSL) failure

        scheme, rest = splittype(url)
        host, path = splithost(rest)
        hostname, port = splitport(host)

        if scheme == 'http':
            conn = httplib.HTTPConnection(hostname, port)
        elif scheme == 'https':
            conn = HTTPSVerifyingConnection(hostname, port, ca_certs_file=CA_CERTS_FILE)
        else:
            raise ValueError('Invalid scheme: {0!r}'.format(scheme))

        try:
            conn.request('POST', path, body, headers=headers)
            response = conn.getresponse()
        except httplib.HTTPException as err:
            raise ProtocolError(str(err))
        except ssl.SSLError as err:
            raise ProtocolError(str(err))
        except socket.error as err:
            raise NetworkError(str(err))

        content_type = response.getheader('content-type', '')
        if response.status == 200:
            if mode == 'file':
                return FileWrapper(response)
            elif mode == 'urlencoded':
                return dict(urlparse.parse_qsl(response.read()))
            elif content_type.startswith('application/json'):
                try:
                    return json.load(response)
                except ValueError as err:
                    raise ProtocolError(str(err))
            else:
                raise ProtocolError('Invalid response content type: {0}'.format(content_type))
        else:
            if content_type.startswith('application/json'):
                try:
                    params = json.load(response)
                except ValueError as err:
                    raise ProtocolError(str(err))
                if not isinstance(params, dict) or 'message' not in params:
                    raise ProtocolError('Invalid error response: {0!r}'.format(params))
            else:
                params = dict(message=response.read().decode('UTF-8', errors='ignore'))

            if response.status == 400:
                raise BadRequest(params)
            elif response.status == 401:
                raise Unauthorized(params['message'])
            else:
                raise HttpError(response.status, params['message'])

    def _prep_params(self, params):
        if not params:
            return

        for k, v in params.iteritems():
            if v is True:
                v = 'true'
            elif v is False:
                v = 'false'
            elif v is None:
                continue
            elif isinstance(v, (int, long, float, dict, list)):
                v = json.dumps(v)
            elif isinstance(v, basestring):
                v = unicode(v).encode('UTF-8')
            else:
                raise TypeError('Invalid parameter value: {0!r}'.format(v))
            yield k, v


class MethodProxy(object):
    def __init__(self, client, path):
        self._client = client
        self._path = path

    def __call__(self, **params):
        return self._client.call_method(self._path, params)

    def __getattr__(self, item):
        return MethodProxy(self._client, '{0}/{1}'.format(self._path, item))
