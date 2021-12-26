import hmac
import hashlib
import time

from clockzy.lib.handlers.codes import BAD_SLACK_SIGNATURE, BAD_SLACK_TIMESTAMP_REQUEST, NON_SLACK_REQUEST, SUCCESS
from clockzy.config.settings import SLACK_APP_SIGNATURE


class SlackRequest:
    """Slack request mapping class.

    Args:
        headers (list(str)): Request headers.
        token (str): Slack request token.
        team_id (str): Slack request team_id.
        team_domain (str): Slack request team_domain.
        channel_id (str): Slack request channel_id.
        channel_name (str): Slack request channel_name.
        user_id (str): Slack request user_id.
        user_name (str): Slack request user_name.
        command (str): Slack request command.
        text (str): Slack request command parameters.
        api_app_id (str): Slack request api_app_id.
        is_enterprise_install (str): Slack request is_enterprise_install.
        response_url (str): Slack request response_url.
        trigger_id (str): Slack request trigger_id.

    Attributes:
        headers (list(str)): Request headers.
        token (str): Slack request token.
        team_id (str): Slack request team_id.
        team_domain (str): Slack request team_domain.
        channel_id (str): Slack request channel_id.
        channel_name (str): Slack request channel_name.
        user_id (str): Slack request user_id.
        user_name (str): Slack request user_name.
        command (str): Slack request command.
        text (str): Slack request command parameters.
        api_app_id (str): Slack request api_app_id.
        is_enterprise_install (str): Slack request is_enterprise_install.
        response_url (str): Slack request response_url.
        trigger_id (str): Slack request trigger_id.
    """
    def __init__(self, headers=[], token=None, team_id=None, team_domain=None, channel_id=None,
                 channel_name=None, user_id=None, user_name=None, command=None, text=None,
                 api_app_id=None, is_enterprise_install=None, response_url=None, trigger_id=None):
        self.headers = headers
        self.token = token
        self.team_id = team_id
        self.team_domain = team_domain
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.user_id = user_id
        self.user_name = user_name
        self.command = command
        self.command_parameters = [] if text == '' else text.split('+')
        self.api_app_id = api_app_id
        self.is_enterprise_install = is_enterprise_install
        self.response_url = response_url
        self.trigger_id = trigger_id

    def __str__(self):
        """Define how the class object will be displayed."""
        return f"token: {self.token}, team_id: {self.team_id}, " \
               f"team_domain: {self.team_domain}, channel_id: {self.channel_id}, channel_name: {self.channel_name}, " \
               f"user_id: {self.user_id}, user_name: {self.user_name}, command: {self.command}, " \
               f"command_parameters: {self.command_parameters}, api_app_id: {self.api_app_id}, " \
               f"is_enterprise_install: {self.is_enterprise_install}, response_url: {self.response_url}, " \
               f"trigger_id: {self.trigger_id}, headers: [{self.headers}]"

    def validate_slack_request_signature(self, raw_body):
        """Authenticate the request, verifying the signature.

        Args:
            raw_body (str): Request raw body (urlencode format).

        Returns:
            int: SUCCESS if authentication is ok
                 NON_SLACK_REQUEST, BAD_SLACK_TIMESTAMP_REQUEST, BAD_SLACK_SIGNATURE otherwise.
        """
        if 'X-Slack-Signature' not in self.headers or 'X-Slack-Request-Timestamp' not in self.headers:
            return NON_SLACK_REQUEST

        request_signature = self.headers['X-Slack-Signature']
        request_timestamp = int(self.headers['X-Slack-Request-Timestamp'])
        request_body = raw_body.decode('utf-8')

        # Verify that the request is not prior to 1 minute (Avoid replay attacks)
        if int(time.time() - request_timestamp) > 60:
            return BAD_SLACK_TIMESTAMP_REQUEST

        sign_basestring = f"v0:{request_timestamp}:{request_body}"
        signature = hmac.new(bytes(SLACK_APP_SIGNATURE, 'utf-8'), bytes(sign_basestring, 'utf-8'),
                             digestmod=hashlib.sha256).hexdigest()
        signature_check = f"v0={signature}"

        # Validate request signature
        if not hmac.compare_digest(signature_check, request_signature):
            return BAD_SLACK_SIGNATURE

        return SUCCESS
