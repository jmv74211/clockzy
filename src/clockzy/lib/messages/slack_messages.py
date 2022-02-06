import logging
from clockzy.lib.slack import slack_block_builder as bb
from clockzy.lib.slack import slack_core as slack
from clockzy.lib.db.database_interface import run_query, get_config_object, get_clock_data_in_time_range, \
                                              get_last_clock_from_user
from clockzy.lib.utils import time
from clockzy.lib.clocking import calculate_worked_time
from clockzy.lib.db.db_schema import ALIAS_TABLE, USER_TABLE
from clockzy.lib.clocking import IN_ACTION, PAUSE_ACTION, RETURN_ACTION, OUT_ACTION


ERROR_IMAGE = 'https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/x.png'
WARNING_IMAGE = 'https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/warning.png'
GREEN_CIRCLE = ':large_green_circle:'
YELLOW_CIRCLE = ':large_yellow_circle:'
RED_CIRCLE = ':red_circle:'
HOURGLASS = ':hourglass_flowing_sand:'
TIMER_CLOCK = ':timer_clock:'
MEGA = ':mega:'
FLAG = ':triangular_flag_on_post:'
CALENDAR = ':calendar:'


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

    if time_range == time.TODAY:
        num_hours = int(worked_time.split('h')[0])
        status_icon = GREEN_CIRCLE if num_hours >= 8 else \
            (YELLOW_CIRCLE if num_hours < 8 and num_hours >= 7 else RED_CIRCLE)
        return f"{HOURGLASS} Your working time {time_string} is *{worked_time}* {status_icon}"

    return f"{HOURGLASS} Your working time {time_string} is *{worked_time}*"


def build_time_history_message(user_id, time_range, timezone):
    """Build the slack message when a user request to know the worked time history.

    Args:
        user_id (str): User identifier to calculate the worked time.
        time_range (str): Enum [today, week, month]
        timezone (str): User timezone.

    Returns:
        str: Slack message.
    """
    from_time = f"{time.get_current_date()} 00:00:00" if time_range == time.TODAY else \
                (time.get_first_week_day() if time_range == time.WEEK else time.get_first_month_day())
    header = f"{time_range.upper()} HISTORY"
    summary = f"{CALENDAR} From _*{from_time}*_ to _*{time.get_current_date_time(timezone)}*_\n"

    lower_datetime = time.get_lower_time_from_time_range(time_range)
    upper_datetime = time.get_current_date_time(timezone)
    working_days = time.get_working_days(lower_datetime, upper_datetime, excluded=())
    worked_time_output = ''
    num_worked_days = 0

    # Calculate the time worked for each day of the selected range and add it to the output
    for worked_day in reversed(working_days):
        init_datetime = worked_day
        end_datetime = f"{worked_day.split(' ')[0]} 23:59:59"
        worked_time = calculate_worked_time(user_id, lower_limit=init_datetime, upper_limit=end_datetime,
                                            timezone=timezone)
        if worked_time != '0h 0m':
            num_worked_days += 1
        worked_time_output += f"*• {worked_day}*: {worked_time}\n"

    # Calculate the average time
    if num_worked_days > 0:
        total_worked_time = calculate_worked_time(user_id, lower_limit=lower_datetime, upper_limit=upper_datetime,
                                                  timezone=timezone)
        average_seconds = int(time.get_num_seconds_from_hh_mm_time(total_worked_time) / num_worked_days)
        average_time = time.get_time_hh_mm_from_seconds(average_seconds)
        average_hours = int(average_time.split('h')[0])
        average_icon = GREEN_CIRCLE if average_hours >= 8 else \
            (YELLOW_CIRCLE if average_hours < 8 and average_hours >= 7 else RED_CIRCLE)

        # Add extra info to the summary message
        summary += f"{HOURGLASS} Total worked: *{total_worked_time}*"
        if time_range == time.TODAY:
            summary += f" {average_icon}\n"

        if time_range != time.TODAY:
            summary += f"\n{FLAG} Worked days: *{num_worked_days}*\n"
            summary += f"{TIMER_CLOCK} Average time: *{average_time}* {average_icon}\n"

    # Build the block messages
    blocks = [
        bb.write_slack_header(header),
        bb.write_slack_divider(),
        bb.write_slack_markdown(summary),
        bb.write_slack_divider(),
        bb.write_slack_markdown(worked_time_output)
    ]

    return blocks


