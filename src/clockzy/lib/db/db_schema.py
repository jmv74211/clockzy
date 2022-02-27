"""
Clockzy tables schema definitions.
"""

USER_TABLE = 'user'
CLOCK_TABLE = 'clock'
COMMANDS_HISTORY_TABLE = 'command_history'
CONFIG_TABLE = 'config'
ALIAS_TABLE = 'alias'
TEMPORARY_CREDENTIALS_TABLE = 'temporary_credentials'

USER_TABLE_SCHEMA = """ \
    CREATE TABLE IF NOT EXISTS user (
        id VARCHAR(50) NOT NULL,
        user_name VARCHAR(100) NOT NULL,
        password VARCHAR(100),
        email VARCHAR(200),
        entry_data DATETIME,
        last_registration_date DATETIME,
        PRIMARY KEY (id)
    )Engine=InnoDB;
"""

CLOCK_TABLE_SCHEMA = """ \
    CREATE TABLE IF NOT EXISTS clock (
        id INT NOT NULL AUTO_INCREMENT,
        user_id VARCHAR(50),
        action VARCHAR(20) NOT NULL,
        date_time DATETIME NOT NULL,
        local_date_time DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE ON UPDATE CASCADE
    )Engine=InnoDB;
"""

COMMANDS_HISTORY_TABLE_SCHEMA = """ \
    CREATE TABLE IF NOT EXISTS command_history (
        id INT NOT NULL AUTO_INCREMENT,
        user_id VARCHAR(50),
        command VARCHAR(50) NOT NULL,
        parameters VARCHAR(150),
        date_time DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE ON UPDATE CASCADE
    )Engine=InnoDB;
"""

CONFIG_TABLE_SCHEMA = """ \
    CREATE TABLE IF NOT EXISTS config (
        user_id VARCHAR(50),
        intratime_integration BOOLEAN NOT NULL,
        time_zone VARCHAR(50),
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE ON UPDATE CASCADE
    )Engine=InnoDB;
"""

ALIAS_TABLE_SCHEMA = """ \
    CREATE TABLE IF NOT EXISTS alias (
        id INT NOT NULL AUTO_INCREMENT,
        user_id VARCHAR(100) NOT NULL,
        alias VARCHAR(100) NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE ON UPDATE CASCADE
    )Engine=InnoDB;
"""

TEMPORARY_CREDENTIALS_TABLE_SCHEMA = """\
    CREATE TABLE IF NOT EXISTS temporary_credentials (
       user_id VARCHAR(100) NOT NULL,
       password VARCHAR(30) NOT NULL,
       expiration_date_time DATETIME NOT NULL,
       PRIMARY KEY (user_id),
       FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE ON UPDATE CASCADE
    )Engine=InnoDB;
"""
