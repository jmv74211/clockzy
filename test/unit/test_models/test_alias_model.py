import pytest

from clockzy.lib.models.alias import Alias
from clockzy.lib.test_framework.database import item_exists, intratime_user_parameters, alias_parameters
from clockzy.lib.db.db_schema import ALIAS_TABLE


# Pytest tierdown fixture is executed from righ to left position
@pytest.mark.parametrize('user_parameters, alias_parameters', [(intratime_user_parameters, alias_parameters)])
def test_save_alias(add_pre_user, delete_post_user, delete_post_alias):
    test_alias = Alias(**alias_parameters)

    # Add the alias and check that 1 row has been affected (no exception when running)
    test_alias.save()

    # Query and check that the alias exist
    assert item_exists({'user_name': test_alias.user_name}, ALIAS_TABLE)


@pytest.mark.parametrize('user_parameters, alias_parameters', [(intratime_user_parameters, alias_parameters)])
def test_update_alias(add_pre_user, add_pre_alias, delete_post_user, delete_post_alias):
    test_alias = Alias(**alias_parameters)

    # Update the alias info and check that 1 row has been affected (no exception when running)
    test_alias.alias = 'alias_updated'
    test_alias.update()

    # Query and check that the alias exist
    assert item_exists({'user_name': test_alias.user_name, 'alias': 'alias_updated'}, ALIAS_TABLE)


@pytest.mark.parametrize('user_parameters, alias_parameters', [(intratime_user_parameters, alias_parameters)])
def test_delete_alias(add_pre_user, add_pre_alias, delete_post_user):
    test_alias = Alias(**alias_parameters)

    # Delete the alias info and check that 1 row has been affected (no exception when running)
    test_alias.delete()

    # Query and check that the alias does not exist
    assert not item_exists({'user_name': test_alias.user_name}, ALIAS_TABLE)