import os
import pytest

from clockzy.lib.db.database_interface import get_clock_data_in_time_range
from clockzy.lib.test_framework.database import no_intratime_user_parameters
from clockzy.lib.models.user import User
from clockzy.lib.models.clock import Clock
from clockzy.lib.utils.file import read_yaml


test_data = read_yaml(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data',
                                   'test_get_clock_data_in_time_range.yaml'))
test_ids = [item['name'] for item in test_data['test_cases']]

test_parameters = [(item['datetime_from'], item['datetime_to'], item['expected_result']) for item in
                   test_data['test_cases']]


@pytest.fixture(scope="module")
def clock():
    # Add the test user
    clock_user = User(**no_intratime_user_parameters)
    clock_user.save()

    # Add the clocking data
    for item in test_data['clocks']:
        clock = Clock(item['user_id'], item['action'], item['date_time'])
        clock.save()

    yield

    # Delete the test user and all its data
    clock_user.delete()


@pytest.mark.parametrize('datetime_from, datetime_to, expected_result', test_parameters, ids=test_ids)
def test_get_clock_data_in_time_range(datetime_from, datetime_to, expected_result, clock):
    """Test the get_clock_data_in_time_range function from clockzy module"""
    user_id = no_intratime_user_parameters['id']
    assert len(get_clock_data_in_time_range(user_id, datetime_from, datetime_to)) == expected_result
