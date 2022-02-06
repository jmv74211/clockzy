import pytz
from datetime import datetime, timedelta


DAYS = 'day'
HOURS = 'hour'
MINUTES = 'minute'
SECONDS = 'second'
TODAY = 'today'
WEEK = 'week'
MONTH = 'month'


def get_current_date_time(timezone='Europe/Berlin'):
    """Get the current date time.

    Args:
        timezone (str): Timezone.

    Returns:
        str: Datetime in format %Y-%m-%d %H:%M:%S
    """
    date_time = datetime.now(pytz.timezone(timezone)).strftime("%Y-%m-%d %H:%M:%S")

    return date_time


def get_current_date():
    """Get the current date.

    Returns:
        str: Date in format in format %Y-%m-%d
    """

    return f"{datetime.now().strftime('%Y-%m-%d')}"


def subtract_days_to_datetime(date_time, days):
    """Subtract a number of days from a given date

    Args:
        date_time (str): Date in format %Y-%m-%d %H:%M:%S
        days (int): Number of days to subtract

    Returns:
        str: Datetime in format %Y-%m-%d %H:%M:%S
    """
    date_object = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
    return datetime.strftime(date_object - timedelta(days=days), '%Y-%m-%d %H:%M:%S')


def get_week_day(date_time):
    """Get the current day of the week, where Monday is 0 and Sunday is 6.

    Args:
        date_time (str): Datetime to find out what day of the week it is.

    Returns:
        int: [0-6] where Monday is 0 and Sunday is 6
    """
    date_object = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
    return date_object.weekday()


def get_first_week_day():
    """Get the first datetime of current week

    Returns
        str: First day of week in %Y-%m-%d %H:%M:%S format. e.g 2020-11-02 00:00:00
    """
    date_time = f"{get_current_date()} 00:00:00"
    week_init_date = datetime.strptime(subtract_days_to_datetime(date_time, get_week_day(date_time)),
                                       '%Y-%m-%d %H:%M:%S').date()
    week_init_datetime = f"{datetime.strftime(week_init_date, '%Y-%m-%d')} 00:00:00"

    return week_init_datetime


def get_first_month_day():
    """Get the first datetime of current month.

    Returns:
        str: %Y-%m-%d %H:%M:%S: First day of month e.g 2020-11-01 00:00:00
    """
    date_time = f"{get_current_date()} 00:00:00"
    date_time_object = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S').replace(day=1, hour=0, minute=0, second=0)
    month_init_datetime = datetime.strftime(date_time_object, '%Y-%m-%d %H:%M:%S')

    return month_init_datetime


def get_time_difference(datetime_from, datetime_to, unit=SECONDS):
    """Get the time difference between two datetimes (time subtraction).

    Args:
        datetime_from (str): Lower limit datetime in format %Y-%m-%d %H:%M:%S
        datetime_to (str): Upper limit datetime in format %Y-%m-%d %H:%M:%S
        unit (str): Unit of time to express the result. enum: ['day', 'hour', 'minute', 'second']

    Returns:
        int: Time elapsed between the two datetimes.
    """
    datetime_from_object = datetime.strptime(datetime_from, '%Y-%m-%d %H:%M:%S')
    datetime_to_object = datetime.strptime(datetime_to, '%Y-%m-%d %H:%M:%S')

    if unit == DAYS:
        return int((datetime_to_object - datetime_from_object).total_seconds() / (60*60*24))
    elif unit == HOURS:
        return int((datetime_to_object - datetime_from_object).total_seconds() / (60*60))
    elif unit == MINUTES:
        return int((datetime_to_object - datetime_from_object).total_seconds() / 60)
    else:
        return int((datetime_to_object - datetime_from_object).total_seconds())


def get_time_hh_mm_from_seconds(num_seconds):
    """Get the time string from seconds. e.g 3660 --> 1h 1m

    Parameters:
        num_seconds (int): Number of seconds.

    Returns:
        str: Time string in format [x]h [y]m
    """
    mm, ss = divmod(num_seconds, 60)
    hh, mm = divmod(mm, 60)

    return f"{hh}h {mm}m"


def datetime_to_str(datetime):
    """Convert a datetime object into string.

    Args:
        datetime (datatime): Datetime object.

    Returns:
        str: Date string in format %Y-%m-%d %H:%M:%S
    """
    return datetime.strftime("%Y-%m-%d %H:%M:%S")


def get_lower_time_from_time_range(time_range):
    """Get the start date of the specified time range.

    Args:
        time_range (str): Enum [today, week, month].

    Returns:
        str: Date string in format %Y-%m-%d 00:00:00
    """
    if time_range == 'today':
        lower_limit_datetime = f"{get_current_date()} 00:00:00"
    elif time_range == 'week':
        lower_limit_datetime = get_first_week_day()
    else:  # Month
        lower_limit_datetime = get_first_month_day()

    return lower_limit_datetime


def get_working_days(datetime_from, datetime_to, excluded=(6, 7)):
    """Get all dates between Monday and Friday for the specified time range.

     Args:
        datetime_from (str): Upper limit datetime in format %Y-%m-%d %H:%M:%S
        datetime_to (str): Upper limit datetime  in format %Y-%m-%d %H:%M:%S
        excluded (tuple): Excluded days.

    Returns:
        list(str): List of dates in format %Y-%m-%d 00:00:00
    """
    initial_datetime = datetime.strptime(datetime_from, '%Y-%m-%d %H:%M:%S')
    end_datetime = datetime.strptime(datetime_to, '%Y-%m-%d %H:%M:%S')
    days = []

    while initial_datetime.date() <= end_datetime.date():
        if initial_datetime.isoweekday() not in excluded:
            days.append(datetime.strftime(initial_datetime, '%Y-%m-%d %H:%M:%S'))
        initial_datetime += timedelta(days=1)

    return days


def get_num_seconds_from_hh_mm_time(string_time):
    """Get the num seconds from a string date in format [x]h [y]m.

    Args:
        string_time (str): Time in format 0h 0m

    Returns:
        int: Total of seconds
    """
    hours = int(string_time.split('h')[0])
    minutes = int(string_time.split(' ')[1].split('m')[0])

    return timedelta(hours=hours, minutes=minutes).total_seconds()


def sum_hh_mm_time(time_1, time_2):
    """Sum two times in the following format: 0h 0m

    Args:
        time_1 (str): Time 1 in format 0h 0m
        time_2 (str): Time 2 in format 0h 0m

    Returns:
        str: Sum of the specified times in format 0h 0m
    """
    result = get_num_seconds_from_hh_mm_time(time_1) + get_num_seconds_from_hh_mm_time(time_2)

    return get_time_hh_mm_from_seconds(int(result))
