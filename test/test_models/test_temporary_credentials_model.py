import pytest

from clockzy.lib.models.temporary_credentials import TemporaryCredentials
from clockzy.lib.db.database_interface import item_exists
from clockzy.lib.test_framework.database import intratime_user_parameters, temporary_credentials_parameters
from clockzy.lib.db.db_schema import TEMPORARY_CREDENTIALS_TABLE
from clockzy.lib.handlers.codes import SUCCESS, ITEM_ALREADY_EXISTS


@pytest.mark.parametrize('user_parameters, credentials_parameters',
                         [(intratime_user_parameters, temporary_credentials_parameters)])
def test_save_temporary_credentials(credentials_parameters, add_pre_user, delete_post_user):
    test_temporary_credentials = TemporaryCredentials(**credentials_parameters)

    # Add the config and check that 1 row has been affected (no exception when running)
    assert test_temporary_credentials.save() == SUCCESS

    # If we try to add the same config, check that it can not be inserted
    assert test_temporary_credentials.save() == ITEM_ALREADY_EXISTS

    # Query and check that the config exist
    assert item_exists({'user_id': test_temporary_credentials.user_id}, TEMPORARY_CREDENTIALS_TABLE)


@pytest.mark.parametrize('user_parameters, credentials_parameters',
                         [(intratime_user_parameters, temporary_credentials_parameters)])
def test_update_config(credentials_parameters, add_pre_user, add_pre_temporary_credentials, delete_post_user):
    test_temporary_credentials = TemporaryCredentials(**credentials_parameters)

    # Update the expiration time info and check that 1 row has been affected (no exception when running)
    test_temporary_credentials.expiration_date_time = '2022-02-27 20:51:00'
    assert test_temporary_credentials.update() == SUCCESS

    # Query and check that the config exist
    assert item_exists({'user_id': test_temporary_credentials.user_id, 'expiration_date_time': '2022-02-27 20:51:00'},
                       TEMPORARY_CREDENTIALS_TABLE)


@pytest.mark.parametrize('user_parameters, credentials_parameters',
                         [(intratime_user_parameters, temporary_credentials_parameters)])
def test_delete_config(credentials_parameters, add_pre_user, add_pre_temporary_credentials, delete_post_user):
    test_temporary_credentials = TemporaryCredentials(**credentials_parameters)

    # Delete the config info and check that 1 row has been affected (no exception when running)
    assert test_temporary_credentials.delete() == SUCCESS

    # Query and check that the config does not exist
    assert not item_exists({'user_id': test_temporary_credentials.user_id}, TEMPORARY_CREDENTIALS_TABLE)
