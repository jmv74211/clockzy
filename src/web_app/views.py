from flask import render_template


def login(error_message=None):
    """Login view.

    Args:
        error_message (str): Error message to show when the login has failed.

    Returns:
        str: View HTML code.
    """
    if error_message:
        return render_template('login.html', error=error_message)
    else:
        return render_template('login.html')


def index(user_id, clocking_data=[], notification=None):
    """Index view.

    Args:
        user_id (str): User ID that has been logged in.
        clocking_data (list(list(str))): Clocking data to show in the clocking table.
        notification (str): Notification to show if exist.

    Returns:
        str: View HTML code.
    """
    return render_template('index.html', user_id=user_id, clocking_data=clocking_data, notification=notification)


def get_clocking_table(clock_data):
    """Clocking table view. Used to build the clocking table according to a specified query parameters.

    Args:
        clock_data (list(list(str))): All clocking data to show in the clocking table view.

    Returns:
        str: View HTML code.
    """
    return render_template('clock_table_data.html', clocking_data=clock_data)
