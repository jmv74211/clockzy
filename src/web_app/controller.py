from datetime import datetime

from clockzy.lib.db.database_interface import get_database_data_from_objects, get_clock_object, get_filtered_clock_data
from clockzy.lib.utils.time import get_time_difference, add_seconds_to_datetime
from clockzy.lib.models.clock import Clock
from clockzy.lib.db.db_schema import TEMPORARY_CREDENTIALS_TABLE, CLOCK_TABLE
from clockzy.lib.global_vars import MANAGEMENT_REQUEST
from clockzy.lib.handlers.codes import SUCCESS, GENERIC_ERROR
from clockzy.lib.utils import time


ALLOWED_ACTIONS = ['in', 'pause', 'return', 'out']
DATE_TIME_FORMAT = 'YYYY-MM-DD HH:MM:SS'


def _raw_list(_list, upper=False):
    """Convert a python list to a custom str list.

    Args:
        _list (list): String list.
        upper (boolean): True for upperCase the list items, False otherwise.

    Returns:
        str: List converted to string with custom format.
    """
    output = ''

    for item in _list:
        output += f"{item.upper()} " if upper else f"{item} "

    return output.strip()


def validate_credentials(user_id, password):
    """Check if the user credentials are valid.

    Args:
        user_id (str): User ID.
        password (str): User password.

    Returns:
        (boolean, str): Credentials validation result and error message in case that credentials are not correct.
    """
    user_data = get_database_data_from_objects({'user_id': user_id}, TEMPORARY_CREDENTIALS_TABLE)

    if len(user_data) == 0:
        return False, f"The user {user_id} does not exist, or does not have credentials set up for the clockzy web" \
                      f" app. Please run {MANAGEMENT_REQUEST} in the clockzy slack application to create them."

    user_password = user_data[0][1]
    password_expiration_time = user_data[0][2]

    if user_password != password:
        return False, f"Your password is not correct."

    if time.date_time_has_expired(password_expiration_time):
        return False, f"Your password has expired. Please run {MANAGEMENT_REQUEST} in the clockzy slack application " \
                      'to create a new one.'

    return True, ''


def get_clocking_data(user_id):
    """Get all the clocking data from a specific user.

    Args:
        user_id (str): User ID.

    Returns:
        list(list(str)): Matrix with clocking data. [[clocking_id, date_time, action], ...]
    """
    return [[str(item[0]), datetime.strftime(item[3], '%Y-%m-%d %H:%M:%S'), item[2].upper()] for item in
            get_database_data_from_objects({'user_id': user_id}, CLOCK_TABLE)]


def update_clocking_data(clocking_data):
    """Update a clocking data in the DB. Required fields: 'user_id', 'clock_id', 'action', 'date_time'.

    Args:
        clocking_data (dict): New clocking data.

    Returns:
        (int, str): Result code and result operation message.
    """
    required_fields = ['user_id', 'clock_id', 'action', 'date_time']

    for field in required_fields:
        if field not in clocking_data:
            return GENERIC_ERROR, f"Missing data. Required fields = {required_fields}"

    if clocking_data['action'].lower() not in ALLOWED_ACTIONS:
        return GENERIC_ERROR, f"Your action {clocking_data['action']} is not allowed.<br/>\n" \
            f"Allowed ones: {_raw_list(ALLOWED_ACTIONS, True)}"

    if not time.validate_date_time_format(clocking_data['date_time']):
        return GENERIC_ERROR, f"Your date_time {clocking_data['date_time']} format is not he expected one. " \
                              f"<br/>\nExpected {DATE_TIME_FORMAT}"

    if not time.check_if_date_time_belongs_to_current_year(clocking_data['date_time']):
        return GENERIC_ERROR, f"You can only edit clockings from the current year."

    if time.check_if_future_date_time(clocking_data['date_time']):
        return GENERIC_ERROR, f"You cannot use datetimes that belong to the future."

    clock_object = get_clock_object(clock_id=clocking_data['clock_id'])

    if clock_object is None:
        return GENERIC_ERROR, f"No clocking ID {clocking_data['clock_id']} exists"

    if clocking_data['user_id'] != clock_object.user_id:
        return GENERIC_ERROR, f"The clocking ID {clocking_data['clock_id']} does not belong to your user"

    # Get the time difference between local server datetime and clocking datetime
    time_difference = get_time_difference(clock_object.date_time, clock_object.local_date_time)

    # Update the clocking object data
    clock_object.date_time = clocking_data['date_time']
    clock_object.action = clocking_data['action']
    clock_object.local_date_time = add_seconds_to_datetime(clocking_data['date_time'], time_difference)

    update_result = clock_object.update()

    if update_result != SUCCESS:
        return GENERIC_ERROR, f"Error ({update_result}) when updating a clocking data"

    return SUCCESS, 'The clocking data has been updated successfully'


