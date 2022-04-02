import logging
from flask import Flask, jsonify, request, make_response
from http import HTTPStatus
from functools import wraps
from os import environ
from os.path import join

from clockzy.lib.db.db_schema import USER_TABLE, ALIAS_TABLE, TEMPORARY_CREDENTIALS_TABLE
from clockzy.lib import global_vars as var
from clockzy.lib.messages import api_responses as ar
from clockzy.lib.models.slack_request import SlackRequest
from clockzy.lib.models.user import User
from clockzy.lib.models.clock import Clock
from clockzy.lib.models.command_history import CommandHistory
from clockzy.lib.models.config import Config
from clockzy.lib.models.alias import Alias
from clockzy.lib.models.temporary_credentials import TemporaryCredentials
from clockzy.lib.handlers import codes as cd
from clockzy.lib.slack import slack_core as slack
from clockzy.config import settings
from clockzy.lib.messages.slack_messages import send_slack_message
from clockzy.lib.db import db_schema as dbs
from clockzy.lib.utils.time import get_current_date_time
from clockzy.lib.db.database_interface import item_exists, get_user_object, get_database_data_from_objects, \
                                              get_config_object
from clockzy.lib.clocking import user_can_clock_this_action, calculate_worked_time
from clockzy.lib import intratime
from clockzy.lib.utils import crypt, time
from clockzy.lib.messages import logger_messages as lgm
from clockzy.scripts import initialize_database, database_healthcheck


clockzy_service = Flask(__name__)
app_logger = logging.getLogger('clockzy')

ALLOWED_COMMANDS = {
    var.ECHO_REQUEST: {
        'description': 'Development endpoint.',
        'allowed_parameters': [],
        'num_parameters': 0,
    },
    var.SIGN_UP_REQUEST: {
        'description': 'Sign up for this app.',
        'allowed_parameters': [],
        'num_parameters': 0,
    },
    var.UPDATE_USER_REQUEST: {
        'description': 'Update the username and time zone with the slack profile info.',
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
        'description': 'Get the time worked for the specified time period.',
        'allowed_parameters': ['today', 'week', 'month'],
        'free_parameters': False,
        'num_parameters': 1
    },
    var.TIME_HISTORY_REQUEST: {
        'description': 'Get the time worked history for the specified time period.',
        'allowed_parameters': ['today', 'week', 'month'],
        'free_parameters': False,
        'num_parameters': 1
    },
    var.CLOCK_HISTORY_REQUEST: {
        'description': 'Get the clock history data for the specified time period.',
        'allowed_parameters': ['today', 'week', 'month'],
        'free_parameters': False,
        'num_parameters': 1
    },
    var.TODAY_INFO_REQUEST: {
        'description': 'Get total time worked and clockings made today.',
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
        'description': 'Check the user status.',
        'allowed_parameters': [],
        'free_parameters': True,
        'num_parameters': 1,
        'parameters_description': '<user_name_or_alias>'
    },
    var.ENABLE_INTRATIME_INTEGRATION_REQUEST: {
        'description': 'Link clock registrations to the intratime application.',
        'allowed_parameters': [],
        'free_parameters': True,
        'num_parameters': 2,
        'parameters_description': '<intratime_mail> <intratime_password>'
    },
    var.DISABLE_INTRATIME_INTEGRATION_REQUEST: {
        'description': 'Disable the intratime integration.',
        'allowed_parameters': [],
        'num_parameters': 0
    },
    var.MANAGEMENT_REQUEST: {
        'description': 'Generate temporary credentials to access the administration panel.',
        'allowed_parameters': [],
        'num_parameters': 0
    }
}


def empty_response():
    """Build an empty response with 200 status code"""
    return make_response('', HTTPStatus.OK)


