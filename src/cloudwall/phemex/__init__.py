import abc
import base64
import hashlib
import hmac
import time
from decimal import Decimal
from typing import Optional, Dict

from requests import PreparedRequest, Session
from requests.auth import AuthBase


@abc.ABC
class PhemexCredentials(AuthBase):
    """
    Base class for
    """
    @abc.abstractmethod
    def __call__(self, request: PreparedRequest):
        pass


class PublicCredentials(PhemexCredentials):
    """
    Public credentials are a no-op for request signing
    """
    def __call__(self, request: PreparedRequest):
        pass


class AuthCredentials(PhemexCredentials):
    def __call__(self, request: PreparedRequest):
        expiry = str(time.time() + 60)
        message = (request.path_url + expiry + (request.body or ''))
        message = message.encode('ascii')
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())
        request.headers.update({
            'x-phemex-request-signature': signature_b64,
            'x-phemex-request-expiry': expiry,
            'x-phemex-access-token': self.api_key,
            'Content-Type': 'application/json'
        })


class PhemexConnection:
    def __init__(self, credentials: PhemexCredentials, api_url='https://api.phemex.com',
                 request_timeout: int = 30):
        self.credentials = credentials
        self.api_url = api_url.rstrip('/')
        self.request_timeout = request_timeout
        self.session = Session()

    def send_message(self, method: str, endpoint: str, params: Optional[Dict] = None,
                     data: Optional[str] = None):
        url = self.api_url + endpoint
        r = self.session.request(method,
                                 url,
                                 params=params,
                                 data=data,
                                 auth=self.credentials,
                                 timeout=self.request_timeout)
        return r.json(parse_float=Decimal)
