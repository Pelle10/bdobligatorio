from mysql.connector.pooling import MySQLConnectionPool
from config import DB_CONFIG

pool = MySQLConnectionPool(pool_name='mypool', pool_size=8, **DB_CONFIG)

def get_conn():
    return pool.get_connection()
