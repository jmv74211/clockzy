from flask import Flask, request, jsonify, make_response, redirect, url_for, session
from functools import wraps
from http import HTTPStatus

import controller
import views
from clockzy.lib.handlers.codes import SUCCESS
from clockzy.config import settings


app = Flask(__name__)
app.secret_key = settings.WEB_APP_SECRET_KEY


def user_logged(func):
    """Wrapper to check if the user is logged"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return views.login()

        return func(*args, **kwargs)

    return wrapper


@app.errorhandler(404)
def page_not_found(error):
    """Redirect to the index page if the requested URI is not found"""
    return redirect(url_for('index'))


@app.route('/login', methods=['GET'])
def login():
    """Login view"""
    return views.login()


@app.route('/check_credentials', methods=['POST'])
def check_credentials():
    """Credentials validation proccess"""
    if 'user_id' not in request.form or 'password' not in request.form:
        return redirect(url_for('login'))

    user_id = request.form['user_id']
    password = request.form['password']

    validation_ok, error_message = controller.validate_credentials(user_id, password)

    if not validation_ok:
        return views.login(error_message)

    session['logged_in'] = True
    session['user_id'] = user_id

    return redirect(url_for('index'))


@app.route('/index', methods=['GET'])
@user_logged
def index():
    """Index view"""
    clocking_data = controller.get_clocking_data(session['user_id'])

    notification = session['notification'] if 'notification' in session else None

    if 'notification' in session:
        session.pop('notification')

    return views.index(session['user_id'], clocking_data, notification)


@app.route('/logout', methods=['GET'])
@user_logged
def logout():
    """Logout process"""
    session.clear()
    return views.login()


@app.route('/clocking_data', methods=['PUT'])
@user_logged
def update_clocking_data():
    """Update clocking data process"""
    request_data = request.get_json()
    result_status, result_message = controller.update_clocking_data(request_data)

    if result_status == SUCCESS:
        session['notification'] = 'The clocking data has been updated successfully.'

    return make_response(result_message, HTTPStatus.OK) if result_status == SUCCESS else \
        make_response(result_message, HTTPStatus.BAD_REQUEST)


@app.route('/clocking_data', methods=['POST'])
@user_logged
def add_clocking_data():
    """Add clocking data endpoint"""
    request_data = request.get_json()

    result_status, result_message = controller.add_clocking_data(request_data)

    if result_status == SUCCESS:
        session['notification'] = 'The clocking data has been added successfully.'

    return make_response(result_message, HTTPStatus.OK) if result_status == SUCCESS else \
        make_response(result_message, HTTPStatus.BAD_REQUEST)


@app.route('/clocking_data', methods=['DELETE'])
@user_logged
def delete_clocking_data():
    """Delete clocking data endpoint"""
    request_data = request.get_json()

    result_status, result_message = controller.delete_clocking_data(request_data)

    if result_status == SUCCESS:
        session['notification'] = 'The clocking data has been deleted successfully.'

    return make_response(result_message, HTTPStatus.OK) if result_status == SUCCESS else \
        make_response(result_message, HTTPStatus.BAD_REQUEST)


@app.route('/get_query_data', methods=['POST'])
@user_logged
def get_query_data():
    """Get the clocking table view according to the specified parameters"""
    request_data = request.get_json()

    if 'search' not in request_data:
        make_response('Error: Need search data parameter', HTTPStatus.BAD_REQUEST)

    clock_data = controller.get_filtered_clock_user_data(session['user_id'], request_data['search'])

    table_view = views.get_clocking_table(clock_data).replace('&#39;', "'")

    return jsonify({'data': table_view}), HTTPStatus.OK


if __name__ == '__main__':
    app.run(host=settings.WEB_APP_SERVICE_HOST, port=settings.WEB_APP_SERVICE_PORT, debug=False)
