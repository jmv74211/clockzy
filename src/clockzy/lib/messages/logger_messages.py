# Logging messages

bad_slack_signature = 'The slack signature is not correct'
bad_timestamp_signature = 'The slack timestamp signature is not correct'


def unauthorized_request(ip):
    return f"An unauthorized request has been received from {ip}"


def missing_slack_request_object(func):
    return f"Programming error, missing slack_request_object in {func}"


def command_monitoring(user, id, command):
    return f"The user {user}({id}) has executed the '{command}' command"


def user_created(user, id):
    return f"The user {user}({id}) has been created successfully"


def error_creating_user(user, id):
    return f"Could not create the user {user}({id})"


def user_deleted(user, id):
    return f"The user {user}({id}) has been deleted successfully"


def error_deleting_user(user, id):
    return f"Could not delete the user {user}({id})"


def error_intratime_auth(user, id):
    return f"The user {user}({id}) has tried to clock with bad intratime credentials"


def error_intratime_clocking(user, id, action):
    return f"Error when the user {user}({id}) is trying to clock the '{action}' action. The intratime API may not " \
           'be working properly'


def error_clockzy_clocking(user, id, action):
    return f"Error when the user {user}({id}) is trying to clock the {action}' action in the clockzy local DB"


def success_clockzy_clocking(user, id, action):
    return f"The user {user}({id}) has successfully clocked the {action} action"


def alias_created(user, id, referenced_user, alias):
    return f"The alias '{alias}' for the {referenced_user} user has been created successfully by the {user}({id}) user"


def error_creating_alias(user, id, alias):
    return f"Error when then user {user}({id}) is creating the {alias} alias"


def error_updating_user_credentials(user, id):
    return f"Error when updating the credentials for the user {user}{(id)}"


def error_updating_user_configuration(user, id):
    return f"Error when updating the configuration for the user {user}({id})"


def success_enabling_intratime_sync(user, id):
    return f"The user {user}({id}) has successfully enabled the intratime integration"


def error_disabling_intratime_sync(user, id):
    return f"Error when disabling the intratime integration for the user {user}({id})"


def success_disabling_intratime_sync(user, id):
    return f"The user {user}({id}) has disabled successfully the intratime integration"
