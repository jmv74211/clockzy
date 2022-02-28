from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from functools import wraps

import controller
import views

app = Flask(__name__)
app.secret_key = "super secret key"


def user_logged(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return views.login()

        return func(*args, **kwargs)

    return wrapper


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
    return views.index()


if __name__ == '__main__':
    app.run(host='localhost', port=7000, debug=True)