def add_clocking_data(clocking_data):
    """Add new clocking data to the DB. Required fields: 'user_id', 'action', 'date_time'.

    Args:
        clocking_data (dict): New clocking data.

    Returns:
        (int, str): Result code and result operation message.
    """
    required_fields = ['user_id', 'action', 'date_time']

    for field in required_fields:
        if field not in clocking_data:
            return GENERIC_ERROR, f"Missing data. Required fields = {required_fields}"

    if clocking_data['action'].lower() not in ALLOWED_ACTIONS:
        return GENERIC_ERROR, f"Your action {clocking_data['action']} is not allowed.<br/>\n" \
            f"Allowed ones: {_raw_list(ALLOWED_ACTIONS, True)}"

    if not time.validate_date_time_format(clocking_data['date_time']):
        return GENERIC_ERROR, f"Your date_time {clocking_data['date_time']} format is not he expected one. " \
                              f"<br/>\nExpected {DATE_TIME_FORMAT}"

    if not time.check_if_date_time_belongs_to_current_year(clocking_data['date_time']):
        return GENERIC_ERROR, f"You can only add clockings from the current year."

    if time.check_if_future_date_time(clocking_data['date_time']):
        return GENERIC_ERROR, f"You cannot use datetimes that belong to the future."

    clock_object = Clock(clocking_data['user_id'], clocking_data['action'].lower(), clocking_data['date_time'])
    add_result = clock_object.save()

    if add_result != SUCCESS:
        return GENERIC_ERROR, f"Error ({add_result}) when adding a clocking data"

    return SUCCESS, 'The clocking data has been added successfully'


def delete_clocking_data(clocking_data):
    """Delete clocking data from the DB.

    Args:
        clocking_data (dict): Clocking data to delete. Required fields: 'user_id', 'clock_id'.

    Returns:
        (int, str): Result code and result operation message.
    """
    required_fields = ['user_id', 'clock_id']

    for field in required_fields:
        if field not in clocking_data:
            return GENERIC_ERROR, f"Missing data. Required fields = {required_fields}"

    clock_object = get_clock_object(clock_id=clocking_data['clock_id'])

    if clock_object is None:
        return GENERIC_ERROR, f"No clocking ID {clocking_data['clock_id']} exists"

    if clocking_data['user_id'] != clock_object.user_id:
        return GENERIC_ERROR, f"The clocking ID {clocking_data['clock_id']} does not belong to your user"

    delete_result = clock_object.delete()

    if delete_result != SUCCESS:
        return GENERIC_ERROR, f"Error ({delete_result}) when deleting a clocking data"

    return SUCCESS, 'The clocking data has been deleted successfully'


def get_filtered_clock_user_data(user_id, search=''):
    """Get the clocking data filtered by string match for a specific user.

    Args:
        user_id (str): User ID.
        search (str): String to filter the clocking data.

    Returns:
        list(list(str)): Clocking data filtered.
    """
    clock_data = get_filtered_clock_data(user_id, f"%{search}%")

    if clock_data is None:
        return []

    clock_data_filtered = [[str(item.id), datetime.strftime(item.date_time, '%Y-%m-%d %H:%M:%S'),
                           item.action.upper()] for item in clock_data]

    return clock_data_filtered
