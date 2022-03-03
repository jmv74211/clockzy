from flask import render_template

def login(error_message=None):
    if error_message:
        return render_template('login.html', error=error_message)
    else:
        return render_template('login.html')


def index(user_id, clocking_data = []):
    return render_template('index.html', user_id=user_id, clocking_data=clocking_data)
