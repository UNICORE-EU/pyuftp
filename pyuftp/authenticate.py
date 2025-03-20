"""
    Helpers for authenticating
"""

try:
    from urllib3 import disable_warnings

    disable_warnings()
except ImportError:
    pass

from abc import ABCMeta, abstractmethod
from base64 import b64encode, b64decode
from jwt import encode as jwt_encode
from os import getenv
import datetime
import json
import requests
import socket

class AuthenticationFailedException(Exception):  # noqa N818
    """User authentication has failed."""


class Credential:
    """
    Base class for credential
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_auth_header(self):
        """returns the value for the HTTP Authorization header"""
        ...


class UsernamePassword(Credential):
    """
    Produces a HTTP Basic authorization header value

    Args:
        username: the username
        password: the password
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_auth_header(self):
        t = f"{self.username}:{self.password}"
        return "Basic " + b64encode(bytes(t, "ascii")).decode("ascii")
    
    def __repr__(self):
        return "USERNAME"

    __str__ = __repr__

class OIDCToken(Credential):
    """
    Produces a header value "Bearer <auth_token>"

    Args:
        token: the value of the auth token
        refresh_token: optional function that can be called
                       to get a fresh bearer token
    """

    def __init__(self, token, refresh_token=None):
        self.token = token
        self.refresh_token = refresh_token

    def get_auth_header(self):
        if self.refresh_token is not None:
            self.token = self.refresh_token()
        return "Bearer " + self.token

    def __repr__(self):
        return "OIDC"

    __str__ = __repr__