def build_clock_history_message(user_id, time_range, timezone):
    """Build the slack message when a user request to know its clock history.

    Args:
        user_id (str): User identifier to calculate the worked time.
        time_range (str): Enum [today, week, month]
        timezone (str): Timezone.

    Returns:
        str: Slack message.
    """
    from_time = f"{time.get_current_date()} 00:00:00" if time_range == time.TODAY else \
                (time.get_first_week_day() if time_range == time.WEEK else time.get_first_month_day())
    header = f"{time_range.upper()} HISTORY"
    summary = f"{CALENDAR} From _*{from_time}*_ to _*{time.get_current_date_time(timezone)}*_\n"

    lower_datetime = time.get_lower_time_from_time_range(time_range)
    upper_datetime = time.get_current_date_time(timezone)
    worked_time = calculate_worked_time(user_id, lower_limit=lower_datetime, upper_limit=upper_datetime,
                                        timezone=timezone)
    working_days = time.get_working_days(lower_datetime, upper_datetime, excluded=())
    num_worked_days = 0
    clock_history_output_list = []
    output_list_elements = 0

    # Build the block messages content. Create a new block message every 10 days to avoid the character text block limit
    for index, worked_day in enumerate(reversed(working_days)):
        init_datetime = worked_day
        end_datetime = f"{worked_day.split(' ')[0]} 23:59:59"
        clocking_data = get_clock_data_in_time_range(user_id, init_datetime, end_datetime)
        clock_history_output = ''
        if len(clocking_data) > 0:
            num_worked_days += 1
            clock_history_output += f"• *{worked_day.split(' ')[0]}*:\n"
            for clock_item in clocking_data:
                clock_time = clock_item.date_time.strftime('%H:%M:%S')
                clock_history_output += f"{' ' * 6}• `{clock_item.action.upper()}`: _{clock_time}_\n"
        else:
            clock_history_output += f"• *{worked_day.split(' ')[0]}*: {MEGA} No clocking data for this day\n"

        # Add the message to the block item
        if len(clock_history_output_list) == 0:
            clock_history_output_list.append(clock_history_output)
        elif index % 10 == 0:
            clock_history_output_list.append(clock_history_output)
            output_list_elements += 1
        else:
            clock_history_output_list[output_list_elements] += clock_history_output

    # Calculate the average time
    if num_worked_days > 0:
        average_seconds = int(time.get_num_seconds_from_hh_mm_time(worked_time) / num_worked_days)
        average_time = time.get_time_hh_mm_from_seconds(average_seconds)
        average_hours = int(average_time.split('h')[0])
        average_icon = GREEN_CIRCLE if average_hours >= 8 else \
            (YELLOW_CIRCLE if average_hours < 8 and average_hours >= 7 else RED_CIRCLE)

        # Add extra info to the summary message
        summary += f"{HOURGLASS} Total worked: *{worked_time}* {average_icon}\n"

        if time_range != time.TODAY:
            summary += f"{FLAG} Worked days: *{num_worked_days}*\n"
            summary += f"{TIMER_CLOCK} Average time: *{average_time}* {average_icon}\n"

    # Build the block messages
    blocks = [
        bb.write_slack_header(header),
        bb.write_slack_divider(),
        bb.write_slack_markdown(summary),
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
    header = 'ALIASES'
    query_ids = f"SELECT DISTINCT user_id FROM {ALIAS_TABLE}"
    data_ids = run_query(query_ids)
    message = ''

    blocks = [
        bb.write_slack_header(header),
        bb.write_slack_divider()
    ]

    if len(data_ids) == 0:
        blocks.append(bb.write_slack_markdown(f"{MEGA} No registered aliases found"))
        return blocks

    # Iterate over all users in alias data
    for user_id in data_ids:
        user_name = run_query(f"SELECT user_name FROM {USER_TABLE} WHERE id='{user_id[0]}'")[0][0]
        message += f"• *{user_name}*: "
        aliases = run_query(f"SELECT alias FROM {ALIAS_TABLE} WHERE user_id='{user_id[0]}'")
        # Get all aliases from that user
        for alias in aliases:
            message += f"`{ alias[0]}`, "

        # Remove ', ' from the end
        message = message[:-2]
        message += '\n'

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
        return f"{MEGA} The user `{user_name}` does not have any clock data"

    if last_clock.action.lower() == IN_ACTION or last_clock.action.lower() == RETURN_ACTION:
        return f"The user `{user_name}` is available {GREEN_CIRCLE}"
    elif last_clock.action.lower() == PAUSE_ACTION:
        return f" The user `{user_name}` is absent, but will return later {YELLOW_CIRCLE}"
    else:
        return f"The user `{user_name}` is not available {RED_CIRCLE}"


def send_slack_message(message_id, response_url, extra_args=[]):
    """Send a predefined slack message.

    Args:
        message_id (str): Message identifier to send.
        response_url (str): Slack request response URL.
        extra_args (list): List of needed variables to compose the message.
    """
    # List of message IDs that are sent as block type
    block_messages = ['BAD_CLOCKING_TYPE', 'BAD_CLOCKING_CREDENTIALS', 'ERROR_CLOCKING_INTRATIME', 'CLOCKING_SUCCESS',
                      'ERROR_CLOCKING_CLOCKZY_WITH_INTRATIME', 'ERROR_CLOCKING_CLOCKZY_WITHOUT_INTRATIME',
                      'GET_ALIASES', 'COMMAND_HELP', 'TIME_HISTORY', 'CLOCK_HISTORY', 'TODAY_INFO']

    message_type = 'blocks' if message_id in block_messages else 'text'

    if message_id == 'USER_NOT_REGISTERED':
        message = build_error_message('Your user is not registered!. You can do it typing `/sign_up` command')
    elif message_id == 'NOT_ALLOWED_COMMAND':
        message = f"`{extra_args[0]}` is not an allowed command. Allowed ones: `{extra_args[1]}`"
    elif message_id == 'WRONG_NUM_COMMAND_PARAMETERS':
        message = f"`{extra_args[0]}` command expects *{extra_args[1]}* parameter(s): `{extra_args[2]}`"
    elif message_id == 'WRONG_COMMAND_PARAMETER':
        message = f"`{extra_args[0]}` command expects one of the following parameters value: `{extra_args[1]}`"
    elif message_id == 'ADD_USER_SUCCESS':
        message = build_success_message('Your account has been created successfully')
    elif message_id == 'USER_ALREADY_REGISTERED':
        message = f"{MEGA} Your user is already registered!"
    elif message_id == 'ADD_USER_ERROR':
        message = build_error_message('Could not create the user. Please contact with the app administrator')
    elif message_id == 'USER_INFO_ALREADY_UPDATED':
        message = f"{MEGA} Your user info is already updated!. No changes were made"
    elif message_id == 'UPDATE_USER_ERROR':
        message = build_error_message('Could not update your user data. Please contact with the app administrator')
    elif message_id == 'UPDATE_USER_SUCCESS':
        message = build_success_message('Your username data has been updated successfully!')
    elif message_id == 'DELETE_USER_SUCCESS':
        message = build_success_message('The user has been deleted successfully')
    elif message_id == 'DELETE_USER_ERROR':
        message = build_error_message('Could not delete the user. Please contact with the app administrator')
    elif message_id == 'BAD_CLOCKING_TYPE':
        message = build_block_message('Could not clock your action', extra_args[0], False, ERROR_IMAGE)
    elif message_id == 'BAD_CLOCKING_CREDENTIALS':
        message = build_block_message('Could not clock your action', 'Your intratime credentials are not correct. '
                                      f"Please update them using the `{extra_args[0]}` command", False, ERROR_IMAGE)
    elif message_id == 'ERROR_CLOCKING_INTRATIME':
        message = build_block_message('Could not clock your action', 'It seems that the intratime API is not '
                                      'available. Try again in a few seconds', False, ERROR_IMAGE)
    elif message_id == 'CLOCKING_SUCCESS':
        message = build_successful_clocking_message(extra_args[0], extra_args[1], extra_args[2], extra_args[3])
    elif message_id == 'ERROR_CLOCKING_CLOCKZY_WITH_INTRATIME':
        message = build_block_message('Could not clock your action in clockzy app', 'The clock has been registered in '
                                      'the Intratime app but not in clockzy app. Please, contact with the app '
                                      'administrator', False, WARNING_IMAGE)
    elif message_id == 'ERROR_CLOCKING_CLOCKZY_WITHOUT_INTRATIME':
        message = build_block_message('Could not clock your action', 'Contact with the app administrator', False,
                                      ERROR_IMAGE)
    elif message_id == 'WORKED_TIME':
        message = build_worked_time_message(extra_args[0], extra_args[1])
    elif message_id == 'TIME_HISTORY':
        message = build_time_history_message(extra_args[0], extra_args[1], extra_args[2])
    elif message_id == 'CLOCK_HISTORY':
        message = build_clock_history_message(extra_args[0], extra_args[1], extra_args[2])
    elif message_id == 'TODAY_INFO':
        message = build_clock_history_message(extra_args[0], extra_args[1], extra_args[2])
    elif message_id == 'COMMAND_HELP':
        message = build_command_help_message()
    elif message_id == 'UNDEFINED_USERNAME':
        message = build_error_message(f"Could not find an user with `{extra_args[0]}` username")
    elif message_id == 'ALIAS_ALREADY_REGISTERED':
        message = build_error_message(f"The alias `{extra_args[0]}` is already registered as an alias")
    elif message_id == 'ERROR_CREATING_ALIAS':
        message = build_error_message('Could not create the alias, please contact with the app administrator')
    elif message_id == 'ADD_ALIAS_SUCCESS':
        message = build_success_message(f"The `{extra_args[0]}` alias has been registered successfully for the "
                                        f"`{extra_args[1]}` username")
    elif message_id == 'GET_ALIASES':
        message = build_get_aliases_message()
    elif message_id == 'BAD_USERNAME_OR_ALIAS':
        message = build_error_message(f"The `{extra_args[0]}` user_name or alias does not exist.")
    elif message_id == 'USER_STATUS':
        message = build_user_status_message(extra_args[0], extra_args[1])
    elif message_id == 'BAD_INTRATIME_CREDENTIALS':
        message = build_error_message('The entered Intratime credentials are not correct')
    elif message_id == 'ERROR_UPDATING_USER_CREDENTIALS':
        message = build_error_message('Your intratime credentials could not be updated, please contact with the app '
                                      'administrator')
    elif message_id == 'ERROR_UPDATING_USER_CONFIGURATION':
        message = build_error_message('Your user configuration could not be updated, please contact with the app '
                                      'administrator')
    elif message_id == 'ENABLE_INTRATIME_SUCCESS':
        message = build_success_message('The linking with the Intratime app has been successful!')
    elif message_id == 'INTRATIME_ALREADY_DISABLED':
        message = f"{MEGA} You already have it disabled!"
    elif message_id == 'ERROR_DISABLING_INTRATIME':
        message = build_error_message('Could not disable the intratime integration. Please contact with the app '
                                      'admistrator')
    elif message_id == 'DISABLE_INTRATIME_SUCCESS':
        message = build_success_message('Integration with intratime disabled successfully')
    elif message_id == 'ERROR_GETTING_USER_PROFILE_INFO':
        message = build_error_message('Could not get your profile info to set your time zone. Please contact with the '
                                      'app admistrator')
    else:
        logging.getLogger('clockzy').error(f"Undefined {message_id} message ID")
        slack.post_ephemeral_response_message(build_error_message(f"Undefined {message_id} slack message ID. Please  "
                                                                  'contact with the app administrator'),
                                              response_url, message_type)
        return None

    # Send the slack message
    slack.post_ephemeral_response_message(message, response_url, message_type)
