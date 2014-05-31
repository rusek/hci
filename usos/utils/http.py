import httplib
import os.path
import socket
import ssl


CA_CERTS_FILE = os.path.join(os.path.dirname(__file__), 'cacerts.crt')


class HTTPSVerifyingConnection(httplib.HTTPSConnection):
    def __init__(self, host, port=None, ca_certs_file=None, key_file=None, cert_file=None,
                 strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 source_address=None):
        httplib.HTTPSConnection.__init__(self, host, port, key_file, cert_file, strict, timeout, source_address)
        self.ca_certs_file = ca_certs_file

    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout, self.source_address)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        if self.ca_certs_file:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                                        ca_certs=self.ca_certs_file, cert_reqs=ssl.CERT_REQUIRED)
        else:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file)
