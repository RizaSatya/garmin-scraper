import psycopg


def connect_db(database_url: str):
    return psycopg.connect(database_url)
