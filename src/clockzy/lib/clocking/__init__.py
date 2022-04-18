from clockzy.lib.db.database_interface import get_last_clock_from_user, get_clock_data_in_time_range
from clockzy.lib.utils import time


IN_ACTION = 'in'
PAUSE_ACTION = 'pause'
RETURN_ACTION = 'return'
OUT_ACTION = 'out'


def user_can_clock_this_action(user_id, action):
    """Check if the user can clock an action taking into account the last previous clocking made.

    Args:
        user_id (str): User id who wants to make the clocking.
        action (str): Action to check.

    Returns
        Tuple(boolean, str): If the user can clock the action and the error message in negative case.
    """
    last_clocked_object = get_last_clock_from_user(user_id)

    white_list = {
        IN_ACTION: [PAUSE_ACTION, OUT_ACTION],
        PAUSE_ACTION: [RETURN_ACTION],
        RETURN_ACTION: [PAUSE_ACTION, OUT_ACTION],
        OUT_ACTION: [IN_ACTION]
    }

    # If no previous records and action is not IN
    if last_clocked_object is None and action != IN_ACTION:
        return (False, 'You do not have any previous registration, so the coherent thing is that you sign an entry'
                       '(`IN`)')
    # If no previous records but the action is IN
    elif last_clocked_object is None:
        return (True, None)

    last_clocked_action = last_clocked_object.action.lower()

    # If previous records but the action is wrong
    if action not in white_list[last_clocked_action]:
        available_actions = [f"`{action.upper()}`" for action in white_list[last_clocked_action]]
        return (False, f"Your last clock action was `{last_clocked_action.upper()}`, so you can not `{action.upper()}` "
                       f"clock action.\n*Available actions*: {', '.join(available_actions)}")

    return (True, None)


def calculate_worked_time(user_id, time_range=None, lower_limit=None, upper_limit=None, timezone='Europe/Berlin'):
    """Calculate the worked time (using the clocking data) in the specified time range.

    Note: You can specify the time_range or the lower_limit and upper_limit.

    Args:
        user_id (str): User identifier for searching the clocking data and calculating the worked time.
        time_range (str): enum: [today, week, month].
        lower_limit (str): Upper limit datetime in format %Y-%m-%d %H:%M:%S
        upper_limit (str): Upper limit datetime  in format %Y-%m-%d %H:%M:%S
        timezone (str): User timezone.

    Returns:
        str: Worked time in the following format [x]h [y]m
    """
    if time_range:
        lower_limit = time.get_lower_time_from_time_range(time_range, timezone)
        upper_limit = time.get_current_date_time(timezone)

    # Get the clocking objects
    clock_data = get_clock_data_in_time_range(user_id, lower_limit, upper_limit)

    # If there is no data in the specified range
    if len(clock_data) == 0:
        previous_month_datetime = time.subtract_days_to_datetime(lower_limit, 31)
        # Get the clockings data between the lower datetime and one month back from that date
        before_clockings = get_clock_data_in_time_range(user_id, previous_month_datetime, lower_limit)
        # If the user has not made any clock registration yet (in one month)
        if len(before_clockings) == 0:
            return time.get_time_hh_mm_from_seconds(0)
        # Get time in case of continuing from the previous clocking
        user_last_clock = before_clockings[-1]
        if user_last_clock.action.lower() == IN_ACTION or user_last_clock.action.lower() == RETURN_ACTION:
            lower_limit = f"{time.get_current_date_time(timezone).split(' ')[0]} 00:00:00"
            time_difference = time.get_time_difference(lower_limit, time.get_current_date_time(timezone))
            return time.get_time_hh_mm_from_seconds(time_difference)
        # The user closed the previous days and has not started yet
        else:
            return time.get_time_hh_mm_from_seconds(0)

    # Calculate the number of worked seconds
    worked_seconds = 0
    before_action = ''
    before_action_datetime = ''

    for index, clock_item in enumerate(clock_data):
        # Add worked time if worked in the early morning hours
        if index == 0 and (clock_item.action.lower() == OUT_ACTION or clock_item.action.lower() == PAUSE_ACTION):
            morning_time = f"{time.datetime_to_str(clock_item.date_time).split(' ')[0]} 00:00:00"
            worked_seconds += time.get_time_difference(morning_time, time.datetime_to_str(clock_item.date_time))

        # Add clocking time
        if (clock_item.action.lower() == PAUSE_ACTION and before_action == IN_ACTION) or \
           (clock_item.action.lower() == OUT_ACTION and before_action == IN_ACTION) or \
           (clock_item.action.lower() == OUT_ACTION and before_action == RETURN_ACTION) or \
           (clock_item.action.lower() == PAUSE_ACTION and before_action == RETURN_ACTION):
            worked_seconds += time.get_time_difference(before_action_datetime,
                                                       time.datetime_to_str(clock_item.date_time))
        before_action = clock_item.action.lower()
        before_action_datetime = time.datetime_to_str(clock_item.date_time)

    # Get information about the last clockings to calculate time not closed if necessary
    last_clocked_action = clock_data[-1].action.lower()
    last_clocked_datetime = time.datetime_to_str(clock_data[-1].date_time)

    # Add the time remaining until now before pausing or exiting (time worked but not clocked)
    if last_clocked_action != OUT_ACTION and last_clocked_action != PAUSE_ACTION:
        # If the date is today, then add up to the current time
        if last_clocked_datetime.split(' ')[0] == time.get_current_date_time(timezone).split(' ')[0]:
            last_clocked_datetime_end = time.get_current_date_time(timezone)
        # If the date is not today, then add to the end of that day
        else:
            last_clocked_datetime_end = f"{last_clocked_datetime.split(' ')[0]} 23:59:59"
        # Add the working time not closed
        last_non_clocked_time = time.get_time_difference(last_clocked_datetime, last_clocked_datetime_end)
        worked_seconds += last_non_clocked_time

    return time.get_time_hh_mm_from_seconds(worked_seconds)
