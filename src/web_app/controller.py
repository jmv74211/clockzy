from datetime import datetime

from clockzy.lib.db.database_interface import get_database_data_from_objects, get_clock_object
from clockzy.lib.utils.time import get_time_difference, add_seconds_to_datetime
from clockzy.lib.models.clock import Clock
from clockzy.lib.db.db_schema import TEMPORARY_CREDENTIALS_TABLE, CLOCK_TABLE
from clockzy.lib.global_vars import MANAGEMENT_REQUEST
from clockzy.lib.utils.time import date_time_has_expired


def validate_credentials(user_id, password):
    user_data = get_database_data_from_objects({'user_id': user_id}, TEMPORARY_CREDENTIALS_TABLE)

    if len(user_data) == 0:
        return False, f"The user {user_id} does not exist, or does not have credentials set up for the clockzy web" \
                      f" app. Please run {MANAGEMENT_REQUEST} in the clockzy slack application to create them."

    user_password = user_data[0][1]
    password_expiration_time = user_data[0][2]

    if user_password != password:
        return False, f"Your password is not correct."

    if date_time_has_expired(password_expiration_time):
        return False, f"Your password has expired. Please run {MANAGEMENT_REQUEST} in the clockzy slack application " \
                      'to create a new one.'

    return True, ''


def get_clocking_data(user_id):
    return [[str(item[0]), datetime.strftime(item[3], '%Y-%m-%d %H:%M:%S'), item[2].upper()] for item in \
        get_database_data_from_objects({'user_id': user_id}, CLOCK_TABLE)]


def update_clocking_data(clocking_data):
    clock_object = get_clock_object(clock_id=clocking_data['id'])

    if clock_object is None:
        return None

    # Get the time difference between local server datetime and clocking datetime
    time_difference = get_time_difference(clock_object.date_time, clock_object.local_date_time)

    # Update the clocking object data
    clock_object.date_time = clocking_data['date_time']
    clock_object.action = clocking_data['action']
    clock_object.local_date_time = add_seconds_to_datetime(clocking_data['date_time'], time_difference)

    update_result = clock_object.update()

    return update_result


def add_clocking_data(clocking_data):
    clock_object = Clock(clocking_data['user_id'], clocking_data['action'], clocking_data['date_time'])
    add_result = clock_object.save()

    return add_result


def delete_clocking_data(clocking_data):
    clock_object = get_clock_object(clock_id=clocking_data['clock_id'])

    if clock_object is None:
        return None

    if clocking_data['user_id'] != clock_object.user_id:
        return None

    delete_result = clock_object.delete()

    return delete_result
