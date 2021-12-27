def build_sucess_message(message):
    """Build a slack success text message.

    Args:
        message (str): Message to send.

    Returns:
        str: Message to send with checkmarks icons.
    """
    return f":white_check_mark: {message} :white_check_mark:"


def build_error_message(message):
    """Build a slack error text message.

    Args:
        message (str): Message to send.

    Returns:
        str: Message to send with X icons.
    """
    return f":x: {message} :x:"

# Add user
ADD_USER_SUCCESS = build_sucess_message('The user has been created successfully')
USER_ALREADY_REGISTERED = build_error_message('Your user is already registered!')
ADD_USER_ERROR = build_error_message('Could not create the user. Please contact with the app administrator')

# Delete user
DELETE_USER_SUCCESS = build_sucess_message('The user has been deleted successfully')
USER_NOT_REGISTERED = build_error_message('Your user is not registered!. You can do it typing `/sign_up` command')
DELETE_USER_ERROR = build_error_message('Could not delete the user. Please contact with the app administrator')
