from flask import Flask, request, render_template, make_response, redirect, url_for, session
from functools import wraps
from http import HTTPStatus

import controller
import views
from clockzy.lib.handlers.codes import SUCCESS


app = Flask(__name__)
app.secret_key = "super secret key"


def user_logged(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return views.login()

        return func(*args, **kwargs)

    return wrapper


@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    return views.login()


@app.route('/check-credentials', methods=['GET', 'POST'])
def check_credentials():
    if not 'user_id' in request.form or not 'password' in request.form:
        return redirect(url_for('login'))

    user_id = request.form['user_id']
    password = request.form['password']

    validation_ok, error_message = controller.validate_credentials(user_id, password)

    if not validation_ok:
        return views.login(error_message)

    session['logged_in'] = True
    session['user_id'] = user_id

    return redirect(url_for('index'))


@app.route('/index', methods=['GET', 'POST'])
@user_logged
def index():
    clocking_data = controller.get_clocking_data(session['user_id'])
    return views.index(session['user_id'], clocking_data)


@app.route('/logout', methods=['GET', 'POST'])
@user_logged
def logout():
    session.pop('logged_in')
    session.pop('user_id')
    return views.login()

# def validate_clocking_data


@app.route('/update_clocking_data', methods=['POST'])
def update_clocking_data():
    request_data = request.get_json()

    update_result = controller.update_clocking_data(request_data)

    if update_result == SUCCESS:
        return make_response('', HTTPStatus.OK)
    else:
         return make_response('', HTTPStatus.BAD_REQUEST)

@app.route('/add_clocking_data', methods=['POST'])
def add_clocking_data():
    request_data = request.get_json()

    add_result = controller.add_clocking_data(request_data)

    if add_result == SUCCESS:
        return make_response('', HTTPStatus.OK)
    else:
         return make_response('', HTTPStatus.BAD_REQUEST)

@app.route('/delete_clocking_data', methods=['POST'])
def delete_clocking_data():
    request_data = request.get_json()

    delete_result = controller.delete_clocking_data(request_data)

    if delete_result == SUCCESS:
        return make_response('', HTTPStatus.OK)
    else:
         return make_response('', HTTPStatus.BAD_REQUEST)


if __name__ == '__main__':
    app.run(host='localhost', port=7000, debug=True)
