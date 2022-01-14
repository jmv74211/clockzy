import requests
import json
from http import HTTPStatus

from clockzy.lib.handlers import codes
from clockzy.lib.utils.time import get_current_date_time


INTRATIME_API_URL = 'http://newapi.intratime.es'
INTRATIME_API_LOGIN_PATH = '/api/user/login'
INTRATIME_API_CLOCKING_PATH = f'{INTRATIME_API_URL}/api/user/clocking'
INTRATIME_API_USER_CLOCKINGS_PATH = f'{INTRATIME_API_URL}/api/user/clockings'
INTRATIME_API_APPLICATION_HEADER = 'Accept: application/vnd.apiintratime.v1+json'
INTRATIME_API_HEADER = {
                            'Accept': 'application/vnd.apiintratime.v1+json',
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'charset': 'utf8'
                        }


def get_action_id(action):
    """Get the intratime action ID.

    Args:
        action (str): Action enum: ['in', 'out', 'pause', 'return']

    Returns:
        int: ID associated with the action.
    """
    switcher = {
        'in': 0,
        'out': 1,
        'pause': 2,
        'return': 3,
    }

    return switcher[action]


def get_auth_token(email, password):
    """Get the Intratime auth token.

    Args:
        email (str): User authentication email.
        password (str): User authentication password.

    Returns:
        str: User session token
        int:
            codes.INTRATIME_AUTH_ERROR if user authentication has failed
            codes.INTRATIME_API_CONNECTION_ERROR if there is a Intratime API connection error
    """
    payload = f"user={email}&pin={password}"

    try:
        request = requests.post(url=f"{INTRATIME_API_URL}{INTRATIME_API_LOGIN_PATH}", data=payload,
                                headers=INTRATIME_API_HEADER)
    except ConnectionError as exception:
        return codes.INTRATIME_CONNECTION_ERROR

    try:
        token = json.loads(request.text)['USER_TOKEN']
    except KeyError as exception:
        return codes.INTRATIME_AUTH_ERROR

    return token


def check_user_credentials(email, password):
    """Check if user credentials are correct.

    Args:
        email (str): User email authentication
        password (str): User password authentication

    Returns:
        boolean: True if successful authentication False otherwise.
    """
    token = get_auth_token(email=email, password=password)

    return token != codes.INTRATIME_CONNECTION_ERROR and token != codes.INTRATIME_AUTH_ERROR


def clocking(action, email, password):
    """Register an action in the Intratime API.

    Args:
        action (str): Action enum: ['in', 'out', 'pause', 'return'].
        email (str): User intratime email.
        password (str): User intratime password.

    Returns:
        int: codes.SUCCESS if clocking has been successful.
             codes.INTRATIME_AUTH_ERROR if bad token authentication.
             codes.INTRATIME_CONNECTION_ERROR if there is a Intratime API connection error.
             codes.INTRATIME_CLOCKING_ERROR if intratime API response is not valid.
    """
    date_time = get_current_date_time()
    api_action = get_action_id(action.lower())
    token = get_auth_token(email, password)

    # If it fails to obtain the token, then return error code
    if type(token) is not str:
        return token

    # Add user token to intratime header request
    INTRATIME_API_HEADER.update({'token': token})

    payload = f"user_action={api_action}&user_use_server_time={False}&user_timestamp={date_time}"

    try:
        request = requests.post(url=INTRATIME_API_CLOCKING_PATH, data=payload, headers=INTRATIME_API_HEADER)

        if request.status_code == HTTPStatus.UNAUTHORIZED:
            return codes.INTRATIME_AUTH_ERROR

        if request.status_code == HTTPStatus.CREATED:
            return codes.SUCCESS

        return codes.INTRATIME_CLOCKING_ERROR

    except ConnectionError:
        return codes.INTRATIME_CONNECTION_ERROR
