from flask import render_template

def login(error_message=None):
    if error_message:
        return render_template('login.html', error=error_message)
    else:
        return render_template('login.html')


def index():
    return render_template('index.html')