def set_logging():
    """Configure the service and app loggers"""
    # Set service logs (Set only if the app is not run with gunicorn)
    if 'GUNICORN' not in environ:
        service_logger = logging.getLogger('werkzeug')
        service_logger.setLevel(logging.DEBUG if settings.DEBUG_MODE else logging.INFO)
        service_file_handler = logging.FileHandler(join(settings.LOGS_PATH, 'clockzy_service.log'))
        service_logger.addHandler(service_file_handler)

    # Set app logs
    app_logger.setLevel(logging.DEBUG if settings.DEBUG_MODE else logging.INFO)
    formatter = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")
    app_file_handler = logging.FileHandler(join(settings.LOGS_PATH, 'clockzy_app.log'))
    app_file_handler.setFormatter(formatter)
    app_logger.addHandler(app_file_handler)


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
            app_logger.info(lgm.unauthorized_request(request.remote_addr))
            return jsonify({'result': ar.NON_SLACK_REQUEST}), HTTPStatus.UNAUTHORIZED
        elif validation == cd.BAD_SLACK_TIMESTAMP_REQUEST:
            app_logger.info(lgm.bad_timestamp_signature)
            return jsonify({'result': ar.BAD_SLACK_HEADERS_REQUEST}), HTTPStatus.UNAUTHORIZED
        elif validation == cd.BAD_SLACK_SIGNATURE:
            app_logger.info(lgm.bad_slack_signature)
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
            app_logger.info(lgm.missing_slack_request_object('validate_user'))
            return make_response('', HTTPStatus.INTERNAL_SERVER_ERROR)

        user_id = kwargs['slack_request_object'].user_id
        response_url = kwargs['slack_request_object'].response_url

        if not item_exists({'id': user_id}, USER_TABLE):
            send_slack_message('USER_NOT_REGISTERED', response_url)
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
            app_logger.info(lgm.missing_slack_request_object('validate_command_parameters'))
            return make_response('', HTTPStatus.INTERNAL_SERVER_ERROR)

        command = kwargs['slack_request_object'].command
        command_parameters = kwargs['slack_request_object'].command_parameters
        response_url = kwargs['slack_request_object'].response_url

        # Check if it is an expected command
        if command not in ALLOWED_COMMANDS.keys():
            send_slack_message('NOT_ALLOWED_COMMAND', response_url, [command, ALLOWED_COMMANDS.keys()])
            return empty_response()

        # If commands parameters are expected, then check them.
        if ALLOWED_COMMANDS[command]['num_parameters'] > 0:
            command_data = ALLOWED_COMMANDS[command]
            # Check that the number of expected parameters is correct (Extra args wont be processed)
            if len(command_parameters) < command_data['num_parameters']:
                parameters = command_data['allowed_parameters'] if len(command_data['allowed_parameters']) > 0 else \
                    command_data['parameters_description']
                send_slack_message('WRONG_NUM_COMMAND_PARAMETERS', response_url, [command,
                                                                                  command_data['num_parameters'],
                                                                                  parameters])
                return empty_response()

            # Check if the parameter value is correct when it is an enumerated one.
            if not command_data['free_parameters'] and command_parameters[0] not in command_data['allowed_parameters']:
                send_slack_message('WRONG_COMMAND_PARAMETER', response_url, [command,
                                                                             command_data['allowed_parameters']])
                return empty_response()

        return func(*args, **kwargs)

    return wrapper


