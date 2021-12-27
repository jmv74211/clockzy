from flask import Flask, jsonify, request, make_response
from http import HTTPStatus
from functools import wraps

from clockzy.lib.db.db_schema import USER_TABLE
from clockzy.lib.global_vars import slack_vars as var
from clockzy.lib.messages import api_responses as ar
from clockzy.lib.models.slack_request import SlackRequest
from clockzy.lib.models.user import User
from clockzy.lib.handlers import codes as cd
from clockzy.lib.slack import slack_core as slack
from clockzy.config import settings
from clockzy.lib.slack import slack_messages as msg
from clockzy.lib.db import db_schema as dbs
from clockzy.lib.db.database_interface import item_exists, get_user_object


app = Flask(__name__)


def empty_response():
    """Build an empty response with 200 status code"""
    return make_response('', HTTPStatus.OK)


def validate_slack_request(func):
    """Decorator function to validate that the request comes from the slack app and from no other source."""
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


@app.route(var.ECHO_REQUEST, methods=['POST'])
@validate_slack_request
@validate_user
def echo(slack_request_object, user_data):
    """Endpoint to check the current server status

    - Input_data: {}
    - Output_data: {'result': 'Alive'}
    """
    return empty_response()


@app.route(var.ADD_USER_REQUEST, methods=['POST'])
@validate_slack_request
def sign_up(slack_request_object):
    """ Endpoint to register a new user"""
    user = User(slack_request_object.user_id, slack_request_object.user_name)
    result = user.save()

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
def delete_user(slack_request_object, user_data):
    """Endpoint to delete a registered user"""
    result = user_data.delete()

    if result == cd.SUCCESS:
        slack.post_ephemeral_response_message(msg.DELETE_USER_SUCCESS, slack_request_object.response_url)
    else:
        slack.post_ephemeral_response_message(msg.DELETE_USER_ERROR, slack_request_object.response_url)

    return empty_response()


if __name__ == '__main__':
    app.run(host=settings.SLACK_SERVICE_HOST, port=settings.SLACK_SERVICE_PORT, debug=settings.DEBUG_MODE)
