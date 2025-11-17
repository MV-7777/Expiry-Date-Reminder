import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host='localhost',
        port=3306,
        user='root',
        password='1234',
        database='expiry_tracker'
    )
    return conn
