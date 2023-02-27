"""DNS Authenticator for Dinahosting."""
import json
import logging

import requests
import base64
import tldextract


from certbot import errors
from certbot import interfaces
from certbot.plugins import dns_common


logger = logging.getLogger(__name__)


API_URL = "https://dinahosting.com/special/api.php"

class Authenticator(dns_common.DNSAuthenticator):
    """
    DNS Authenticator for Dinahosting
    This Authenticator uses the Dinahosting API to fulfill a dns-01 challenge.
    """

    description = "Obtain certificates using a DNS TXT record (if you are using Dinahosting for DNS)."
    ttl = 300

    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials = None

    @classmethod
    def add_parser_arguments(cls, add):  # pylint: disable=arguments-differ
        super(Authenticator, cls).add_parser_arguments(
            add, default_propagation_seconds=120
        )
        add("credentials", help="Dinahosting credentials INI file.")

    def more_info(self):  # pylint: disable=missing-docstring,no-self-use
        return (
            "This plugin configures a DNS TXT record to respond to a dns-01 challenge using the Dinahosting API."
        )

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            "credentials",
            "Dinahosting credentials INI file",
            {
                "username": "Username for Dinahosting API.",
                "password": "Password for Dinahosting API.",
            },
        )

    def _perform(self, fulldomain, validation_name, validation):
        extracted = tldextract.extract(fulldomain)
        domain =  "{}.{}".format(extracted.domain, extracted.suffix)
        self._get_dinahosting_client().add_txt_record(
            domain, validation_name, validation
        )

    def _cleanup(self, fulldomain, validation_name, validation):
        extracted = tldextract.extract(fulldomain)
        domain =  "{}.{}".format(extracted.domain, extracted.suffix)
        index = validation_name.rfind("." + domain)
        hostname = validation_name[:index]
        self._get_dinahosting_client().del_txt_record(
            domain, hostname, validation
        )

    def _get_dinahosting_client(self):
        return _DinahostingClient(
            self.credentials.conf("username"),
            self.credentials.conf("password"),
        )


class _DinahostingClient(object):
    """
    Encapsulates all communication with the Dinahosting API.
    """

    def __init__(self, username, password):
        logger.debug("Creating DinahostingClient")
        self.username = username
        self.password = password

    def add_txt_record(self, domain, hostname, text):
        """
        Add a TXT record using the supplied information.
        :param str domain: The domain to use to look up the managed zone.
        :param str hostname: The record name (typically beginning with '_acme-challenge.').
        :param str text: The record content (typically the challenge validation).
        :raises certbot.errors.PluginError: if an error occurs communicating with the Dinahosting API
        """
        method = "Domain_Zone_AddTypeTXT"
        params = {
            "domain": domain,
            "hostname": hostname,
            "text": text,
        }
        logger.debug("Insert TXT record with params: %s", params)
        self._api_request(method, params)

    def del_txt_record(self, domain, hostname, value):
        """
        Delete a TXT record using the supplied information.
        :param str domain: The domain to use to look up the managed zone.
        :param str hostname: The record name (typically beginning with '_acme-challenge.').
        :param str value: The record content (typically the challenge validation).
        :raises certbot.errors.PluginError: if an error occurs communicating with the Dinahosting API
        """
        method = "Domain_Zone_DeleteTypeTXT"
        params = {
            "domain": domain,
            "hostname": hostname,
            "value": value,
        }
        logger.debug("Delete TXT record with params: %s", params)
        self._api_request(method, params)

    def _api_request(self, method, params=None):
        """
        Make a request against Dinahosting API.
        :param str method: API method to use.
        :param dict params: Dictionary to send a JSON data.
        :returns: Dictionary of the JSON response.
        :rtype: dict
        """
        authorization = '%s:%s' % (self.username, self.password)
        authorization_b64 = base64.b64encode(authorization.encode("utf-8")).decode("ascii")
        data = {
            "method": method,
            "params": params
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % authorization_b64
        }
        return self._request(data, headers)

    def _request(self, data=None, headers=None):
        """
        Make HTTP request.
        :param dict data: Dictionary with data to send as JSON.
        :param dict headers: Headers to send.
        :returns: Dictionary of the JSON response.
        :rtype: dict
        :raises certbot.errors.PluginError: In case of HTTP error.
        """
        logger.debug("API Request to URL: %s", API_URL)
        logger.debug(" - Data...: %s", data)
        resp = requests.post(API_URL, data=json.dumps(data), headers=headers)
        if resp.status_code != 200:
            raise errors.PluginError("HTTP Error {0}".format(resp.status_code))
        try:
            result = resp.json()
            logger.debug("Resultado: %s", result)
        except json.JSONDecodeError:
            raise errors.PluginError(
                "API response with non JSON: {0}".format(resp.text)
            )
        else:
            return result