class JWTToken(Credential):
    """
    Produces a signed JWT token ("Bearer <auth_token>")
    uses pyjwt

    Args:
        subject - the subject user name or user X.500 DN
        issuer - the issuer of the token
        secret - a private key
        algorithm - signing algorithm

        lifetime - token validity time in seconds
        etd - for delegation tokens (servers / services authenticating users), this must be 'True'.
              For end users authenticating, set to 'False'
    """

    def __init__(
        self,
        subject,
        issuer,
        secret,
        algorithm="RS256",
        lifetime=300,
        etd=False,
    ):
        self.subject = subject
        self.issuer = issuer if issuer else subject
        self.lifetime = lifetime
        self.algorithm = algorithm
        self.secret = secret
        self.etd = etd

    def create_token(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        payload = {
            "etd": str(self.etd).lower(),
            "sub": self.subject,
            "iss": self.issuer,
            "iat": now,
            "exp": now + datetime.timedelta(seconds=self.lifetime),
        }
        return jwt_encode(payload, self.secret, algorithm=self.algorithm)

    def get_auth_header(self):
        return "Bearer " + self.create_token()

    def __repr__(self):
        return "JWT"

    __str__ = __repr__

class OIDCAgentToken(Credential):
    """
    Produces a header value "Bearer <auth_token>"
    getting the token from a running OIDC Agent (https://github.com/indigo-dc/oidc-agent)

    Args:
        account_name: the account name to use
    """

    _OIDC_AGENT_SOCK = "OIDC_SOCK"

    def __init__(self, account_name):
        self.account_name = account_name
        self.token = None

    def get_auth_header(self):
        if not self.token:
            self.token = self.get_token()
        return "Bearer " + self.token

    def get_token(self)->str:
        req = {"request": "access_token", "account": self.account_name}
        response = json.loads(self.message_agent(json.dumps(req)))
        success = response.get("status", "").lower() == "success"
        if success:
            return response["access_token"]
        else:
            error_msg = response.get("error", json.dumps(response))
            raise IOError("Error: "+error_msg)

    def is_agent_available(self)->bool:
        return getenv(self._OIDC_AGENT_SOCK) is not None

    def message_agent(self, data: str)->str:
        if not self.is_agent_available():
            raise IOError("OIDC agent is not available")
        with socket.socket(family=socket.AF_UNIX, type=socket.SOCK_STREAM) as ap:
            ap.connect(getenv(self._OIDC_AGENT_SOCK))
            f = ap.makefile("rwb")
            f.write(bytes(data, "UTF-8"))
            f.flush()
            reply = f.read(4096)
            return str(reply, "UTF-8")

    def __repr__(self):
        return "OIDC"
    __str__ = __repr__


class Anonymous(Credential):
    """
    Anonymous access - no auth header at all
    """

    def get_auth_header(self):
        return None
    
    def __repr__(self):
        return "ANONYMOUS"

    __str__ = __repr__


def create_credential(username=None, password=None, token=None, identity=None, oidc_agent_account=None):
    """Helper to create the most common types of credentials

    Requires one of the following combinations of arguments

    username + password : create a UsernamePassword credential
    token               ; create a OIDCToken credential from the given token
    username + identity : create a JWTToken credential which will be signed
                          with the given private key (ssh key or PEM)
    oidc_agent_account  : ask a running OIDC agent for a token to authenticate with
    """

    if oidc_agent_account is not None:
        return OIDCAgentToken(oidc_agent_account)
    if token is not None:
        return OIDCToken(token)
    if token is None and identity is None:
        if username=="anonymous":
            return Anonymous()
        else:
            return UsernamePassword(username, password)
    if identity is None:
        raise AuthenticationFailedException("Not enough info to create user credential")
    try:
        from cryptography.hazmat.primitives import serialization
        pem = open(identity).read()
        pem_bytes = bytes(pem, "UTF-8")
        if password is not None and len(password) > 0:
            passphrase = bytes(password, "UTF-8")
        else:
            passphrase = None
        try:
            private_key = serialization.load_ssh_private_key(pem_bytes, password=passphrase)
        except ValueError:
            private_key = serialization.load_pem_private_key(pem_bytes, password=passphrase)
        secret = private_key
        sub = username
        algo = "EdDSA"
        if "BEGIN RSA" in pem:
            algo = "RS256"
        elif "BEGIN EC" in pem or "PuTTY" in pem:
            algo = "ES256"
        return JWTToken(sub, sub, secret, algorithm=algo, etd=False)
    except ImportError:
        raise AuthenticationFailedException(
            "To use key-based authentication, you will need the 'cryptography' package."
        )

def authenticate(auth_url, credential, base_dir="", encryption_key = None, encryption_algo = None,
                 number_of_streams=1, compress=False):
    """authenticate to the auth server and return a tuple (host, port, one-time-password)"""
    if base_dir != "" and not base_dir.endswith("/"):
        base_dir += "/"
    req = {
        "persistent": "true",
        "serverPath": base_dir,
    }
    if compress:
        req["compress"] = "true"
    if number_of_streams>1:
        req["streamCount"] = number_of_streams
    if encryption_key:
        req["encryptionKey"] = encryption_key
        req["encryptionAlgorithm"] = encryption_algo
    params = post_json(auth_url, credential, req)
    success = params['success']
    if(str(success).lower()=="false"):
        try:
            msg = params['reason']
            raise ValueError(msg)
        except KeyError:
            raise ValueError("Error authenticating. Reply: "+str(params))
    return get_connection_params(params)

def issue_token(auth_url, credential, lifetime=-1, limited=False, renewable=False)->str:
    """get a JWT token from the auth server"""
    token_url = auth_url.split("/rest/auth")[0]+"/rest/auth/token"
    params = {}
    if lifetime>-1:
        params["lifetime"] = lifetime
    if limited:
        params["limited"] = "true"
    if renewable:
        params["renewable"] = "true"
    return get_string(token_url, credential, params)

def show_token_details(token: str):
    _p = token.split(".")[1]
    _p += '=' * (-len(_p)%4) # padding
    payload = json.loads(b64decode(_p))
    sub = payload['sub']
    uid = payload.get('uid')
    if uid:
        sub = "%s (uid=%s)" % (sub, uid)
    print(f"Subject:      {sub}")
    print(f"Lifetime (s): {payload['exp']-payload['iat']}")
    print(f"Issued by:    {payload['iss']}")
    print(f"Valid for:    {payload.get('aud', '<unlimited>')}")
    print(f"Renewable:    {payload.get('renewable', 'no')}")

def get_json(url, credential):
    _headers = {
        "Authorization": credential.get_auth_header(),
        "Accept": "application/json",
    }
    with requests.get(headers=_headers, url=url, verify=False) as res:
        check_error(res)
        js = res.json()
    return js

def get_string(url, credential, params: dict=None) ->  str:
    _headers = {
        "Authorization": credential.get_auth_header(),
        "Accept": "text/plain",
    }
    with requests.get(headers=_headers, url=url, params=params, verify=False) as res:
        check_error(res)
        return res.text

def get_connection_params(json_data) -> tuple[str, str, str]:
    return json_data["serverHost"], json_data["serverPort"], json_data["secret"]

def post_json(url, credential, json_data, as_json = True):
    _headers = {
        "Authorization": credential.get_auth_header(),
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    with requests.post(headers=_headers, url=url, json=json_data, verify=False) as res:
        check_error(res)
        if res.status_code==201:
            return res.headers['Location']
        elif as_json:
            return res.json()
    
def check_error(res):
    """checks for error and extracts any error info sent by the server"""
    if 400 <= res.status_code < 600:
        reason = res.reason
        try:
            reason = res.json().get("errorMessage", "n/a")
        except ValueError:
            pass
        msg = f"{res.status_code} Server Error: {reason} for url: {res.url}"
        raise requests.HTTPError(msg, response=res)
    else:
        res.raise_for_status()