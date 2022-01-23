from clockzy.lib.utils.time import get_current_date_time
from clockzy.lib.models.user import User
from clockzy.lib.db.database_interface import get_database_data_from_objects
from clockzy.lib.db.db_schema import USER_TABLE


# User with intratime integration
intratime_user_parameters = {'id': 'test_user_1', 'user_name': 'test_user_1', 'password': 'test_password',
                             'email': 'test_email'}
# User without intratime integration
no_intratime_user_parameters = {'id': 'test_user_2', 'user_name': 'test_user_2'}
clock_parameters = {'user_id': intratime_user_parameters['id'], 'action': 'IN', 'date_time': get_current_date_time()}
command_history_parameters = {'user_id': intratime_user_parameters['id'], 'command': '/time', 'parameters': 'today',
                              'date_time': get_current_date_time()}
config_parameters = {'user_id': intratime_user_parameters['id'], 'intratime_integration': False,
                     'time_zone': 'Europe/Madrid'}
alias_parameters = {'user_id': intratime_user_parameters['id'], 'alias': 'test'}


def clean_test_data():
    """Clean all test data from the DB"""
    # Get the User objects and automatically delete all their information from all tables on CASCADE
    intratime_user_data = get_database_data_from_objects({'id': intratime_user_parameters['id']}, USER_TABLE)
    normal_user_data = get_database_data_from_objects({'id': no_intratime_user_parameters['id']}, USER_TABLE)

    # Delete intratime user data
    for intratime_user_item in intratime_user_data:
        intratime_user_object = User(intratime_user_item[0], intratime_user_item[1])
        intratime_user_object.delete()

    # Delete normal user data
    for normal_user_item in normal_user_data:
        normal_user_object = User(normal_user_item[0], normal_user_item[1])
        normal_user_object.delete()
