from flask import Flask, jsonify, request, make_response
from http import HTTPStatus
from functools import wraps

from clockzy.lib.db.db_schema import USER_TABLE
from clockzy.lib.global_vars import slack_vars as var
from clockzy.lib.messages import api_responses as ar
from clockzy.lib.models.slack_request import SlackRequest
from clockzy.lib.models.user import User
from clockzy.lib.models.clock import Clock
from clockzy.lib.models.command_history import CommandHistory
from clockzy.lib.models.config import Config
from clockzy.lib.handlers import codes as cd
from clockzy.lib.slack import slack_core as slack
from clockzy.config import settings
from clockzy.lib.slack import slack_messages as msg
from clockzy.lib.db import db_schema as dbs
from clockzy.lib.utils.time import get_current_date_time
from clockzy.lib.db.database_interface import item_exists, get_user_object
from clockzy.lib.clocking import user_can_clock_this_action, calculate_worked_time


app = Flask(__name__)


ALLOWED_COMMANDS = {
    var.ECHO_REQUEST: {
        'description': 'Development endpoint',
        'allowed_parameters': []
    },
    var.SIGN_UP_REQUEST: {
        'description': 'Sign up for this app.',
        'allowed_parameters': []
    },
    var.DELETE_USER_REQUEST: {
        'description': 'Delete your user from this app.',
        'allowed_parameters': []
    },
    var.CLOCK_REQUEST: {
        'description': 'Register a clocking action.',
        'allowed_parameters': ['in', 'pause', 'return', 'out']
    },
    var.TIME_REQUEST: {
        'description': 'Get the time worked for the specified time period',
        'allowed_parameters': ['today', 'week', 'month']
    },
    var.TIME_HISTORY_REQUEST: {
        'description': 'Get the time worked history for the specified time period',
        'allowed_parameters': ['today', 'week', 'month']
    },
    var.CLOCK_HISTORY_REQUEST: {
        'description': 'Get the clock history data for the specified time period',
        'allowed_parameters': ['today', 'week', 'month']
    }
}


def empty_response():
    """Build an empty response with 200 status code"""
    return make_response('', HTTPStatus.OK)


# ----------------------------------------------------------------------------------------------------------------------
#                                                API DECORATORS                                                        #
# ----------------------------------------------------------------------------------------------------------------------

def validate_slack_request(func):
    """Validate that the request comes from the slack app and from no other source.

    In addition, it adds a new parameter that contains the slack request information.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        decoded_request_body = slack.decode_slack_args(request.get_data().decode('utf-8'))
        slack_request_object = SlackRequest(headers=request.headers, **decoded_request_body)
        validation = slack_request_object.validate_slack_request_signature(request.get_data())

        if validation == cd.NON_SLACK_REQUEST:
            return jsonify({'result': ar.NON_SLACK_REQUEST}), HTTPStatus.UNAUTHORIZED
        elif validation == cd.BAD_SLACK_TIMESTAMP_REQUEST:
            return jsonify({'result': ar.BAD_SLACK_HEADERS_REQUEST}), HTTPStatus.UNAUTHORIZED
        elif validation == cd.BAD_SLACK_SIGNATURE:
            return jsonify({'result': ar.BAD_SLACK_SIGNATURE}), HTTPStatus.UNAUTHORIZED

        # Add the slack request object to the function arguments
        kwargs['slack_request_object'] = slack_request_object

        return func(*args, **kwargs)

    return wrapper


def validate_user(func):
    """Check that the slack user is registered in the clockzy app before running the command action.

    In addition, it adds a new parameter that contains the user information.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'slack_request_object' not in kwargs:
            print('Programming error, slack_request_object does not exist in the validate_user decorator.')
            return make_response('', HTTPStatus.INTERNAL_SERVER_ERROR)

        user_id = kwargs['slack_request_object'].user_id
        response_url = kwargs['slack_request_object'].response_url

        if not item_exists({'id': user_id}, USER_TABLE):
            slack.post_ephemeral_response_message(msg.USER_NOT_REGISTERED, response_url)
            return empty_response()

        # Get the user data and return it
        kwargs['user_data'] = get_user_object(user_id)

        return func(*args, **kwargs)

    return wrapper


def validate_command_parameters(func):
    """Check that the command or the command parameters are allowed."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'slack_request_object' not in kwargs:
            print('Programming error slack_request_object does not exist in the validate_command_parameters decorator.')
            return make_response('', HTTPStatus.INTERNAL_SERVER_ERROR)

        command = kwargs['slack_request_object'].command
        command_parameters = kwargs['slack_request_object'].command_parameters
        response_url = kwargs['slack_request_object'].response_url

        # Check if it is an expected command
        if command not in ALLOWED_COMMANDS.keys():
            command_error = f"`{command}` is not an allowed command. Allowed ones: `{ALLOWED_COMMANDS.keys()}`"
            slack.post_ephemeral_response_message(msg.build_error_message(command_error), response_url)
            return empty_response()

        # Check if the specified parameter is allowed
        if len(command_parameters) == 0 and len(ALLOWED_COMMANDS[command]['allowed_parameters']) > 0 or \
           command_parameters[0] not in ALLOWED_COMMANDS[command]['allowed_parameters']:
            parameter_error = f"`{command}` command expects one of the following parameters: " \
                              f"`{ALLOWED_COMMANDS[command]['allowed_parameters']}`"
            slack.post_ephemeral_response_message(msg.build_error_message(parameter_error), response_url)
            return empty_response()

        return func(*args, **kwargs)

    return wrapper


def command_monitoring(func):
    """Log the command request in the history"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'slack_request_object' not in kwargs:
            print('Programming error, slack_request_object does not exist in the command_monitoring decorator.')
            return make_response('', HTTPStatus.INTERNAL_SERVER_ERROR)

        command_history = CommandHistory(kwargs['slack_request_object'].user_id, kwargs['slack_request_object'].command,
                                         ' '.join(kwargs['slack_request_object'].command_parameters))
        command_history.save()

        return func(*args, **kwargs)

    return wrapper


