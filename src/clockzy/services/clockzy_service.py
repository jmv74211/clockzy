import hmac
import hashlib
from flask import Flask, jsonify, request, make_response
from http import HTTPStatus
from functools import wraps

from clockzy.lib.global_vars.slack_vars import ECHO_REQUEST
from clockzy.lib.messages import api_responses
from clockzy.config import settings


app = Flask(__name__)


def empty_response():
    """Build an empty response with 200 status code"""
    return make_response('', HTTPStatus.OK)


def validate_slack_request(func):
    """Decorator function to validate that the request comes from the slack app and from no other source."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'X-Slack-Signature' not in request.headers or 'X-Slack-Request-Timestamp' not in request.headers:
            return jsonify({'result': api_responses.BAD_SLACK_HEADERS_REQUEST}), HTTPStatus.BAD_REQUEST

        request_signature = request.headers['X-Slack-Signature']
        request_timestamp = int(request.headers['X-Slack-Request-Timestamp'])
        request_body = request.get_data().decode('utf-8')

        # Verify that the request is not prior to 1 minute (Avoid replay attacks)
        if int(time.time() - request_timestamp) > 60:
            return jsonify({'result': api_responses.BAD_SLACK_TIMESTAMP_REQUEST}), HTTPStatus.BAD_REQUEST

        sign_basestring = f"v0:{request_timestamp}:{request_body}"
        signature = hmac.new(bytes(settings.SLACK_APP_SIGNATURE, 'utf-8'), bytes(sign_basestring, 'utf-8'),
                             digestmod=hashlib.sha256).hexdigest()
        signature_check = f"v0={signature}"

        # Validate request signature
        if not hmac.compare_digest(signature_check, request_signature):
            return jsonify({'result': api_responses.NON_SLACK_REQUEST}), HTTPStatus.UNAUTHORIZED

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
