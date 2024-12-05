# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from db_connection import get_db_connection
from datetime import datetime, timedelta
import bcrypt
from urllib.parse import quote, unquote
from markupsafe import Markup

from urllib.parse import unquote_plus

 
app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')  # Ensure you have an 'index.html' template

@app.template_filter('url_encode')
def url_encode(s):
    from urllib.parse import quote_plus
    return quote_plus(str(s))

# Custom Jinja filter
@app.template_filter('url_encode')
def url_encode(s):
    return quote(str(s))

from flask import flash  # Import flash for messaging

@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        # Collect form data
        email = request.form['email']
        password = request.form['password']
        fname = request.form['fname']
        lname = request.form['lname']
        building_number = request.form['building_number']
        street_name = request.form['street_name']
        apartment_number = request.form.get('apartment_number')  # Optional
        city = request.form['city']
        state = request.form['state']
        zip_code = request.form['zip_code']
        passport_number = request.form['passport_number']
        passport_expiration = request.form['passport_expiration']
        passport_country = request.form['passport_country']
        dob = request.form['dob']

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Customer (Email, Password, Fname, Lname, Building_number, Street_name,
                Apartment_number, City, State, Zip_code, Passport_number, Passport_expiration, Passport_country, DOB)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                email, hashed_password.decode('utf-8'), fname, lname, building_number, street_name,
                apartment_number, city, state, zip_code, passport_number, passport_expiration,
                passport_country, dob
            ))
            conn.commit()
            # Instead of rendering the login template, redirect to the login route
            flash("Registration successful. Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            error = f"An error occurred: {str(e)}"
            return render_template('register_customer.html', error=error)
        finally:
            cursor.close()
            conn.close()
    return render_template('register_customer.html')



from flask import flash  # Import flash for messaging

@app.route('/register_staff', methods=['GET', 'POST'])
def register_staff():
    if request.method == 'POST':
        # Collect form data
        username = request.form['username']
        password = request.form['password']
        fname = request.form['fname']
        lname = request.form['lname']
        dob = request.form['dob']
        airline_name = request.form['airline_name']

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Airline_Staff (Username, Password, Fname, Lname, DOB, Airline_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, hashed_password.decode('utf-8'), fname, lname, dob, airline_name))
            conn.commit()
            # Use flash to pass a success message
            flash("Registration successful. Please log in.")
            # Redirect to the login route
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            error = f"An error occurred: {str(e)}"
            return render_template('register_staff.html', error=error)
        finally:
            cursor.close()
            conn.close()
    return render_template('register_staff.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Determine user type
        user_type = request.form['user_type']
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if user_type == 'customer':
            # Login for customer
            cursor.execute("SELECT * FROM Customer WHERE Email = %s", (username_or_email,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['Password'].encode('utf-8')):
                session['username'] = user['Email']
                session['user_type'] = 'customer'
                return redirect(url_for('customer_home'))
            else:
                error = 'Invalid email or password.'
                return render_template('login.html', error=error)
        elif user_type == 'staff':
            # Login for staff
            cursor.execute("SELECT * FROM Airline_Staff WHERE Username = %s", (username_or_email,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['Password'].encode('utf-8')):
                session['username'] = user['Username']
                session['user_type'] = 'staff'
                return redirect(url_for('staff_home'))
            else:
                error = 'Invalid username or password.'
                return render_template('login.html', error=error)
        else:
            error = 'Invalid user type.'
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
    SELECT Flight.*, Ticket.Ticket_ID
    FROM Flight
    JOIN Ticket ON Flight.Airline_name = Ticket.Airline_name
               AND Flight.Flight_num = Ticket.Flight_num
               AND Flight.Departure_date_time = Ticket.Departure_date_time
    WHERE Ticket.Customer_email = %s
      AND Flight.Departure_date_time >= NOW()
"""

        cursor.execute(query, (email,))
        flights = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return render_template('my_flights.html', flights=flights)


# app.py (continued)

from datetime import datetime
import uuid
from urllib.parse import unquote_plus

@app.route('/purchase_ticket/<airline_name>/<flight_num>/<departure_date_time>', methods=['GET', 'POST'])
def purchase_ticket(airline_name, flight_num, departure_date_time):
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))

    email = session['username']

    # Decode the URL-encoded departure_date_time
    departure_date_time = unquote_plus(departure_date_time)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch flight details along with the number of seats
        cursor.execute("""
            SELECT Flight.*, Airplane.Num_seats
            FROM Flight
            JOIN Airplane ON Flight.Airline_name = Airplane.Airline_name AND Flight.Plane_ID = Airplane.Plane_ID
            WHERE Flight.Airline_name = %s AND Flight.Flight_num = %s AND Flight.Departure_date_time = %s
        """, (airline_name, flight_num, departure_date_time))
        flight = cursor.fetchone()
        if not flight:
            error = 'Flight not found.'
            return render_template('error.html', error=error)

        # Check seat availability
        num_seats = flight['Num_seats']
        seats_booked = flight['Seats_booked'] or 0
        if seats_booked >= num_seats:
            error = 'No seats available on this flight.'
            return render_template('error.html', error=error)

        # Handle POST request for purchasing the ticket
        if request.method == 'POST':
            # Collect form data
            traveler_Fname = request.form['traveler_Fname']
            traveler_Lname = request.form['traveler_Lname']
            traveler_DOB = request.form['traveler_DOB']
            card_type = request.form['card_type']
            card_number = request.form['card_number']
            name_on_card = request.form['name_on_card']
            expiration_date = request.form['expiration_date']

            # Generate a new Ticket_ID using UUID
            new_ticket_id = str(uuid.uuid4())

            # Get Sold_Price from the flight's Base_price
            sold_price = flight['Base_price']

            # Get current time for Purchase_date_time
            purchase_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Use exact values from the flight for foreign key columns
            fk_airline_name = flight['Airline_name']
            fk_flight_num = flight['Flight_num']
            fk_departure_date_time = flight['Departure_date_time'].strftime('%Y-%m-%d %H:%M:%S')

            # Format dates properly
            traveler_DOB_formatted = datetime.strptime(traveler_DOB, '%Y-%m-%d').strftime('%Y-%m-%d')
            expiration_date_formatted = datetime.strptime(expiration_date, '%Y-%m-%d').strftime('%Y-%m-%d')

            # Insert into Ticket table
            cursor.execute("""
                INSERT INTO Ticket (
                    Ticket_ID, traveler_Fname, traveler_Lname, traveler_DOB, Sold_Price, Card_type,
                    Card_number, Name_on_card, Expiration_date, Purchase_date_time, Flight_num,
                    Airline_name, Departure_date_time, Customer_email
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                new_ticket_id, traveler_Fname, traveler_Lname, traveler_DOB_formatted, sold_price, card_type,
                card_number, name_on_card, expiration_date_formatted, purchase_date_time, fk_flight_num,
                fk_airline_name, fk_departure_date_time, email
            ))

            # Update Seats_booked in Flight table
            #cursor.execute("""
                #UPDATE Flight
                #SET Seats_booked = Seats_booked + 1
                #WHERE Airline_name = %s AND Flight_num = %s AND Departure_date_time = %s
            #""", (fk_airline_name, fk_flight_num, fk_departure_date_time))

            conn.commit()

            # After successful purchase
            message = 'Ticket purchased successfully.'
            return render_template('success.html', message=message)
    except Exception as e:
        conn.rollback()
        # Log the error for debugging
        app.logger.error(f'Error purchasing ticket: {e}')
        error = f'An error occurred: {str(e)}'
        return render_template('error.html', error=error)
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

@app.route('/cancel_trip', methods=['GET', 'POST'])
def cancel_trip():
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    email = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Handle POST request (cancel the trip)
        if request.method == 'POST':
            ticket_id = request.form.get('ticket_id')
            if ticket_id:
                # Delete the ticket from the database
                try:
                    cursor.execute("DELETE FROM Ticket WHERE Ticket_ID = %s", (ticket_id,))
                    conn.commit()
                    flash("Ticket canceled successfully.")
                except Exception as e:
                    conn.rollback()
                    flash(f"An error occurred while canceling the ticket: {str(e)}")

        # Fetch upcoming flights that can be canceled
        query = """
            SELECT Flight.*, Ticket.Ticket_ID
            FROM Flight
            JOIN Ticket ON Flight.Flight_num = Ticket.Flight_num AND Flight.Airline_name = Ticket.Airline_name AND Flight.Departure_date_time = Ticket.Departure_date_time
            WHERE Ticket.Customer_email = %s AND Flight.Departure_date_time > NOW()
        """
        cursor.execute(query, (email,))
        flights = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template('cancel_trip.html', flights=flights)



@app.route('/rate_flights')
def rate_flights():
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))

    email = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch past flights
        cursor.execute("""
            SELECT Flight.*, Ticket.Ticket_ID, Flight.Departure_date_time
            FROM Flight
            JOIN Ticket ON Flight.Flight_num = Ticket.Flight_num AND Flight.Airline_name = Ticket.Airline_name
            WHERE Ticket.Customer_email = %s AND Flight.Arrival_date_time < NOW()
        """, (email,))
        flights = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template('rate_flights.html', flights=flights)


