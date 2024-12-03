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

@app.route('/register_staff', methods=['GET', 'POST'])
def register_staff():
    if request.method == 'POST':
        # Collect form data
        username = request.form['username']
        password = request.form['password']
        fname = request.form['fname']
        lname = request.form['lname']
        airline_name = request.form['airline_name']
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Airline_Staff (Username, Password, Fname, Lname, Airline_name)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, hashed_password.decode('utf-8'), fname, lname, airline_name))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register_staff.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form['user_type']  # 'customer' or 'staff'
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if user_type == 'customer':
            cursor.execute("SELECT * FROM Customer WHERE Email = %s", (username,))
        else:
            cursor.execute("SELECT * FROM Airline_Staff WHERE Username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and bcrypt.checkpw(password, user['Password'].encode('utf-8')):
            session['username'] = username
            session['user_type'] = user_type
            if user_type == 'customer':
                return redirect(url_for('customer_home'))
            else:
                return redirect(url_for('staff_home'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    return render_template('login.html')


