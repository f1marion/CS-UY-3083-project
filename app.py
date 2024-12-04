# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from db_connection import get_db_connection
import bcrypt
 
app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')  # Ensure you have an 'index.html' template


@app.route('/test')
def test():
    return 'Test page is working!'


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

@app.route('/')
def home():
    if 'username' in session:
        if session['user_type'] == 'customer':
            return redirect(url_for('customer_home'))
        elif session['user_type'] == 'staff':
            return redirect(url_for('staff_home'))
    return render_template('index.html')


@app.route('/customer_home')
def customer_home():
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    email = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT Flight.*
            FROM Flight
            JOIN Ticket ON Flight.Flight_num = Ticket.Flight_num
            WHERE Ticket.Customer_email = %s AND Flight.Departure_date_time >= NOW()
        """
        cursor.execute(query, (email,))
        flights = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return render_template('customer_home.html', flights=flights)



# app.py (continued)

@app.route('/search_flights', methods=['GET', 'POST'])
def search_flights():
    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        departure_date = request.form['departure_date']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT * FROM Flight
                WHERE Departure_airport = %s AND Arrival_airport = %s AND DATE(Departure_date_time) = %s
            """
            cursor.execute(query, (source, destination, departure_date))
            flights = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
        return render_template('flight_results.html', flights=flights)
    return render_template('search_flights.html')


# app.py (continued)

@app.route('/flight_status', methods=['GET', 'POST'])
def flight_status():
    if request.method == 'POST':
        airline_name = request.form['airline_name']
        flight_num = request.form['flight_num']
        date = request.form['date']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT Status FROM Flight
                WHERE Airline_name = %s AND Flight_num = %s AND DATE(Departure_date_time) = %s
            """
            cursor.execute(query, (airline_name, flight_num, date))
            status = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
        return render_template('flight_status_result.html', status=status)
    return render_template('flight_status.html')

# app.py (continued)



# app.py (continued)

@app.route('/my_flights')
def my_flights():
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    email = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT Flight.*, Ticket.Ticket_ID FROM Flight
            JOIN Ticket ON Flight.Flight_num = Ticket.Flight_num
            WHERE Ticket.Customer_email = %s AND Flight.Departure_date_time >= NOW()
        """
        cursor.execute(query, (email,))
        flights = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return render_template('my_flights.html', flights=flights)


# app.py (continued)

@app.route('/purchase_ticket/<flight_id>', methods=['GET', 'POST'])
def purchase_ticket(flight_id):
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    email = session['username']
    if request.method == 'POST':
        traveler_fname = request.form['traveler_fname']
        traveler_lname = request.form['traveler_lname']
        traveler_dob = request.form['traveler_dob']
        # Payment details can be collected here
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Generate new Ticket_ID
            cursor.execute("SELECT MAX(Ticket_ID) FROM Ticket")
            max_id = cursor.fetchone()[0] or 0
            new_ticket_id = max_id + 1
            # Insert into Ticket table
            cursor.execute("""
                INSERT INTO Ticket (Ticket_ID, traveler_Fname, traveler_Lname, traveler_DOB, Flight_num, Airline_name, Customer_email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (new_ticket_id, traveler_fname, traveler_lname, traveler_dob, flight_id, 'Airline_Name', email))  # Replace 'Airline_Name' appropriately
            conn.commit()
        except Exception as e:
            error = str(e)
            return render_template('purchase_ticket.html', error=error)
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('my_flights'))
    else:
        # Display flight details
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM Flight WHERE Flight_num = %s", (flight_id,))
            flight = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
        return render_template('purchase_ticket.html', flight=flight)

@app.route('/track_spending')
def track_spending():
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))

    email = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Adjusted query with correct column names
        query = """
            SELECT SUM(Ticket.Sold_price) AS total_spent
            FROM Ticket
            WHERE Ticket.Customer_email = %s AND
                  Ticket.Purchase_date_time >= DATE_SUB(NOW(), INTERVAL 1 YEAR)
        """
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        total_spent = result['total_spent'] if result['total_spent'] else 0
    finally:
        cursor.close()
        conn.close()

    return render_template('track_spending.html', total_spent=total_spent)

@app.route('/cancel_ticket/<int:ticket_id>', methods=['GET', 'POST'])
def cancel_ticket(ticket_id):
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))

    email = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verify that the ticket belongs to the user
        cursor.execute("""
            SELECT * FROM Ticket
            WHERE Ticket_ID = %s AND Customer_email = %s
        """, (ticket_id, email))
        ticket = cursor.fetchone()
        if not ticket:
            error = 'Ticket not found or does not belong to you.'
            return render_template('error.html', error=error)

        # Delete the ticket
        cursor.execute("""
            DELETE FROM Ticket WHERE Ticket_ID = %s
        """, (ticket_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        error = f'An error occurred: {str(e)}'
        return render_template('error.html', error=error)
    finally:
        cursor.close()
        conn.close()

    message = 'Your trip has been successfully cancelled.'
    return render_template('success.html', message=message)

@app.route('/rate_flights', methods=['GET', 'POST'])
def rate_flights():
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))

    email = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch past flights
        cursor.execute("""
            SELECT Flight.*, Ticket.Ticket_ID
            FROM Flight
            JOIN Ticket ON Flight.Flight_num = Ticket.Flight_num AND Flight.Airline_name = Ticket.Airline_name
            WHERE Ticket.Customer_email = %s AND Flight.Arrival_date_time < NOW()
        """, (email,))
        flights = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template('rate_flights.html', flights=flights)


@app.route('/rate_flight/<int:ticket_id>', methods=['GET', 'POST'])
def rate_flight(ticket_id):
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))

    email = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verify that the ticket belongs to the user
        cursor.execute("""
            SELECT Flight.*
            FROM Flight
            JOIN Ticket ON Flight.Flight_num = Ticket.Flight_num AND Flight.Airline_name = Ticket.Airline_name
            WHERE Ticket.Ticket_ID = %s AND Ticket.Customer_email = %s
        """, (ticket_id, email))
        flight = cursor.fetchone()
        if not flight:
            error = 'Flight not found or does not belong to you.'
            return render_template('error.html', error=error)

        if request.method == 'POST':
            rating = request.form['rating']
            comment = request.form['comment']
            # Insert rating and comment into the database
            cursor.execute("""
                INSERT INTO Rate (Ticket_ID, Rating, Comment)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE Rating = %s, Comment = %s
            """, (ticket_id, rating, comment, rating, comment))
            conn.commit()
            message = 'Your feedback has been submitted.'
            return render_template('success.html', message=message)
    except Exception as e:
        conn.rollback()
        error = f'An error occurred: {str(e)}'
        return render_template('error.html', error=error)
    finally:
        cursor.close()
        conn.close()

    return render_template('rate_flight.html', flight=flight)



@app.route('/logout')
def logout():
    # Remove user data from the session
    session.pop('username', None)
    session.pop('user_type', None)
    # Redirect the user to the login page or home page
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)