@app.route('/rate_flight/<ticket_id>', methods=['GET', 'POST'])
def rate_flight(ticket_id):
    if 'username' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))

    email = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verify that the ticket belongs to the user and get flight details
        cursor.execute("""
            SELECT Flight.*, Ticket.Ticket_ID, Flight.Departure_date_time, Flight.Arrival_date_time
            FROM Flight
            JOIN Ticket ON Flight.Flight_num = Ticket.Flight_num 
                       AND Flight.Airline_name = Ticket.Airline_name 
                       AND Flight.Departure_date_time = Ticket.Departure_date_time
            WHERE Ticket.Ticket_ID = %s AND Ticket.Customer_email = %s
        """, (ticket_id, email))
        flight = cursor.fetchone()
        if not flight:
            error = 'Flight not found or does not belong to you.'
            return render_template('error.html', error=error)

        # Check if the flight has already arrived
        flight_arrival_time = flight.get('Arrival_date_time')
        if flight_arrival_time and flight_arrival_time > datetime.now():
            error = 'You can only rate flights that have already occurred.'
            return render_template('error.html', error=error)

        if request.method == 'POST':
            rating = request.form.get('rating')
            comment = request.form.get('comment')

            # Validate rating
            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    raise ValueError
            except (ValueError, TypeError):
                error = 'Rating must be an integer between 1 and 5.'
                return render_template('rate_flight.html', flight=flight, error=error, review=None)

            # Insert or update review in the 'reviews' table
            cursor.execute("""
                INSERT INTO reviews (Email, Airline_name, Flight_num, Departure_date_time, Ratings, Comments)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE Ratings = %s, Comments = %s
            """, (
                email, flight['Airline_name'], flight['Flight_num'], flight['Departure_date_time'],
                rating, comment, rating, comment
            ))
            conn.commit()
            message = 'Your feedback has been submitted.'
            return render_template('success.html', message=message)
    except Exception as e:
        conn.rollback()
        # Log the error for debugging
        app.logger.error(f'Error in rate_flight: {e}')
        error = f'An error occurred: {str(e)}'
        return render_template('error.html', error=error)
    finally:
        cursor.close()
        conn.close()

    # Fetch existing review if any
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT Ratings, Comments FROM reviews
            WHERE Email = %s AND Airline_name = %s AND Flight_num = %s AND Departure_date_time = %s
        """, (email, flight['Airline_name'], flight['Flight_num'], flight['Departure_date_time']))
        review = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    return render_template('rate_flight.html', flight=flight, review=review)



@app.route('/staff_home', methods=['GET', 'POST'])
def staff_home():
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the airline name associated with the staff member
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()['Airline_name']

    # Default date range: next 30 days
    today = datetime.now()
    default_end_date = today + timedelta(days=30)

    if request.method == 'POST':
        # Collect filter criteria from the form
        start_date = request.form.get('start_date') or today.strftime('%Y-%m-%d')
        end_date = request.form.get('end_date') or default_end_date.strftime('%Y-%m-%d')
        source = request.form.get('source')
        destination = request.form.get('destination')

        query = """
            SELECT * FROM Flight
            WHERE Airline_name = %s AND DATE(Departure_date_time) BETWEEN %s AND %s
        """
        params = [airline, start_date, end_date]

        if source:
            query += " AND Departure_airport = %s"
            params.append(source)
        if destination:
            query += " AND Arrival_airport = %s"
            params.append(destination)

        cursor.execute(query, params)
    else:
        # Default view: next 30 days
        cursor.execute("""
            SELECT * FROM Flight
            WHERE Airline_name = %s AND Departure_date_time BETWEEN %s AND %s
        """, (airline, today, default_end_date))

    flights = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('staff_home.html', flights=flights)



@app.route('/view_customers/<flight_num>/<departure_date_time>')
def view_customers(flight_num, departure_date_time):
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    departure_date_time = unquote_plus(departure_date_time)
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get airline name
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()['Airline_name']

    cursor.execute("""
        SELECT Customer.*
        FROM Customer
        JOIN Ticket ON Customer.Email = Ticket.Customer_email
        WHERE Ticket.Airline_name = %s AND Ticket.Flight_num = %s AND Ticket.Departure_date_time = %s
    """, (airline, flight_num, departure_date_time))

    customers = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('view_customers.html', customers=customers)


@app.route('/create_flight', methods=['GET', 'POST'])
def create_flight():
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))
    
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get airline name associated with the staff member
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()['Airline_name']
    
    # Get list of airplanes for the airline
    cursor.execute("SELECT Plane_ID, Num_seats FROM Airplane WHERE Airline_name = %s", (airline,))
    airplanes = cursor.fetchall()
    
    # Get list of airports
    cursor.execute("SELECT Code FROM Airport")
    airports = cursor.fetchall()
    
    if request.method == 'POST':
        flight_num = request.form['flight_num']
        departure_date_time = request.form['departure_date_time']
        arrival_date_time = request.form['arrival_date_time']
        departure_airport = request.form['departure_airport']
        arrival_airport = request.form['arrival_airport']
        base_price = request.form['base_price']
        status = request.form['status']
        plane_id = request.form['plane_id']
        seats_booked = request.form['seats_booked']
        
        # Data validation
        # Ensure seats_booked is a non-negative integer
        if not seats_booked.isdigit() or int(seats_booked) < 0:
            error = "Seats booked must be a non-negative integer."
            return render_template('create_flight.html', airplanes=airplanes, airports=airports, error=error)
        seats_booked = int(seats_booked)
        
        # Get the capacity of the selected airplane
        plane_capacity = None
        for plane in airplanes:
            if plane['Plane_ID'] == plane_id:
                plane_capacity = plane['Num_seats']
                break
        if plane_capacity is None:
            error = "Invalid airplane selected."
            return render_template('create_flight.html', airplanes=airplanes, airports=airports, error=error)
        
        # Check that seats_booked does not exceed capacity
        if seats_booked > plane_capacity:
            error = f"Seats booked ({seats_booked}) cannot exceed the airplane's capacity ({plane_capacity})."
            return render_template('create_flight.html', airplanes=airplanes, airports=airports, error=error)
        
        # Ensure departure and arrival airports are different
        if departure_airport == arrival_airport:
            error = "Departure and arrival airports cannot be the same."
            return render_template('create_flight.html', airplanes=airplanes, airports=airports, error=error)
        
        # Insert flight into database
        try:
            cursor.execute("""
                INSERT INTO Flight (Airline_name, Flight_num, Departure_date_time, Arrival_date_time, Departure_airport,
                Arrival_airport, Base_price, Status, Plane_ID, Seats_booked)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (airline, flight_num, departure_date_time, arrival_date_time, departure_airport,
                  arrival_airport, base_price, status, plane_id, seats_booked))
            conn.commit()
            message = "Flight created successfully."
            return render_template('success.html', message=message)
        except Exception as e:
            conn.rollback()
            error = f"An error occurred: {str(e)}"
            return render_template('create_flight.html', airplanes=airplanes, airports=airports, error=error)
        finally:
            cursor.close()
            conn.close()
    else:
        cursor.close()
        conn.close()
        return render_template('create_flight.html', airplanes=airplanes, airports=airports)



