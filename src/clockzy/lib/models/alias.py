from clockzy.lib.db.db_schema import ALIAS_TABLE
from clockzy.lib.handlers.codes import ITEM_ALREADY_EXISTS, ITEM_NOT_EXISTS
from clockzy.lib.db.database_interface import run_query_getting_status, item_exists, get_last_insert_id


class Alias:
    """Alias ORM (Object–relational mapping)

    Args:
        user_id (str): User identifier.
        alias (str): Aliases to add a second name to the specified user.

    Attributes:
        id (int): Alias identifier.
        user_id (str): User identifier.
        alias (str): Aliases to add a second name to the specified user.
    """
    def __init__(self, user_id, alias):
        self.id = None
        self.user_id = user_id
        self.alias = alias

    def __str__(self):
        """Define how the class object will be displayed."""
        return f"id: {self.id}, user_id: {self.user_id}, alias: {self.alias}"

    def save(self):
        """Save the alias information in the database.

        Returns:
            int: Operation status code.
        """
        add_alias_query = f"INSERT INTO {ALIAS_TABLE} VALUES (null, '{self.user_id}', '{self.alias}');"

        if self.id and item_exists({'id': self.id}, ALIAS_TABLE):
            return ITEM_ALREADY_EXISTS

        query_status_code = run_query_getting_status(add_alias_query)

        self.id = get_last_insert_id(ALIAS_TABLE)

        return query_status_code

    def delete(self):
        """Delete the alias data from the database.

        Returns:
            int: Operation status code.
        """
        delete_alias_query = f"DELETE FROM {ALIAS_TABLE} WHERE id='{self.id}'"

        if not item_exists({'id': self.id}, ALIAS_TABLE):
            return ITEM_NOT_EXISTS

        return run_query_getting_status(delete_alias_query)

    def update(self):
        """Update the alias information from the database.

        Returns:
            int: Operation status code.
        """
        update_alias_query = f"UPDATE {ALIAS_TABLE} SET user_id='{self.user_id}', " \
                             f"alias='{self.alias}' WHERE id='{self.id}'"

        if not item_exists({'id': self.id}, ALIAS_TABLE):
            return ITEM_NOT_EXISTS

        return run_query_getting_status(update_alias_query)
