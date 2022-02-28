from clockzy.lib.db.database_interface import get_database_data_from_objects
from clockzy.lib.db.db_schema import TEMPORARY_CREDENTIALS_TABLE
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
