import logging
from os.path import join
from os import environ
from flask import Flask, request, jsonify, make_response, redirect, url_for, session
from functools import wraps
from http import HTTPStatus

import controller
import views
from clockzy.lib.handlers.codes import SUCCESS
from clockzy.config import settings
from clockzy.lib.db.database_interface import get_user_object
from clockzy.lib.messages import logger_messages as lgm


web_app = Flask(__name__)
web_app.secret_key = settings.WEB_APP_SECRET_KEY
web_app_logger = logging.getLogger('clockzy')


def set_logging():
    """Configure the service and app loggers"""
    # Set service logs
    if 'GUNICORN' not in environ:
        service_logger = logging.getLogger('werkzeug')
        service_logger.setLevel(logging.DEBUG if settings.DEBUG_MODE else logging.INFO)
        service_file_handler = logging.FileHandler(join(settings.LOGS_PATH, 'clockzy_web_service.log'))
        service_logger.addHandler(service_file_handler)

    # Set app logs
    web_app_logger.setLevel(logging.DEBUG if settings.DEBUG_MODE else logging.INFO)
    formatter = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")
    web_app_file_handler = logging.FileHandler(join(settings.LOGS_PATH, 'clockzy_web_app.log'))
    web_app_file_handler.setFormatter(formatter)
    web_app_logger.addHandler(web_app_file_handler)


def user_logged(func):
    """Wrapper to check if the user is logged"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return views.login()

        return func(*args, **kwargs)

    return wrapper


@web_app.errorhandler(404)
def page_not_found(error):
    """Redirect to the index page if the requested URI is not found"""
    return redirect(url_for('index'))


@web_app.route('/login', methods=['GET'])
def login():
    """Login view"""
    return views.login()


@web_app.route('/check_credentials', methods=['POST'])
def check_credentials():
    """Credentials validation proccess"""
    if 'user_id' not in request.form or 'password' not in request.form:
        return redirect(url_for('login'))

    user_id = request.form['user_id']
    password = request.form['password']

    validation_data = controller.validate_credentials(user_id, password)

    if not validation_data['result']:
        return views.login(validation_data['error_message'])

    session['logged_in'] = True
    session['user_id'] = user_id
    session['user_name'] = get_user_object(user_id).user_name

    web_app_logger.info(lgm.user_logged(session['user_name'], user_id))

    return redirect(url_for('index'))


@web_app.route('/index', methods=['GET'])
@user_logged
def index():
    """Index view"""
    clocking_data = controller.get_clocking_data(session['user_id'])

    notification = session['notification'] if 'notification' in session else None

    if 'notification' in session:
        session.pop('notification')

    return views.index(session['user_id'], clocking_data, notification)


@web_app.route('/logout', methods=['GET'])
@user_logged
def logout():
    """Logout process"""
    session.clear()
    return views.login()


@web_app.route('/clocking_data', methods=['PUT'])
@user_logged
def update_clocking_data():
    """Update clocking data process"""
    request_data = request.get_json()
    operation_data = controller.update_clocking_data(request_data)

    if operation_data['result'] == SUCCESS:
        session['notification'] = 'The clocking data has been updated successfully.'
        clocking_data = operation_data['data']
        web_app_logger.info(lgm.success_updating_clocking_data(session['user_name'], session['user_id'],
                                                               clocking_data['clock_id'], clocking_data['action'],
                                                               clocking_data['date_time']))

    return make_response(operation_data['message'], HTTPStatus.OK) if operation_data['result'] == SUCCESS else \
        make_response(operation_data['message'], HTTPStatus.BAD_REQUEST)


@web_app.route('/clocking_data', methods=['POST'])
@user_logged
def add_clocking_data():
    """Add clocking data endpoint"""
    request_data = request.get_json()
    operation_data = controller.add_clocking_data(request_data)

    if operation_data['result'] == SUCCESS:
        session['notification'] = 'The clocking data has been added successfully.'
        clocking_data = operation_data['data']
        web_app_logger.info(lgm.success_adding_clocking_data(session['user_name'], session['user_id'],
                                                             clocking_data['action'], clocking_data['date_time']))

    return make_response(operation_data['message'], HTTPStatus.OK) if operation_data['result'] == SUCCESS else \
        make_response(operation_data['message'], HTTPStatus.BAD_REQUEST)


@web_app.route('/clocking_data', methods=['DELETE'])
@user_logged
def delete_clocking_data():
    """Delete clocking data endpoint"""
    request_data = request.get_json()
    operation_data = controller.delete_clocking_data(request_data)

    if operation_data['result'] == SUCCESS:
        session['notification'] = 'The clocking data has been deleted successfully.'
        web_app_logger.info(lgm.success_deleting_clocking_data(session['user_name'], session['user_id'],
                                                               operation_data['data']['clock_id']))

    return make_response(operation_data['message'], HTTPStatus.OK) if operation_data['result'] == SUCCESS else \
        make_response(operation_data['message'], HTTPStatus.BAD_REQUEST)


@web_app.route('/get_query_data', methods=['POST'])
@user_logged
def get_query_data():
    """Get the clocking table view according to the specified parameters"""
    request_data = request.get_json()

    if 'search' not in request_data:
        make_response('Error: Need search data parameter', HTTPStatus.BAD_REQUEST)

    clock_data = controller.get_filtered_clock_user_data(session['user_id'], request_data['search'])

    table_view = views.get_clocking_table(clock_data).replace('&#39;', "'")

    return jsonify({'data': table_view}), HTTPStatus.OK


# Run this tasks outside the main because gunicorn will not run that main (See https://stackoverflow.com/a/26579510)
# Set app logger
set_logging()


if __name__ == '__main__':
    web_app.run(host=settings.WEB_APP_SERVICE_HOST, port=settings.WEB_APP_SERVICE_PORT, debug=False)
