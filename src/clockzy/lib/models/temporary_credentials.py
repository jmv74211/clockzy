from clockzy.lib.db.db_schema import TEMPORARY_CREDENTIALS_TABLE
from clockzy.lib.utils.time import get_current_date_time, get_expiration_date_time
from clockzy.config.settings import CREDENTIALS_EXPIRATION_TIME
from clockzy.lib.handlers.codes import ITEM_ALREADY_EXISTS, ITEM_NOT_EXISTS
from clockzy.lib.db.database_interface import run_query_getting_status, item_exists


class TemporaryCredentials:
    def __init__(self, user_id, password=None):
        self.user_id = user_id
        self.password = password
        self.expiration_date_time = get_expiration_date_time(time_expiration=CREDENTIALS_EXPIRATION_TIME)

    def __str__(self):
        """Define how the class object will be displayed.

        Returns:
            int: Operation status code.
        """
        return f"user_id: {self.user_id}, password: {self.password}, expiration_date_time: {self.expiration_date_time}"

    def save(self):
        """Save the config information in the database.

        Returns:
            int: Operation status code.
        """
        add_temporary_credetials_query = f"INSERT INTO {TEMPORARY_CREDENTIALS_TABLE} VALUES ('{self.user_id}', " \
                                         f"'{self.password}', '{self.expiration_date_time}');"

        if item_exists({'user_id': self.user_id}, TEMPORARY_CREDENTIALS_TABLE):
            return ITEM_ALREADY_EXISTS

        return run_query_getting_status(add_temporary_credetials_query)

    def delete(self):
        """Delete the config data from the database.

        Returns:
            int: Operation status code.
        """
        delete_temporary_credetials_query = f"DELETE FROM {TEMPORARY_CREDENTIALS_TABLE} WHERE user_id='{self.user_id}'"

        if not item_exists({'user_id': self.user_id}, TEMPORARY_CREDENTIALS_TABLE):
            return ITEM_NOT_EXISTS

        return run_query_getting_status(delete_temporary_credetials_query)

    def update(self):
        """Update the config information from the database.

        Returns:
            int: Operation status code.
        """
        update_config_query = f"UPDATE {TEMPORARY_CREDENTIALS_TABLE} SET user_id='{self.user_id}', " \
                              f"password='{self.password}', expiration_date_time='{self.expiration_date_time}' " \
                              f"WHERE user_id='{self.user_id}'"

        if not item_exists({'user_id': self.user_id}, TEMPORARY_CREDENTIALS_TABLE):
            return ITEM_NOT_EXISTS

        return run_query_getting_status(update_config_query)
