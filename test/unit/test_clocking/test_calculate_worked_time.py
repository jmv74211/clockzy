import pytest
import freezegun

from clockzy.lib.clocking import calculate_worked_time
from clockzy.lib.test_framework.database import no_intratime_user_parameters


test_calculate_worked_time_parameters = [
    (no_intratime_user_parameters['id'], 'today', '2021-11-20 19:20:00', '9h 15m'),
    (no_intratime_user_parameters['id'], 'week', '2021-11-05 23:50:00', '30h 15m'),
    (no_intratime_user_parameters['id'], 'month', '2021-11-20 19:20:00', '48h 45m'),
    (no_intratime_user_parameters['id'], 'today', '2021-12-28 18:28:00', '9h 28m'),
    (no_intratime_user_parameters['id'], 'today', '2021-12-28 23:50:00', '10h 0m'),
    (no_intratime_user_parameters['id'], 'week', '2021-12-28 23:50:00', '19h 0m'),
    (no_intratime_user_parameters['id'], 'month', '2021-12-28 23:50:00', '53h 30m')
]


@pytest.mark.parametrize('user_id, time_range, freezed_time, expected_result', test_calculate_worked_time_parameters)
def test_calculate_worked_time(add_clock_test_data, user_id, time_range, freezed_time, expected_result):
    """Test the calculate_worked_time function from the clocking module"""
    with freezegun.freeze_time(freezed_time):
        assert calculate_worked_time(user_id, time_range) == expected_result
