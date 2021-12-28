import pytest

from clockzy.lib.db.database_interface import get_clock_data_in_time_range
from clockzy.lib.test_framework.database import no_intratime_user_parameters

test_get_clock_data_in_time_range_parameters = [
    (no_intratime_user_parameters['id'], '2021-11-01 00:00:00', '2021-12-29 00:00:00', 40),
    (no_intratime_user_parameters['id'], '2021-11-01 00:00:00', '2021-11-30 23:59:59', 18),
    (no_intratime_user_parameters['id'], '2021-12-01 00:00:00', '2021-12-29 23:59:59', 22),
    (no_intratime_user_parameters['id'], '2021-12-27 00:00:00', '2021-12-30 23:59:59', 8),
    (no_intratime_user_parameters['id'], '2021-12-20 00:00:00', '2021-12-24 23:59:59', 0),
    (no_intratime_user_parameters['id'], '2021-12-27 00:00:00', '2021-12-27 23:59:59', 4),
]

@pytest.mark.parametrize('user_id, datetime_from, datetime_to, expected_result',
                         test_get_clock_data_in_time_range_parameters)
def test_get_clock_data_in_time_range(add_clock_test_data, user_id, datetime_from, datetime_to, expected_result):
    """Test the get_clock_data_in_time_range function from clockzy module"""
    assert len(get_clock_data_in_time_range(user_id, datetime_from, datetime_to)) == expected_result