def command_monitoring(func):
    """Log the command request in the history"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'slack_request_object' not in kwargs:
            app_logger.info(lgm.missing_slack_request_object('command_monitoring'))
            return make_response('', HTTPStatus.INTERNAL_SERVER_ERROR)

        command = kwargs['slack_request_object'].command
        command_parameters = ' '.join(kwargs['slack_request_object'].command_parameters)
        command_history = CommandHistory(kwargs['slack_request_object'].user_id, command, command_parameters)
        command_history.save()

        app_logger.info(lgm.command_monitoring(kwargs['user_data'].user_name, kwargs['user_data'].id,
                                               f"{command} {command_parameters}"))
        return func(*args, **kwargs)

    return wrapper


# ----------------------------------------------------------------------------------------------------------------------
#                                                API ENDPOINTS                                                         #
# ----------------------------------------------------------------------------------------------------------------------


@clockzy_service.route(var.ECHO_REQUEST, methods=['POST'])
def echo():
    """Endpoint to check the current server status"""
    return jsonify({'status': 'alive'}), HTTPStatus.OK


@clockzy_service.route(var.SIGN_UP_REQUEST, methods=['POST'])
@validate_slack_request
def sign_up(slack_request_object):
    """Endpoint to register a new user"""
    # Save the user in the DB
    response_url = slack_request_object.response_url
    user_data = User(slack_request_object.user_id, slack_request_object.user_name)
    result = user_data.save()

    # Get the user profile info (needed for getting the user time zone)
    user_profile_data = slack.get_user_profile_data(user_data.id)
    if user_profile_data[0] != cd.SUCCESS or 'tz' not in user_profile_data[1]:
        app_logger.error(lgm.error_getting_user_profile_info(user_data.user_name, user_data.id))
        send_slack_message('ERROR_GETTING_USER_PROFILE_INFO', response_url)
        return empty_response()

    # Create the objects associated to the user
    user_config = Config(user_data.id, False, user_profile_data[1]['tz'])
    user_config.save()

    # Communicate the result of the user creation operation
    if result == cd.SUCCESS:
        app_logger.info(lgm.user_created(user_data.user_name, user_data.id))
        send_slack_message('ADD_USER_SUCCESS', response_url)
    elif result == cd.ITEM_ALREADY_EXISTS:
        send_slack_message('USER_ALREADY_REGISTERED', response_url)
    else:
        app_logger.error(lgm.error_creating_user(user_data.user_name, user_data.id))
        send_slack_message('ADD_USER_ERROR', response_url)

    return empty_response()


@clockzy_service.route(var.UPDATE_USER_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@command_monitoring
def update_user(slack_request_object, user_data):
    """Endpoint to update the user data, using the slack profile info"""
    response_url = slack_request_object.response_url

    # Get the user profile info (needed for getting the user time zone)
    user_profile_data = slack.get_user_profile_data(user_data.id)
    if user_profile_data[0] != cd.SUCCESS or 'tz' not in user_profile_data[1]:
        app_logger.error(lgm.error_getting_user_profile_info(user_data.user_name, user_data.id))
        send_slack_message('ERROR_GETTING_USER_PROFILE_INFO', response_url)
        return empty_response()

    # Get the user time zone from the database
    user_config = get_config_object(user_data.id)

    # Check if the user data is already updated
    if user_data.user_name == slack_request_object.user_name and user_config.time_zone == user_profile_data[1]['tz']:
        send_slack_message('USER_INFO_ALREADY_UPDATED', response_url)
    else:
        update_ok = True

        # Update the user name if necessary
        if user_data.user_name != slack_request_object.user_name:
            user_data.user_name = slack_request_object.user_name
            if user_data.update() != cd.SUCCESS:
                app_logger.error(lgm.error_updating_user(user_data.user_name, user_data.id, 'user_name'))
                update_ok = False

        # Update the user time zone if necessary
        if user_config.time_zone != user_profile_data[1]['tz']:
            user_config.time_zone = user_profile_data[1]['tz']
            if user_config.update() != cd.SUCCESS:
                app_logger.error(lgm.error_updating_user(user_data.user_name, user_data.id, 'time_zone'))
                update_ok = False

        # Communicate the result
        if update_ok:
            app_logger.info(lgm.success_updating_user(user_data.user_name, user_data.id))
            send_slack_message('UPDATE_USER_SUCCESS', response_url)
        else:
            send_slack_message('UPDATE_USER_ERROR', response_url)

    return empty_response()


@clockzy_service.route(var.DELETE_USER_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@command_monitoring
def delete_user(slack_request_object, user_data):
    """Endpoint to delete a registered user"""
    response_url = slack_request_object.response_url
    result = user_data.delete()

    if result == cd.SUCCESS:
        app_logger.info(lgm.user_deleted(user_data.user_name, user_data.id))
        send_slack_message('DELETE_USER_SUCCESS', response_url)
    else:
        app_logger.error(lgm.error_deleting_user(user_data.user_name, user_data.id))
        send_slack_message('DELETE_USER_ERROR', response_url)

    return empty_response()


@clockzy_service.route(var.CLOCK_REQUEST, methods=['POST'])
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
    user_timezone = get_config_object(user_data.id).time_zone

    # Check if the user can clock that action (it makes sense)
    clock_check = user_can_clock_this_action(user_data.id, action)

    # If the clocking is wrong, then indicate it to the user
    if not clock_check[0]:
        send_slack_message('BAD_CLOCKING_TYPE', response_url, [clock_check[1]])
        return empty_response()

    # If the user has intratime app linked, then register the action in the intratime API.
    intratime_enabled = get_config_object(user_data.id).intratime_integration
    if intratime_enabled:
        user_email = user_data.email
        user_password = crypt.decrypt(user_data.password)
        clocking_status = intratime.clocking(action, user_email, user_password, user_timezone)

        # If the intratime clocking has failed, then display an error message and exit so as not to clock it in clockzy.
        if clocking_status != cd.SUCCESS:
            if clocking_status == cd.INTRATIME_AUTH_ERROR:
                app_logger.info(lgm.error_intratime_auth(user_data.user_name, user_data.id))
                send_slack_message('BAD_CLOCKING_CREDENTIALS', response_url, [var.ENABLE_INTRATIME_INTEGRATION_REQUEST])
            else:
                app_logger.error(lgm.error_intratime_clocking(user_data.user_name, user_data.id, action.upper()))
                send_slack_message('ERROR_CLOCKING_INTRATIME', response_url)

            return empty_response()

    # Save the clock in the DB
    clock = Clock(user_data.id, action, get_current_date_time(user_timezone))
    result = clock.save()

    # Communicate the result of the clocking operation
    if result == cd.SUCCESS:
        send_slack_message('CLOCKING_SUCCESS', response_url, [user_data.id, clock.action, clock.date_time,
                                                              user_data.user_name])
    else:
        if intratime_enabled:
            app_logger.error(lgm.error_clockzy_clocking(user_data.user_name, user_data.id, action.upper()))
            send_slack_message('ERROR_CLOCKING_CLOCKZY_WITH_INTRATIME', response_url)
        else:
            app_logger.error(lgm.error_clockzy_clocking(user_data.user_name, user_data.id, action.upper()))
            send_slack_message('ERROR_CLOCKING_CLOCKZY_WITHOUT_INTRATIME', response_url)

        return empty_response()

    # Update the last registration data from that user
    user_data.last_registration_date = get_current_date_time()
    user_data.update()

    app_logger.error(lgm.success_clockzy_clocking(user_data.user_name, user_data.id, action.upper()))

    return empty_response()


@clockzy_service.route(var.TIME_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
@command_monitoring
def time(slack_request_object, user_data):
    """Endpoint to get the worked time for the specified time range"""
    time_range = slack_request_object.command_parameters[0]
    response_url = slack_request_object.response_url
    user_timezone = get_config_object(user_data.id).time_zone

    # Calculate the worked time
    worked_time = calculate_worked_time(user_data.id, time_range=time_range, timezone=user_timezone)

    # Communicate the result
    send_slack_message('WORKED_TIME', response_url, [time_range, worked_time])

    return empty_response()


@clockzy_service.route(var.TIME_HISTORY_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
@command_monitoring
def time_history(slack_request_object, user_data):
    """Endpoint to get the worked time history for the specified time range"""
    time_range = slack_request_object.command_parameters[0]
    response_url = slack_request_object.response_url
    user_timezone = get_config_object(user_data.id).time_zone

    # Calculate and send the report
    send_slack_message('TIME_HISTORY', response_url, [user_data.id, time_range, user_timezone])

    return empty_response()


@clockzy_service.route(var.CLOCK_HISTORY_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
@command_monitoring
def clock_history(slack_request_object, user_data):
    """Endpoint to get the clock history for the specified time range"""
    time_range = slack_request_object.command_parameters[0]
    response_url = slack_request_object.response_url
    user_timezone = get_config_object(user_data.id).time_zone

    # Calculate and send the report
    send_slack_message('CLOCK_HISTORY', response_url, [user_data.id, time_range, user_timezone])

    return empty_response()


@clockzy_service.route(var.TODAY_INFO_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@command_monitoring
def today_info(slack_request_object, user_data):
    """Endpoint to show the clock history and worked time for today"""
    response_url = slack_request_object.response_url
    user_timezone = get_config_object(user_data.id).time_zone

    # Calculate and send the report
    send_slack_message('TODAY_INFO', response_url, [user_data.id, 'today', user_timezone])

    return empty_response()


@clockzy_service.route(var.COMMAND_HELP_REQUEST, methods=['POST'])
@validate_slack_request
def command_help(slack_request_object):
    """Endpoint to show the available commands of the clockzy app"""
    response_url = slack_request_object.response_url

    send_slack_message('COMMAND_HELP', response_url)

    return empty_response()


@clockzy_service.route(var.ADD_ALIAS_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
@command_monitoring
def add_alias(slack_request_object, user_data):
    """Endpoint to add a new user alias"""
    response_url = slack_request_object.response_url
    user_name = slack_request_object.command_parameters[0]
    alias_name = slack_request_object.command_parameters[1]
    referenced_user_data = get_database_data_from_objects({'user_name': user_name}, USER_TABLE)

    # Check if the specified username exists
    if len(referenced_user_data) == 0:
        send_slack_message('UNDEFINED_USERNAME', response_url, [user_name])
        return empty_response()

    # Check if alias is already registered
    if item_exists({'alias': alias_name}, ALIAS_TABLE):
        send_slack_message('ALIAS_ALREADY_REGISTERED', response_url, [alias_name])
        return empty_response()

    user_id = referenced_user_data[0][0]
    alias = Alias(user_id, alias_name)
    result = alias.save()

    # Communicate the result of the alias creation operation
    if result != cd.SUCCESS:
        app_logger.error(lgm.error_creating_alias(user_data.user_name, user_data.id, alias_name))
        send_slack_message('ERROR_CREATING_ALIAS', response_url)
        return empty_response()

    app_logger.info(lgm.alias_created(user_data.user_name, user_data.id, user_id, alias_name))
    send_slack_message('ADD_ALIAS_SUCCESS', response_url, [alias_name, user_name])

    return empty_response()


@clockzy_service.route(var.GET_ALIASES_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@command_monitoring
def get_aliases(slack_request_object, user_data):
    """Endpoint to show all user aliases"""
    response_url = slack_request_object.response_url

    send_slack_message('GET_ALIASES', response_url)

    return empty_response()


@clockzy_service.route(var.CHECK_USER_STATUS_REQUEST, methods=['POST'])
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
        send_slack_message('BAD_USERNAME_OR_ALIAS', response_url, [user_name])
        return empty_response()

    # Get the user id
    user_data = get_database_data_from_objects({'user_name': user_name}, USER_TABLE)
    if len(user_data) == 0:
        user_id = get_database_data_from_objects({'alias': user_name}, ALIAS_TABLE)[0][1]
    else:
        user_id = user_data[0][0]

    send_slack_message('USER_STATUS', response_url, [user_id, user_name])

    return empty_response()


@clockzy_service.route(var.ENABLE_INTRATIME_INTEGRATION_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@validate_command_parameters
def enable_intratime_integration(slack_request_object, user_data):
    """Enable the intratime integration. All clockings will be save in intratime too."""
    response_url = slack_request_object.response_url
    intratime_user = slack_request_object.command_parameters[0]
    intratime_password = slack_request_object.command_parameters[1]

    # Validate the entered intratime credentials
    if not intratime.check_user_credentials(intratime_user, intratime_password):
        send_slack_message('BAD_INTRATIME_CREDENTIALS', response_url)
        return empty_response()

    # Add the intratime credentials to the user data in the DB
    user_data.email = intratime_user
    user_data.password = crypt.encrypt(intratime_password)
    if user_data.update() != cd.SUCCESS:
        app_logger.error(lgm.error_updating_user_credentials(user_data.user_name, user_data.id))
        send_slack_message('ERROR_UPDATING_USER_CREDENTIALS', response_url)
        return empty_response()

    # Update the user configuration and set the intratime integration to True
    user_config = get_config_object(user_data.id)
    user_config.intratime_integration = True
    user_config.update()

    if not get_config_object(user_data.id).intratime_integration:
        app_logger.error(lgm.error_updating_user_configuration(user_data.user_name, user_data.id))
        send_slack_message('ERROR_UPDATING_USER_CONFIGURATION', response_url)
        return empty_response()

    app_logger.info(lgm.success_enabling_intratime_sync(user_data.user_name, user_data.id))
    send_slack_message('ENABLE_INTRATIME_SUCCESS', response_url)

    return empty_response()


@clockzy_service.route(var.DISABLE_INTRATIME_INTEGRATION_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@command_monitoring
def disable_intratime_integration(slack_request_object, user_data):
    """Disable the intratime integration."""
    response_url = slack_request_object.response_url

    # Check that the user has the integration activated
    if not get_config_object(user_data.id).intratime_integration:
        send_slack_message('INTRATIME_ALREADY_DISABLED', response_url)
        return empty_response()

    # Disable the integration in the config data
    user_config = get_config_object(user_data.id)
    user_config.intratime_integration = False

    if user_config.update() != cd.SUCCESS:
        app_logger.error(lgm.error_disabling_intratime_sync(user_data.user_name, user_data.id))
        send_slack_message('ERROR_DISABLING_INTRATIME', response_url)
        return empty_response()

    # Clean the email and password data
    user_data.email = None
    user_data.password = None
    user_data.update()

    # Send the success message
    app_logger.error(lgm.success_disabling_intratime_sync(user_data.user_name, user_data.id))
    send_slack_message('DISABLE_INTRATIME_SUCCESS', response_url)

    return empty_response()


@clockzy_service.route(var.MANAGEMENT_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
@command_monitoring
def get_management_credentials(slack_request_object, user_data):
    """Generate temporary credentials to access the administration panel"""
    CREDENTIAL_TIME_EXPIRATION = 60
    response_url = slack_request_object.response_url

    # Generate new temporary credentials
    new_temporary_credentials = TemporaryCredentials(user_data.id, crypt.generate_random_temporary_password())

    # Save or update the new credentials in the DB
    if item_exists({'user_id': user_data.id}, TEMPORARY_CREDENTIALS_TABLE):
        new_temporary_credentials.update()
    else:
        new_temporary_credentials.save()

    # Send the slack message
    send_slack_message('TEMPORARY_CREDENTIALS', response_url, [new_temporary_credentials.user_id,
                                                               new_temporary_credentials.password,
                                                               CREDENTIAL_TIME_EXPIRATION])
    return empty_response()


# Run this tasks outside the main because gunicorn will not run that main (See https://stackoverflow.com/a/26579510)
# Set app logger
set_logging()

# Check the database conection
database_healthcheck.main()

# Create and initialize the clockzy DB if does not exist.
initialize_database.main()


if __name__ == '__main__':
    # Run clockzy service
    clockzy_service.run(host=settings.SLACK_SERVICE_HOST, port=settings.SLACK_SERVICE_PORT, debug=False)
