# db_connection.py
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='your_db_username', #replace
        password='your_db_password', #replace
        database='Project1_1'
    )
