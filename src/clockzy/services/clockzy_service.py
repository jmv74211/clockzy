from flask import Flask, jsonify, request, make_response
from http import HTTPStatus
from functools import wraps

from clockzy.lib.db.db_schema import USER_TABLE, ALIAS_TABLE
from clockzy.lib import global_vars as var
from clockzy.lib.messages import api_responses as ar
from clockzy.lib.models.slack_request import SlackRequest
from clockzy.lib.models.user import User
from clockzy.lib.models.clock import Clock
from clockzy.lib.models.command_history import CommandHistory
from clockzy.lib.models.config import Config
from clockzy.lib.models.alias import Alias
from clockzy.lib.handlers import codes as cd
from clockzy.lib.slack import slack_core as slack
from clockzy.config import settings
from clockzy.lib.messages import slack_messages as msg
from clockzy.lib.db import db_schema as dbs
from clockzy.lib.utils.time import get_current_date_time
from clockzy.lib.db.database_interface import item_exists, get_user_object, get_database_data_from_objects, \
                                              get_config_object
from clockzy.lib.clocking import user_can_clock_this_action, calculate_worked_time
from clockzy.lib import intratime
from clockzy.lib.utils import crypt


app = Flask(__name__)


ALLOWED_COMMANDS = {
    var.ECHO_REQUEST: {
        'description': 'Development endpoint',
        'allowed_parameters': [],
        'num_parameters': 0,
    },
    var.SIGN_UP_REQUEST: {
        'description': 'Sign up for this app.',
        'allowed_parameters': [],
        'num_parameters': 0,
    },
    var.DELETE_USER_REQUEST: {
        'description': 'Delete your user from this app.',
        'allowed_parameters': [],
        'num_parameters': 0,
    },
    var.CLOCK_REQUEST: {
        'description': 'Register a clocking action.',
        'allowed_parameters': ['in', 'pause', 'return', 'out'],
        'free_parameters': False,
        'num_parameters': 1
    },
    var.TIME_REQUEST: {
        'description': 'Get the time worked for the specified time period',
        'allowed_parameters': ['today', 'week', 'month'],
        'free_parameters': False,
        'num_parameters': 1
    },
    var.TIME_HISTORY_REQUEST: {
        'description': 'Get the time worked history for the specified time period',
        'allowed_parameters': ['today', 'week', 'month'],
        'free_parameters': False,
        'num_parameters': 1
    },
    var.CLOCK_HISTORY_REQUEST: {
        'description': 'Get the clock history data for the specified time period',
        'allowed_parameters': ['today', 'week', 'month'],
        'free_parameters': False,
        'num_parameters': 1
    },
    var.TODAY_INFO_REQUEST: {
        'description': 'Get total time worked and clockings made today',
        'allowed_parameters': [],
        'num_parameters': 0
    },
    var.ADD_ALIAS_REQUEST: {
        'description': 'Add an alias for a given user name.',
        'allowed_parameters': [],
        'free_parameters': True,
        'num_parameters': 2,
        'parameters_description': '<user_name> <new_alias_name>'
    },
    var.GET_ALIASES_REQUEST: {
        'description': 'Get all user aliases.',
        'allowed_parameters': [],
        'num_parameters': 0,
    },
    var.CHECK_USER_STATUS_REQUEST: {
        'description': 'Check the user status',
        'allowed_parameters': [],
        'free_parameters': True,
        'num_parameters': 1,
        'parameters_description': '<user_name_or_alias>'
    },
    var.INTRATIME_SYNC_REQUEST: {
        'description': 'Link clock registrations to the intratime application',
        'allowed_parameters': [],
        'free_parameters': True,
        'num_parameters': 2,
        'parameters_description': '<intratime_mail> <intratime_password>'
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

        # If commands parameters are expected, then check them.
        if ALLOWED_COMMANDS[command]['num_parameters'] > 0:
            command_data = ALLOWED_COMMANDS[command]
            # Check that the number of expected parameters is correct (Extra args wont be processed)
            if len(command_parameters) < command_data['num_parameters']:
                parameters = command_data['allowed_parameters'] if len(command_data['allowed_parameters']) > 0 else \
                    command_data['parameters_description']
                parameters_error = f"`{command}` command expects *{command_data['num_parameters']}* " \
                                   f"parameter(s): `{parameters}`"
                slack.post_ephemeral_response_message(msg.build_error_message(parameters_error), response_url)
                return empty_response()

            # Check if the parameter value is correct when it is an enumerated one.
            if not command_data['free_parameters'] and command_parameters[0] not in command_data['allowed_parameters']:
                parameters_error = f"`{command}` command expects one of the following parameters value: " \
                                   f"`{command_data['allowed_parameters']}`"
                slack.post_ephemeral_response_message(msg.build_error_message(parameters_error), response_url)
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
    """Endpoint to check the current server status"""
    return empty_response()


@app.route(var.SIGN_UP_REQUEST, methods=['POST'])
@validate_slack_request
def sign_up(slack_request_object):
    """Endpoint to register a new user"""
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
    """Endpoint to delete a registered user.

    Note: If the user has enabled synchronization with intratime, it will first try to register in that app. If for
          any reason it cannot be registered, then the registration process is cancelled. In case of success,
          it continues with the process and registers locally in the clockzy app.
    """
    action = slack_request_object.command_parameters[0]
    response_url = slack_request_object.response_url

    # Check if the user can clock that action (it makes sense)
    clock_check = user_can_clock_this_action(user_data.id, action)

    # If the clocking is wrong, then indicate it to the user
    if not clock_check[0]:
        error_message = msg.build_block_message('Could not clock your action', clock_check[1], False, msg.ERROR_IMAGE)
        slack.post_ephemeral_response_message(error_message, response_url, 'blocks')

        return empty_response()

    # If the user has intratime app linked, then register the action in the intratime API.
    intratime_enabled = get_config_object(user_data.id).intratime_integration
    if intratime_enabled:
        user_email = user_data.email
        user_password = crypt.decrypt(user_data.password)
        clocking_status = intratime.clocking(action, user_email, user_password)

        # If the intratime clocking has failed, then display an error message and exit so as not to clock it in clockzy.
        if clocking_status != cd.SUCCESS:
            if clocking_status == cd.INTRATIME_AUTH_ERROR:
                slack_message = msg.build_block_message('Could not clock your action',
                                                        'Your intratime credentials are not correct. Please update '
                                                        f"them using the `{var.INTRATIME_SYNC_REQUEST}` command.",
                                                        False, msg.ERROR_IMAGE)
            else:
                slack_message = msg.build_block_message('Could not clock your action',
                                                        'It seems that the intratime API is not available. Try '
                                                        'again in a few seconds', False, msg.ERROR_IMAGE)
            slack.post_ephemeral_response_message(slack_message, response_url, 'blocks')

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
        if intratime_enabled:
            slack_message = msg.build_block_message('Could not clock your action in clockzy app',
                                                    'The clock has been registered in the Intratime app but not in '
                                                    'clockzy. Please, contact with the app administrator',
                                                    False, msg.WARNING_IMAGE)
        else:
            slack_message = msg.build_block_message('Could not clock your action', 'Contact with the app administrator',
                                                    False, msg.ERROR_IMAGE)
        slack.post_ephemeral_response_message(slack_message, response_url, 'blocks')

        return empty_response()

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


@app.route(var.TODAY_INFO_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@command_monitoring
def today_info(slack_request_object, user_data):
    """Endpoint to show the clock history and worked time for today"""
    response_url = slack_request_object.response_url

    # Get the clock data for today
    clock_history_message = msg.build_clock_history_message(user_data.id, 'today')
    slack.post_ephemeral_response_message(clock_history_message, response_url, 'blocks')

    return empty_response()


@app.route(var.COMMAND_HELP_REQUEST, methods=['POST'])
@validate_slack_request
def command_help(slack_request_object):
    """Endpoint to show the available commands of the clockzy app"""
    response_url = slack_request_object.response_url
    command_help_message = msg.build_command_help_message()
    slack.post_ephemeral_response_message(command_help_message, response_url, 'blocks')

    return empty_response()


@app.route(var.ADD_ALIAS_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
@command_monitoring
def add_alias(slack_request_object, user_data):
    """Endpoint to add a new user alias"""
    response_url = slack_request_object.response_url
    user_name = slack_request_object.command_parameters[0]
    alias_name = slack_request_object.command_parameters[1]
    user_data = get_database_data_from_objects({'user_name': user_name}, USER_TABLE)

    # Check if the specified username exists
    if len(user_data) == 0:
        error_message = f"Could not find an user with `{user_name}` username"
        slack.post_ephemeral_response_message(msg.build_error_message(error_message), response_url)
        return empty_response()

    # Check if alias is already registered
    if item_exists({'alias': alias_name}, ALIAS_TABLE):
        error_message = f"The alias `{alias_name}` is already registered as an alias"
        slack.post_ephemeral_response_message(msg.build_error_message(error_message), response_url)
        return empty_response()

    user_id = user_data[0][0]
    alias = Alias(user_id, alias_name)
    result = alias.save()

    # Communicate the result of the alias creation operation
    if result == cd.SUCCESS:
        success_message = f"The `{alias_name}` alias has been registered successfully for the `{user_name}` user name."
        slack.post_ephemeral_response_message(msg.build_success_message(success_message), response_url)
    else:
        error_message = 'Could not create the alias, please contact with the app administrator'
        slack.post_ephemeral_response_message(msg.build_error_message(error_message), response_url)

    return empty_response()


@app.route(var.GET_ALIASES_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@command_monitoring
def get_aliases(slack_request_object, user_data):
    """Endpoint to show all user aliases"""
    response_url = slack_request_object.response_url
    aliases_message = msg.build_get_aliases_message()
    slack.post_ephemeral_response_message(aliases_message, response_url, 'blocks')

    return empty_response()


@app.route(var.CHECK_USER_STATUS_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
@command_monitoring
def get_user_status(slack_request_object, user_data):
    """Endpoint to query the user status given an username or alias name"""
    response_url = slack_request_object.response_url
    user_name = slack_request_object.command_parameters[0]

    # Check if the user name or alias exist
    if not item_exists({'user_name': user_name}, USER_TABLE) and not item_exists({'alias': user_name}, ALIAS_TABLE):
        error_message = f"The `{user_name}` user_name or alias does not exist."
        slack.post_ephemeral_response_message(msg.build_error_message(error_message), response_url)
        return empty_response()

    # Get the user id
    user_data = get_database_data_from_objects({'user_name': user_name}, USER_TABLE)
    if len(user_data) == 0:
        user_id = get_database_data_from_objects({'alias': user_name}, ALIAS_TABLE)[0][1]
    else:
        user_id = user_data[0][0]

    slack_message = msg.build_user_status_message(user_id, user_name)
    slack.post_ephemeral_response_message(slack_message, response_url)

    return empty_response()


@app.route(var.INTRATIME_SYNC_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
def link_intratime_account(slack_request_object, user_data):
    response_url = slack_request_object.response_url
    intratime_user = slack_request_object.command_parameters[0]
    intratime_password = slack_request_object.command_parameters[1]

    # Validate the entered intratime credentials
    if not intratime.check_user_credentials(intratime_user, intratime_password):
        error_message = f"The entered Intratime credentials are not correct."
        slack.post_ephemeral_response_message(msg.build_error_message(error_message), response_url)

    # Add the intratime credentials to the user data in the DB
    user_data.email = intratime_user
    user_data.password = crypt.encrypt(intratime_password)
    if user_data.update() != cd.SUCCESS:
        command_error = 'Your intratime credentials could not be updated, please contact with the app administrator'
        slack.post_ephemeral_response_message(msg.build_error_message(command_error), response_url)
        return empty_response()

    # Update the user configuration and set the intratime integration to True
    user_config = Config(user_data.id, True)
    user_config.update()

    if not get_config_object(user_data.id).intratime_integration:
        command_error = 'Your user configuration could not be updated, please contact with the app administrator'
        slack.post_ephemeral_response_message(msg.build_error_message(command_error), response_url)
        return empty_response()

    success_message = 'The linking with the Intratime app has been successful!'
    slack.post_ephemeral_response_message(msg.build_success_message(success_message), response_url)

    return empty_response()


if __name__ == '__main__':
    app.run(host=settings.SLACK_SERVICE_HOST, port=settings.SLACK_SERVICE_PORT, debug=settings.DEBUG_MODE)
