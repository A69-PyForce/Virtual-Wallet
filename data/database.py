from dotenv import load_dotenv
from mariadb.connections import Connection
from mariadb import ConnectionPool
import atexit
import os

load_dotenv()

# Load DB config from .env for database connection.
DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "database": os.getenv("DB_NAME"),
}

# Pool configuration
POOL_CONFIG = {
    "pool_name": "mypool",
    "pool_size": 20,
    "pool_reset_connection": True
}

# Create the connection pool
pool = ConnectionPool(
    **DB_CONFIG,
    **POOL_CONFIG
)

# Register cleanup function to close the pool when the application exits
atexit.register(pool.close)

def _get_connection() -> Connection:
    """
    Get a database connection from the pool.
    """
    return pool.get_connection()
    
def read_query(sql: str, sql_params=()) -> list[tuple]:
    """
    Read and execute a SQL query. For parameterized queries, use '?' as a placeholder \n
    for parameters and pass their values as a tuple in the sql_params argument.
    Args:
        sql (str): The SQL query string to execute.
        sql_params (tuple): The SQL query parameters. Defaults as an empty tuple.
        
    Returns:
        list: The result of the SQL query as a sequence of sequences, e.g. list(tuple).
    """
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, sql_params)
        return cursor.fetchall()
            
def insert_query(sql: str, sql_params=()) -> int:
    """
    Execute an INSERT SQL query and return the ID of the last inserted row.
    
    Args:
        sql (str): The INSERT SQL query string.
        sql_params (tuple): The parameters for the query. Defaults to an empty tuple.
        
    Returns:
        int: The ID of the last inserted row.
    """
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, sql_params)
        conn.commit()
        return cursor.lastrowid
            
def update_query(sql: str, sql_params=()) -> bool:
    """
    Execute an UPDATE SQL query.
    
    Args:
        sql (str): The UPDATE SQL query string.
        sql_params (tuple): The parameters for the query. Defaults to an empty tuple.
        
    Returns:
        bool: True if rows were affected, False otherwise.
    """
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, sql_params)
        conn.commit()
        return cursor.rowcount > 0