from clockzy.lib.slack import slack_block_builder as bb
from clockzy.lib.db.database_interface import run_query, get_config_object, get_clock_data_in_time_range, \
                                              get_last_clock_from_user
from clockzy.lib.utils import time
from clockzy.lib.clocking import calculate_worked_time
from clockzy.lib.db.db_schema import ALIAS_TABLE, USER_TABLE
from clockzy.lib.clocking import IN_ACTION, PAUSE_ACTION, RETURN_ACTION, OUT_ACTION


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


def build_worked_time_message(time_range, worked_time):
    """Build the slack message when a user request to know the worked time.

    Args:
        time_range (str): Enum [today, week, month]
        worked_time (str): Worked time string.

    Returns:
        str: Slack message.
    """
    time_string = 'this week' if time_range == time.WEEK else ('this month' if time_range == time.MONTH else time_range)

    return f":timer_clock: Your working time {time_string} is *{worked_time}* :timer_clock:"


def build_time_history_message(user_id, time_range):
    """Build the slack message when a user request to know the worked time history.

    Args:
        user_id (str): User identifier to calculate the worked time.
        time_range (str): Enum [today, week, month]

    Returns:
        str: Slack message.
    """
    from_time = f"{time.get_current_date()} 00:00:00" if time_range == time.TODAY else \
                (time.get_first_week_day() if time_range == time.WEEK else time.get_first_month_day())
    header = f"{'-'*27} *{time_range.upper()} HISTORY* {'-'*27}\n\n:calendar: From _*{from_time}*_ to " \
             f"_*{time.get_current_date_time()}*_ :calendar:\n"

    lower_datetime = time.get_lower_time_from_time_range(time_range)
    upper_datetime = time.get_current_date_time()
    working_days = time.get_working_days(lower_datetime, upper_datetime)
    worked_time_output = ''
    total_worked_time = '0h 0m'

    # Calculate the time worked for each day of the selected range and add it to the output
    for worked_day in reversed(working_days):
        init_datetime = worked_day
        end_datetime = f"{worked_day.split(' ')[0]} 23:59:59"
        worked_time = calculate_worked_time(user_id, lower_limit=init_datetime, upper_limit=end_datetime)
        worked_time_output += f"*• {worked_day}*: {worked_time}\n"
        total_worked_time = time.sum_hh_mm_time(total_worked_time, worked_time)

    # Add the total worked time to the header message
    header += f":timer_clock: Total worked: *{total_worked_time}* :timer_clock:\n"

    # Build the block messages
    blocks = [
        bb.write_slack_divider(),
        bb.write_slack_markdown(header),
        bb.write_slack_divider(),
        bb.write_slack_markdown(worked_time_output)
    ]

    return blocks


def build_clock_history_message(user_id, time_range):
    """Build the slack message when a user request to know its clock history.

    Args:
        user_id (str): User identifier to calculate the worked time.
        time_range (str): Enum [today, week, month]

    Returns:
        str: Slack message.
    """
    from_time = f"{time.get_current_date()} 00:00:00" if time_range == time.TODAY else \
                (time.get_first_week_day() if time_range == time.WEEK else time.get_first_month_day())
    header = f"{'-'*27} *{time_range.upper()} HISTORY* {'-'*27}\n\n:calendar: From _*{from_time}*_ to " \
             f"_*{time.get_current_date_time()}*_ :calendar:\n"

    lower_datetime = time.get_lower_time_from_time_range(time_range)
    upper_datetime = time.get_current_date_time()
    worked_time = calculate_worked_time(user_id, lower_limit=lower_datetime, upper_limit=upper_datetime)
    header += f":timer_clock: Total worked: *{worked_time}* :timer_clock:\n"
    working_days = time.get_working_days(lower_datetime, upper_datetime)
    clock_history_output_list = []
    output_list_elements = 0

    # Build the block messages content. Create a new block message every 10 days to avoid the character text block limit
    for index, worked_day in enumerate(reversed(working_days)):
        init_datetime = worked_day
        end_datetime = f"{worked_day.split(' ')[0]} 23:59:59"
        clocking_data = get_clock_data_in_time_range(user_id, init_datetime, end_datetime)
        clock_history_output = ''
        if len(clocking_data) > 0:
            clock_history_output += f"• *{worked_day.split(' ')[0]}*:\n"
            for clock_item in clocking_data:
                clock_history_output += f"{' ' * 6}• {clock_item.action.upper()}: {clock_item.date_time}\n"
        else:
            clock_history_output += f"• *{worked_day.split(' ')[0]}*: :warning: No clocking data for this day " \
                                    ':warning:\n'

        # Add the message to the block item
        if len(clock_history_output_list) == 0:
            clock_history_output_list.append(clock_history_output)
        elif index % 10 == 0:
            clock_history_output_list.append(clock_history_output)
            output_list_elements += 1
        else:
            clock_history_output_list[output_list_elements] += clock_history_output

    # Build the block messages
    blocks = [
        bb.write_slack_divider(),
        bb.write_slack_markdown(header),
        bb.write_slack_divider()
    ]

    # Write a slack markdown block for each split message
    for item in clock_history_output_list:
        blocks.append(bb.write_slack_markdown(item))

    return blocks


