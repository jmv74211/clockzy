import pytest
import os

from clockzy.lib.models.user import User
from clockzy.lib.models.clock import Clock
from clockzy.lib.models.command_history import CommandHistory
from clockzy.lib.models.config import Config
from clockzy.lib.models.alias import Alias
from clockzy.lib.utils.file import read_json
from clockzy.lib.test_framework.database import no_intratime_user_parameters


CLOCK_TEST_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'clock_data.json')


@pytest.fixture
def delete_post_user(user_parameters):
    yield
    user = User(**user_parameters)
    user.delete()


@pytest.fixture
def add_pre_user(user_parameters):
    user = User(**user_parameters)
    user.save()
    yield


@pytest.fixture
def delete_post_clock(clock_parameters):
    yield
    clock_id = clock_parameters['id']
    del clock_parameters['id']
    clock = Clock(**clock_parameters)
    clock.id = clock_id
    clock.delete()


@pytest.fixture
def add_pre_clock(clock_parameters):
    clock = Clock(**clock_parameters)
    clock.save()
    yield clock.id


@pytest.fixture
def delete_post_command_history(command_history_parameters):
    yield
    command_history_id = command_history_parameters['id']
    del command_history_parameters['id']
    command_history = CommandHistory(**command_history_parameters)
    command_history.id = command_history_id
    command_history.delete()


@pytest.fixture
def add_pre_command_history(command_history_parameters):
    command_history = CommandHistory(**command_history_parameters)
    command_history.save()
    yield command_history.id


@pytest.fixture
def delete_post_config(config_parameters):
    yield
    config = Config(**config_parameters)
    config.delete()


@pytest.fixture
def add_pre_config(config_parameters):
    config = Config(**config_parameters)
    config.save()
    yield


@pytest.fixture
def delete_post_alias(alias_parameters):
    yield
    alias_id = alias_parameters['id']
    del alias_parameters['id']
    alias = Alias(**alias_parameters)
    alias.id = alias_id
    alias.delete()


@pytest.fixture
def add_pre_alias(alias_parameters):
    alias = Alias(**alias_parameters)
    alias.save()
    yield alias.id


@pytest.fixture
def add_clock_test_data():
    """Fixture to add the testing clock data to the DB"""
    # Read clock data from json data file
    clock_data = read_json(CLOCK_TEST_DATA_FILE)

    # Add the test user
    clock_user = User(**no_intratime_user_parameters)
    clock_user.save()

    # Add the clocking data
    for item in clock_data:
        clock = Clock(item['user_id'], item['action'], item['date_time'])
        clock.save()

    yield

    # Delete the test user and all its data
    clock_user.delete()
