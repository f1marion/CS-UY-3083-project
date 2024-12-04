# db_connection.py
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='pacomemarion', #replace
        password='Project1#', #replace
        database='Project1_1'
    )
