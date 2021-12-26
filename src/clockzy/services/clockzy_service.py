from flask import Flask, jsonify, request, make_response
from http import HTTPStatus
from functools import wraps

from clockzy.lib.global_vars.slack_vars import ECHO_REQUEST, ADD_USER_REQUEST
from clockzy.lib.messages import api_responses as ar
from clockzy.lib.models.slack_request import SlackRequest
from clockzy.lib.models.user import User
from clockzy.lib.handlers import codes as cd
from clockzy.lib.slack import slack_core as slack
from clockzy.config import settings
from clockzy.lib.slack import slack_messages as msg
from clockzy.lib.db import db_schema as dbs


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


@app.route(ECHO_REQUEST, methods=['GET'])
@validate_slack_request
def echo():
    """Endpoint to check the current server status

    - Input_data: {}
    - Output_data: {'result': 'Alive'}
    """
    return jsonify({'result': 'ALIVE'})


@app.route(ADD_USER_REQUEST, methods=['POST'])
@validate_slack_request
def sign_up(slack_request_object):
    """
    Description: Endpoint register a new user

    Input_data: b'token=x&team_id=x&team_domain=x&channel_id=x&channel_name=x&user_id=x&user_name=x&
                  command=%2Fsign_up&text=&api_app_id=x&response_url=x&trigger_id=x'

    Output_data: {}, 200
    """
    user = User(slack_request_object.user_id, slack_request_object.user_name)
    result = user.save()

    if result == cd.SUCCESS:
        slack.post_ephemeral_response_message(msg.ADD_USER_SUCCESS, slack_request_object.response_url)
    elif result == cd.ITEM_ALREADY_EXISTS:
        slack.post_ephemeral_response_message(msg.USER_ALREADY_REGISTERED, slack_request_object.response_url)
    else:
        slack.post_ephemeral_response_message(msg.ADD_USER_ERROR, slack_request_object.response_url)

    return empty_response()


if __name__ == '__main__':
    app.run(host=settings.SLACK_SERVICE_HOST, port=settings.SLACK_SERVICE_PORT, debug=settings.DEBUG_MODE)
