import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "host": "localhost",
    "database": "taskquest",
    "user": "postgres",
    "password": "Anurag29",
    "port": 5432
}

def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn