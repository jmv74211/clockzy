"""
Module to group calls to the database.
"""
from pymysql import MySQLError

from clockzy.lib.db.database import Database
from clockzy.lib.handlers.codes import SUCCESS, OPERATION_ERROR


def run_query(query):
    """Execute the query in the database.

    Args:
        query (String): Raw query to execute.

    Returns:
        - List(tuple): If SELECT query, returns the query results.
        - int: If non SELECT query, return the number of affected rows.
    Raises:
        MySQLError: If it is not a SELECT query and no row has been affected.
    """
    db = Database()
    results = db.run_query(query)

    if not query.startswith('SELECT') and not query.startswith('select') and results == 0:
        raise MySQLError(f"The {query} query has not affected any row")

    return results


def run_query_getting_status(query):
    """Execute a query and get the result code.

    Note: Do not use it when you need to get the results of the query (SELECT results).

    Args:
        query (String): Raw query to execute.

    Returns:
        int: Code status.
    """
    try:
        run_query(query)
        return SUCCESS
    except MySQLError:
        return OPERATION_ERROR


def get_last_insert_id(table_name, identifier='id'):
    """Get the last

    Precondition:
        - Table identifier must be AUTO_INCREMENT

    Note:
     - LAST_INSERT_ID() does not work for this case due to the mysql connections.

    Args:
        table_name (str): Table name to get the last inserted id.
        identifier (str): Identifier field name (usually will be called: id)

    Returns:
        int: Last inserted ID.
    """
    results = run_query(f"SELECT {identifier} from {table_name} ORDER BY id desc LIMIT 1")

    return results[0][0] if len(results) > 0 else 0


def build_select_query_from_object_parameters(parameters, table_name):
    """Build a SELECT query, using the item parameters as conditions (used in WHERE).

    Args:
        parameters (dict): Dictionary that contains the object parameters ({'colum_name': 'value', ...})
        table_name (str): Table where to make the search.

    Returns:
        str: Query using all parameters object as condition.

    """
    query_string = f"SELECT * FROM {table_name} WHERE "

    for parameter, value in parameters.items():
        formatted_value = f"'{value}'" if isinstance(value, str) else value
        query_string += f"{parameter}={formatted_value} and "

    # Delete the last "," character
    query_string = query_string[:-4]

    return query_string


def item_exists(object_parameters, table_name):
    """Check if there is one or more elements in the DB matching with the object parameters.

    Args:
        object_parameters (dict): Dictionary that contains the object parameters ({'colum_name': 'value', ...})
        table_name (str): Table where to make the search.

    Returns:
        boolean: True if there is one or more elements, False otherwise.
    """
    query = build_select_query_from_object_parameters(object_parameters, table_name)

    return len(run_query(query)) > 0


def get_database_data_from_objects(object_parameters, table_name):
    """Get the DB results from a query built with specified object parameters.

    Args:
        object_parameters (dict): Dictionary that contains the object parameters ({'colum_name': 'value', ...})
        table_name (str): Table where to make the search.

    Returns:
        list(tuple): Query results

    """
    result = run_query(build_select_query_from_object_parameters(object_parameters, table_name))

    return result if len(result) > 0 else []


def get_user_object(user_id):
    """Get the user object from the database data.

    Args:
        user_id (str): User identifier to get the data.

    Returns:
        User: User object with the DB data.
        None: If the user_id does not exist in the DB.

    """
    # Avoid circular import
    from clockzy.lib.db.db_schema import USER_TABLE
    from clockzy.lib.models.user import User

    user_data = get_database_data_from_objects({'id': user_id}, USER_TABLE)

    if len(user_data) == 0:
        return None

    user_object = User(user_data[0][0], user_data[0][1])
    user_object.password = user_data[0][2]
    user_object.email = user_data[0][3]
    user_object.entry_data = user_data[0][4]

    return user_object
