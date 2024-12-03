# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from db_connection import get_db_connection
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        # Collect form data
        email = request.form['email']
        password = request.form['password']
        fname = request.form['fname']
        lname = request.form['lname']
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Customer (Email, Password, Fname, Lname)
            VALUES (%s, %s, %s, %s)
        """, (email, hashed_password.decode('utf-8'), fname, lname))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register_customer.html')

