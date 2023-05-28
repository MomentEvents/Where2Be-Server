import psycopg2
from psycopg2 import sql
import os

def test_sql_health():
    try:
        conn = get_sql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
    except psycopg2.Error as e:
        print("Error connecting to the sql database:", e)
        return False
    return True

def get_sql_connection():

    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")

    conn = psycopg2.connect(
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,  # use the appropriate value for a remote host
        port=POSTGRES_PORT
    )

    return conn