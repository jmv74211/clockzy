"""
Script to initialize the Clockzy database and tables environment
"""

from clockzy.lib.db.database import Database
from clockzy.config.settings import DB_NAME
from clockzy.lib.db import db_schema as dbs

SCHEMAS = [dbs.USER_TABLE_SCHEMA, dbs.CLOCK_TABLE_SCHEMA, dbs.COMMANDS_HISTORY_TABLE_SCHEMA, dbs.CONFIG_TABLE_SCHEMA,
           dbs.ALIAS_TABLE_SCHEMA, dbs.TEMPORARY_CREDENTIALS_TABLE_SCHEMA]


def main():
    database = Database()

    # Create database if not exist
    database.create_database(DB_NAME)

    # Create the tables if not exist
    for table_schema in SCHEMAS:
        database.run_query(table_schema)


if __name__ == '__main__':
    main()
