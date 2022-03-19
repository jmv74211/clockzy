"""
Script to check if the database connection is healthy
"""

import pymysql
import sys
from time import sleep

from clockzy.lib.db.database import Database
from clockzy.config.settings import DB_NAME


MAX_WAITING_TIME = 200  # Seconds


def main():
    database = Database()

    # Update database name because the clockzy one may not be created yet
    database.database_name = 'mysql'

    retry_time = 10
    max_retries = int(MAX_WAITING_TIME / retry_time)
    num_retries = 0

    while not database.healthcheck():
        sleep(retry_time)
        num_retries += 1

        print(f"\033[93mWaiting for {database.host}:{database.port} connection to be ready. "
              f"Retry ({num_retries}/{max_retries})\033[0m")

        if num_retries == max_retries:
            print(f"\033[91mCannot establish connection with {database.host}:{database.port}\033[0m")
            sys.exit(-1)

    print(f"\033[92mHealthcheck OK: Connection ready from {database.host}:{database.port}\033[0m")


if __name__ == '__main__':
    main()