# ----------------------------------------------------------------------------------------------------------------------
#                                                API ENDPOINTS                                                         #
# ----------------------------------------------------------------------------------------------------------------------


@app.route(var.ECHO_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@command_monitoring
def echo(slack_request_object, user_data):
    """Endpoint to check the current server status

    - Input_data: {}
    - Output_data: {'result': 'Alive'}
    """
    return empty_response()


@app.route(var.SIGN_UP_REQUEST, methods=['POST'])
@validate_slack_request
def sign_up(slack_request_object):
    """ Endpoint to register a new user"""
    # Save the user in the DB
    user = User(slack_request_object.user_id, slack_request_object.user_name)
    result = user.save()

    # Create the objects associated to the user
    user_config = Config(user.id, False)
    user_config.save()

    # Communicate the result of the user creation operation
    if result == cd.SUCCESS:
        slack.post_ephemeral_response_message(msg.ADD_USER_SUCCESS, slack_request_object.response_url)
    elif result == cd.ITEM_ALREADY_EXISTS:
        slack.post_ephemeral_response_message(msg.USER_ALREADY_REGISTERED, slack_request_object.response_url)
    else:
        slack.post_ephemeral_response_message(msg.ADD_USER_ERROR, slack_request_object.response_url)

    return empty_response()


@app.route(var.DELETE_USER_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@command_monitoring
def delete_user(slack_request_object, user_data):
    """Endpoint to delete a registered user"""
    result = user_data.delete()

    if result == cd.SUCCESS:
        slack.post_ephemeral_response_message(msg.DELETE_USER_SUCCESS, slack_request_object.response_url)
    else:
        slack.post_ephemeral_response_message(msg.DELETE_USER_ERROR, slack_request_object.response_url)

    return empty_response()


@app.route(var.CLOCK_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
@command_monitoring
def clock(slack_request_object, user_data):
    """Endpoint to delete a registered user"""
    action = slack_request_object.command_parameters[0]
    response_url = slack_request_object.response_url

    # Check if the user can clock that action (it makes sense)
    clock_check = user_can_clock_this_action(user_data.id, action)

    # If the clocking is wrong, then indicate it to the user
    if not clock_check[0]:
        error_message = msg.build_block_message('Could not clock your action', clock_check[1], False, msg.ERROR_IMAGE)
        slack.post_ephemeral_response_message(error_message, response_url, 'blocks')
        return empty_response()

    # Save the clock in the DB
    clock = Clock(user_data.id, action, get_current_date_time())
    result = clock.save()

    # Communicate the result of the clocking operation
    if result == cd.SUCCESS:
        slack_message = msg.build_successful_clocking_message(user_data.id, clock.action, clock.date_time,
                                                              user_data.user_name)
        slack.post_ephemeral_response_message(slack_message, response_url, 'blocks')
    else:
        slack_message = msg.build_block_message('Could not clock your action', 'Contact with the app administrator',
                                                False, msg.ERROR_IMAGE)
        slack.post_ephemeral_response_message(slack_message, response_url)

    # Update the last registration data from that user
    user_data.last_registration_date = get_current_date_time()
    user_data.update()

    return empty_response()


@app.route(var.TIME_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
@command_monitoring
def time(slack_request_object, user_data):
    """Endpoint to get the worked time for the specified time range"""
    time_range = slack_request_object.command_parameters[0]
    response_url = slack_request_object.response_url

    # Calculate the worked time
    worked_time = calculate_worked_time(user_data.id, time_range=time_range)

    # Communicate the result
    slack.post_ephemeral_response_message(msg.build_worked_time_message(time_range, worked_time), response_url)

    return empty_response()


@app.route(var.TIME_HISTORY_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
@command_monitoring
def time_history(slack_request_object, user_data):
    """Endpoint to get the worked time history for the specified time range"""
    time_range = slack_request_object.command_parameters[0]
    response_url = slack_request_object.response_url

    # Get the clock data from the specified time range
    worked_time_history_message = msg.build_time_history_message(user_data.id, time_range)
    slack.post_ephemeral_response_message(worked_time_history_message, response_url, 'blocks')

    return empty_response()


@app.route(var.CLOCK_HISTORY_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
@command_monitoring
def clock_history(slack_request_object, user_data):
    """Endpoint to get the clock history for the specified time range"""
    time_range = slack_request_object.command_parameters[0]
    response_url = slack_request_object.response_url

    # Get the clock data from the specified time range
    clock_history_message = msg.build_clock_history_message(user_data.id, time_range)
    slack.post_ephemeral_response_message(clock_history_message, response_url, 'blocks')

    return empty_response()


if __name__ == '__main__':
    app.run(host=settings.SLACK_SERVICE_HOST, port=settings.SLACK_SERVICE_PORT, debug=settings.DEBUG_MODE)
