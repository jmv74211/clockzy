import urllib.parse
import requests
from http import HTTPStatus

from clockzy.lib.handlers import codes


def decode_slack_args(data):
    """Function to decode slack response args from x=1&y=2&z=3 format to {x:1, y:2, z:3}

    Args:
        data (str): Slack string args to decode

    Returns
        dict: Slack args in dict format
    """
    data = urllib.parse.unquote(data)
    elements = [pair_value for item in data.split('&') for pair_value in item.split('=')]

    return dict(zip(elements[0::2], elements[1::2]))


def validate_message(message):
    """Function to validate a slack message to send.

    Args:
        message (str): Message to post.

    Returns:
        boolean: True if message format is valid, False otherwise.
    """
    if isinstance(message, str):
        return True
    elif isinstance(message, list) and len(message) > 0 and isinstance(message[0], dict):
        return True

    return False


def post_ephemeral_response_message(message, response_url, mgs_type='text'):
    """ Function to post a ephemeral message in a slack channel given a response_url.

    Args:
        message (str): Message to post.
        response_url (str): Response url from user conversation.
        mgs_type (str): enum: 'text', 'attachments' or 'blocks' depending on message type

    Returns:
        int:
            codes.INVALID_VALUE if the message_type parameter has invalid value
            codes.BAD_SLACK_API_AUTH_CREDENTIALS if the API request could not be resolved due to credentials issue
            codes.BAD_REQUEST_DATA if data sent is not correct
            codes.INTERNAL_SERVER_ERROR if there is some server error
            codes.UNDEFINED_ERROR if the error is unknown
            codes.SUCCESS if the message has ben posted successfully
    """
    if not validate_message(message):
        return codes.INVALID_VALUE

    payload = {mgs_type: message, 'response_type': 'ephemeral'}
    headers = {'content-type': 'application/json'}

    request = requests.post(response_url, json=payload, headers=headers)

    if request.status_code != HTTPStatus.OK:
        if request.status_code == HTTPStatus.UNAUTHORIZED:
            return codes.BAD_SLACK_API_AUTH_CREDENTIALS
        elif request.status_code == HTTPStatus.BAD_REQUEST:
            return codes.BAD_REQUEST_DATA
        elif request.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            return codes.INTERNAL_SERVER_ERROR
        else:
            return codes.UNDEFINED_ERROR

    if request.text != 'ok':
        return codes.BAD_REQUEST_DATA

    return codes.SUCCESS
