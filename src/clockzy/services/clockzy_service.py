from flask import Flask, jsonify, request, make_response
from http import HTTPStatus
from functools import wraps

from clockzy.lib.global_vars.slack_vars import ECHO_REQUEST
from clockzy.lib.messages import api_responses
from clockzy.lib.models.slack_request import SlackRequest
from clockzy.lib.handlers.codes import BAD_SLACK_SIGNATURE, BAD_SLACK_TIMESTAMP_REQUEST, NON_SLACK_REQUEST
from clockzy.lib.slack import slack
from clockzy.config import settings


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

        if validation == NON_SLACK_REQUEST:
            return jsonify({'result': api_responses.NON_SLACK_REQUEST}), HTTPStatus.UNAUTHORIZED
        elif validation == BAD_SLACK_TIMESTAMP_REQUEST:
            return jsonify({'result': api_responses.BAD_SLACK_HEADERS_REQUEST}), HTTPStatus.UNAUTHORIZED
        elif validation == BAD_SLACK_SIGNATURE:
            return jsonify({'result': api_responses.BAD_SLACK_SIGNATURE}), HTTPStatus.UNAUTHORIZED

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


if __name__ == '__main__':
    app.run(host=settings.SLACK_SERVICE_HOST, port=settings.SLACK_SERVICE_PORT, debug=settings.DEBUG_MODE)
