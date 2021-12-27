from clockzy.lib.slack import slack_block_builder as bb
from clockzy.lib.db.database_interface import get_config_object


def build_success_message(message):
    """Build a slack success text message.

    Args:
        message (str): Message to send.

    Returns:
        str: Message to send with checkmarks icons.
    """
    return f"*Status*: _SUCCESS_ :white_check_mark:\n*Message*: {message}"


def build_error_message(message):
    """Build a slack error text message.

    Args:
        message (str): Message to send.

    Returns:
        str: Message to send with X icons.
    """
    return f"*Status*: _ERROR_ :x:\n*Message*: {message}"


def build_block_message(title, description, success=True, image_url=None):
    """Build a standard block slack message.

    Args:
        title (str): Message title (header).
        description (str): Message description (header).
        success (boolean): Operation status.
        image_url (str): Image URL to render an image in the message (optional).

    Returns:
        list(dict): Messages blocks.
    """
    header = f":white_check_mark: {title} :white_check_mark:" if success else f":x: {title} :x:"
    status = 'SUCCESS' if success else 'FAILED'
    message = f"{header}\n *Status*: {status}\n *Description*: {description}\n"

    block = []
    block.append(bb.write_slack_divider())
    block.append(bb.write_slack_markdown(message, image_url))
    block.append(bb.write_slack_divider())

    return block


def build_successful_clocking_message(user_id, clock_action, clock_date_time, user_name):
    """Build the slack message when an user has clocked successfully.

    Args:
        user_id (str): User identifier.
        clock_action (str): Action clocked.
        clock_date_time (str): Clock date time
        user_name (str): User name.

    Returns:
        list(dict): Messages blocks.
    """
    user_config = get_config_object(user_id)
    intratime_integration = False if user_config is None else user_config.intratime_integration
    image_base_name = f"{clock_action}_intratime.png" if intratime_integration else f"{clock_action}_clockzy.png"
    image_url = f"https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/{image_base_name}"
    message = ':white_check_mark: Your clocking has been registered successfully :white_check_mark:\n' \
              f"*Username*: {user_name}\n*Action*: {clock_action.upper()}\n*Datetime*: {clock_date_time}"
    block = []
    block.append(bb.write_slack_divider())
    block.append(bb.write_slack_markdown(message, image_url))
    block.append(bb.write_slack_divider())

    return block


ERROR_IMAGE = 'https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/x.png'

# Add user
ADD_USER_SUCCESS = build_success_message('The user has been created successfully')
USER_ALREADY_REGISTERED = build_error_message('Your user is already registered!')
ADD_USER_ERROR = build_error_message('Could not create the user. Please contact with the app administrator')

# Delete user
DELETE_USER_SUCCESS = build_success_message('The user has been deleted successfully')
USER_NOT_REGISTERED = build_error_message('Your user is not registered!. You can do it typing `/sign_up` command')
DELETE_USER_ERROR = build_error_message('Could not delete the user. Please contact with the app administrator')