@app.route('/change_status', methods=['GET', 'POST'])
def change_status():
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get airline name
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()[0]

    if request.method == 'POST':
        flight_num = request.form['flight_num']
        departure_date_time = request.form['departure_date_time']
        new_status = request.form['status']

        try:
            cursor.execute("""
                UPDATE Flight
                SET Status = %s
                WHERE Airline_name = %s AND Flight_num = %s AND Departure_date_time = %s
            """, (new_status, airline, flight_num, departure_date_time))
            conn.commit()
            message = "Flight status updated successfully."
            return render_template('success.html', message=message)
        except Exception as e:
            conn.rollback()
            error = f"An error occurred: {str(e)}"
            return render_template('error.html', error=error)
    cursor.close()
    conn.close()
    return render_template('change_status.html')


@app.route('/add_airplane', methods=['GET', 'POST'])
def add_airplane():
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get airline name associated with the staff member
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()['Airline_name']

    if request.method == 'POST':
        plane_id = request.form['plane_id']
        num_seats = request.form['num_seats']
        manufacturing_company = request.form['manufacturing_company']
        model_number = request.form['model_number']
        manufacturing_date = request.form['manufacturing_date']
        age = request.form['age']

        try:
            cursor.execute("""
                INSERT INTO Airplane (Airline_name, Plane_ID, Num_seats, Manufacturing_company, Model_number, Manufacturing_date, Age)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (airline, plane_id, num_seats, manufacturing_company, model_number, manufacturing_date, age))
            conn.commit()
            message = "Airplane added successfully."

            # Fetch all airplanes to display
            cursor.execute("SELECT * FROM Airplane WHERE Airline_name = %s", (airline,))
            airplanes = cursor.fetchall()
            return render_template('view_airplanes.html', airplanes=airplanes, message=message)
        except Exception as e:
            conn.rollback()
            error = f"An error occurred: {str(e)}"
            return render_template('add_airplane.html', error=error)
        finally:
            cursor.close()
            conn.close()

    cursor.execute("SELECT * FROM Airplane WHERE Airline_name = %s", (airline,))
    airplanes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('add_airplane.html', airplanes=airplanes)



@app.route('/add_airport', methods=['GET', 'POST'])
def add_airport():
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        city = request.form['city']
        country = request.form['country']
        airport_type = request.form['airport_type']
        num_terminals = request.form['num_terminals']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Airport (Code, Name, City, Country, Type, Num_terminals)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (code, name, city, country, airport_type, num_terminals))
            conn.commit()
            message = "Airport added successfully."
            return render_template('success.html', message=message)
        except Exception as e:
            conn.rollback()
            error = f"An error occurred: {str(e)}"
            return render_template('add_airport.html', error=error)
        finally:
            cursor.close()
            conn.close()
    return render_template('add_airport.html')



@app.route('/view_ratings', methods=['GET', 'POST'])
def view_ratings():
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get airline name
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()['Airline_name']

    # Fetch flights with average ratings
    cursor.execute("""
        SELECT Flight.Flight_num, Flight.Departure_date_time,
               AVG(Reviews.Ratings) AS average_rating
        FROM Flight
        LEFT JOIN Reviews ON Flight.Airline_name = Reviews.Airline_name
                          AND Flight.Flight_num = Reviews.Flight_num
                          AND Flight.Departure_date_time = Reviews.Departure_date_time
        WHERE Flight.Airline_name = %s
        GROUP BY Flight.Flight_num, Flight.Departure_date_time
    """, (airline,))

    flights = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('view_ratings.html', flights=flights)


@app.route('/view_comments/<flight_num>/<departure_date_time>')
def view_comments(flight_num, departure_date_time):
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    departure_date_time = unquote_plus(departure_date_time)
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get airline name
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()['Airline_name']

    cursor.execute("""
        SELECT Reviews.Ratings, Reviews.Comments, Customer.Fname, Customer.Lname
        FROM Reviews
        JOIN Customer ON Reviews.Email = Customer.Email
        WHERE Reviews.Airline_name = %s AND Reviews.Flight_num = %s AND Reviews.Departure_date_time = %s
    """, (airline, flight_num, departure_date_time))

    reviews = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('view_comments.html', reviews=reviews, flight_num=flight_num)

@app.route('/schedule_maintenance', methods=['GET', 'POST'])
def schedule_maintenance():
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get airline name associated with the staff member
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()['Airline_name']

    # Fetch airplanes owned by the airline
    cursor.execute("SELECT * FROM Airplane WHERE Airline_name = %s", (airline,))
    airplanes = cursor.fetchall()

    if request.method == 'POST':
        plane_id = request.form['plane_id']
        start_datetime = request.form['start_datetime']
        end_datetime = request.form['end_datetime']

        # Check if airplane is available (not under maintenance or assigned to a flight during that period)
        try:
            # Adjusted column names to match database schema
            cursor.execute("""
                SELECT * FROM Maintenance
                WHERE Airline_name = %s AND Plane_ID = %s
                AND (
                    (%s BETWEEN Start_date_time AND End_date_time) OR
                    (%s BETWEEN Start_date_time AND End_date_time) OR
                    (Start_date_time BETWEEN %s AND %s)
                )
            """, (airline, plane_id, start_datetime, end_datetime, start_datetime, end_datetime))
            maintenance_conflicts = cursor.fetchall()

            # Check for flights assigned to the airplane during that period
            cursor.execute("""
                SELECT * FROM Flight
                WHERE Airline_name = %s AND Plane_ID = %s
                AND (
                    Departure_date_time BETWEEN %s AND %s OR
                    Arrival_date_time BETWEEN %s AND %s
                )
            """, (airline, plane_id, start_datetime, end_datetime, start_datetime, end_datetime))

            flight_conflicts = cursor.fetchall()

            if maintenance_conflicts or flight_conflicts:
                error = "The airplane is already scheduled for maintenance or assigned to a flight during this period."
                return render_template('schedule_maintenance.html', airplanes=airplanes, error=error)

            # Schedule maintenance
            cursor.execute("""
                INSERT INTO Maintenance (Airline_name, Plane_ID, Start_date_time, End_date_time)
                VALUES (%s, %s, %s, %s)
            """, (airline, plane_id, start_datetime, end_datetime))
            conn.commit()
            message = "Maintenance scheduled successfully."
            return render_template('success.html', message=message)
        except Exception as e:
            conn.rollback()
            error = f"An error occurred: {str(e)}"
            return render_template('error.html', error=error)
    cursor.close()
    conn.close()
    return render_template('schedule_maintenance.html', airplanes=airplanes)



@app.route('/view_frequent_customers', methods=['GET', 'POST'])
def view_frequent_customers():
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get airline name
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()['Airline_name']

    # Calculate date one year ago
    one_year_ago = datetime.now() - timedelta(days=365)

    # Get frequent customers
    cursor.execute("""
        SELECT Customer.Email, Customer.Fname, Customer.Lname, COUNT(*) AS flight_count
        FROM Ticket
        JOIN Customer ON Ticket.Customer_email = Customer.Email
        WHERE Ticket.Airline_name = %s AND Ticket.Purchase_date_time >= %s
        GROUP BY Customer.Email
        ORDER BY flight_count DESC
        LIMIT 5
    """, (airline, one_year_ago))
    frequent_customers = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('view_frequent_customers.html', frequent_customers=frequent_customers)


@app.route('/view_customer_flights/<customer_email>')
def view_customer_flights(customer_email):
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    customer_email = unquote_plus(customer_email)
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get airline name
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()['Airline_name']

    # Get customer flights
    cursor.execute("""
        SELECT Flight.*
        FROM Flight
        JOIN Ticket ON Flight.Airline_name = Ticket.Airline_name
                     AND Flight.Flight_num = Ticket.Flight_num
                     AND Flight.Departure_date_time = Ticket.Departure_date_time
        WHERE Ticket.Customer_email = %s AND Flight.Airline_name = %s
    """, (customer_email, airline))
    flights = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('view_customer_flights.html', flights=flights, customer_email=customer_email)


@app.route('/view_revenue', methods=['GET'])
def view_revenue():
    if 'username' not in session or session['user_type'] != 'staff':
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get airline name
    cursor.execute("SELECT Airline_name FROM Airline_Staff WHERE Username = %s", (username,))
    airline = cursor.fetchone()[0]

    # Calculate dates
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)
    one_year_ago = today - timedelta(days=365)

    # Revenue in the last month
    cursor.execute("""
        SELECT SUM(Sold_Price) FROM Ticket
        WHERE Airline_name = %s AND Purchase_date_time >= %s
    """, (airline, one_month_ago))
    month_revenue = cursor.fetchone()[0] or 0.0

    # Revenue in the last year
    cursor.execute("""
        SELECT SUM(Sold_Price) FROM Ticket
        WHERE Airline_name = %s AND Purchase_date_time >= %s
    """, (airline, one_year_ago))
    year_revenue = cursor.fetchone()[0] or 0.0

    cursor.close()
    conn.close()
    return render_template('view_revenue.html', month_revenue=month_revenue, year_revenue=year_revenue)






@app.route('/logout')
def logout():
    # Remove user data from the session
    session.pop('username', None)
    session.pop('user_type', None)
    # Redirect the user to the login page or home page
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)