def build_command_help_message():
    """Build the slack message when a user request to know the slack available commands.

    Returns:
        str: Slack message.
    """
    from clockzy.services.clockzy_service import ALLOWED_COMMANDS

    message = "Allowed commands and values:\n"

    for command, data in ALLOWED_COMMANDS.items():
        message += f"• *{command}*: {data['description']}\n"

        if len(data['allowed_parameters']) > 0:
            message += f"{' ' * 10}_Accepted parameters_: " \
                       f"[`{', '.join(str(param) for param in data['allowed_parameters'])}`]\n"
        elif 'parameters_description' in data:
            message += f"{' ' * 10}_Parameters_: `{data['parameters_description']}`\n"

    return [bb.write_slack_markdown(message)]


def build_get_aliases_message():
    """Build the slack message when a user request to know the registered aliases.

    Returns:
        str: Slack message.
    """
    header = f"{'-'*27} *ALIASES* {'-'*27}\n\n"
    query_ids = f"SELECT DISTINCT user_id FROM {ALIAS_TABLE}"
    data_ids = run_query(query_ids)
    message = ''

    blocks = [
        bb.write_slack_divider(),
        bb.write_slack_markdown(header),
        bb.write_slack_divider()
    ]

    if len(data_ids) == 0:
        blocks.append(bb.write_slack_markdown(':warning: No registered aliases found :warning:'))
        return blocks

    # Iterate over all users in alias data
    for user_id in data_ids:
        user_name = run_query(f"SELECT user_name FROM {USER_TABLE} WHERE id='{user_id[0]}'")[0][0]
        message += f"• *{user_name}*: [ "
        aliases = run_query(f"SELECT alias FROM {ALIAS_TABLE} WHERE user_id='{user_id[0]}'")
        # Get all aliases from that user
        for alias in aliases:
            message += f"_{ alias[0]}_, "

        # Remove ', ' from the end
        message = message[:-2]
        message += ' ]\n'

    blocks.append(bb.write_slack_markdown(message))

    return blocks


def build_user_status_message(user_id, user_name):
    """Build the slack message when a user query the status of another user.

    Args:
        user_id (str): User identifier queried.
        user_name (str): User name or alias queried.

    Returns:
        str: Slack message.
    """
    last_clock = get_last_clock_from_user(user_id)

    if last_clock is None:
        return f":warning: The user `{user_name}` does not have any clock data :warning:"

    if last_clock.action.lower() == IN_ACTION or last_clock.action.lower() == RETURN_ACTION:
        return f":large_green_circle: The user `{user_name}` is available :large_green_circle:"
    elif last_clock.action.lower() == PAUSE_ACTION:
        return f":large_yellow_circle: The user `{user_name}` is absent, but will return later :large_yellow_circle:"
    else:
        return f":red_circle: The user `{user_name}` is not available :red_circle:"


# -------------------------------------------------------------------------------------------------------------------- #


ERROR_IMAGE = 'https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/x.png'

# Add user
ADD_USER_SUCCESS = build_success_message('The user has been created successfully')
USER_ALREADY_REGISTERED = build_error_message('Your user is already registered!')
ADD_USER_ERROR = build_error_message('Could not create the user. Please contact with the app administrator')

# Delete user
DELETE_USER_SUCCESS = build_success_message('The user has been deleted successfully')
USER_NOT_REGISTERED = build_error_message('Your user is not registered!. You can do it typing `/sign_up` command')
DELETE_USER_ERROR = build_error_message('Could not delete the user. Please contact with the app administrator')
