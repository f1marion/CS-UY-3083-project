from db_connection import get_db_connection

try:
    conn = get_db_connection()
    print("Database connection successful!")
    conn.close()
except mysql.connector.Error as err:
    print(f"Error: {err}")
