import pytest
import freezegun
import os

from clockzy.lib.clocking import calculate_worked_time
from clockzy.lib.test_framework.database import no_intratime_user_parameters
from clockzy.lib.utils.file import read_yaml


test_data = read_yaml(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data',
                                   'test_calculate_worked_time.yaml'))
test_ids = [item['name'] for item in test_data]
test_parameters = [(item['clocks'], item['time_range'], item['expected_worked_time'], item['fake_current_date'])
                   for item in test_data]


@pytest.mark.parametrize('clocking_data, time_range, expected_worked_time, fake_current_date',
                         test_parameters, ids=test_ids)
def test_calculate_worked_time(clocking_data, time_range, expected_worked_time, fake_current_date, clock):
    """Test the calculate_worked_time function from the clocking module"""
    # Need to specify the offset due to the usage of timezones when getting the current datetime.
    with freezegun.freeze_time(fake_current_date, tz_offset=-1):
        assert calculate_worked_time(no_intratime_user_parameters['id'], time_range) == expected_worked_time
