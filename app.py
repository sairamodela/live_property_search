from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['username'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            port=DB_CONFIG['port']
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_users_table():
    """Create users table if it doesn't exist"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

# Create users table on startup
create_users_table()

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            return User(
                id=str(user_data['id']),
                username=user_data['username'],
                password_hash=user_data['password_hash']
            )
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username and password:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()

                # Check if username already exists
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    cursor.close()
                    conn.close()
                    return render_template('register.html', error="Username already exists")

                # Create new user
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, password_hash)
                )
                conn.commit()
                cursor.close()
                conn.close()

                return redirect(url_for('login'))
            else:
                return render_template('register.html', error="Database connection failed")

    return render_template('register.html', current_year=datetime.now().year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()

            if user_data and check_password_hash(user_data['password_hash'], password):
                user = User(
                    id=str(user_data['id']),
                    username=user_data['username'],
                    password_hash=user_data['password_hash']
                )
                login_user(user)
                return redirect(url_for('home'))
            else:
                return render_template('login.html', error="Invalid credentials")
        else:
            return render_template('login.html', error="Database connection failed")

    return render_template('login.html', current_year=datetime.now().year)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('index.html', username=current_user.username)

@app.route('/api/search', methods=['POST'])
@login_required
def search_properties():
    """
    Universal search endpoint that searches across all relevant columns
    """
    try:
        data = request.get_json()
        search_query = data.get('search', '').strip()

        # Advanced filters
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        min_bedrooms = data.get('min_bedrooms')
        property_type = data.get('property_type')

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = conn.cursor(dictionary=True)

        # Build the query
        query = "SELECT * FROM HouseData WHERE 1=1"
        params = []

        # Universal search across multiple columns
        if search_query:
            search_term = f"%{search_query}%"
            query += """ AND (
                property_id LIKE %s OR
                property_url LIKE %s OR
                address LIKE %s OR
                street_name LIKE %s OR
                city LIKE %s OR
                state LIKE %s OR
                postcode LIKE %s OR
                property_type LIKE %s OR
                agency_name LIKE %s OR
                CONCAT(address, ' ', city, ' ', state, ' ', postcode) LIKE %s OR
                CONCAT(street_name, ' ', city) LIKE %s OR
                CONCAT(city, ', ', state) LIKE %s
            )"""
            # Add the search term for each column
            params.extend([search_term] * 12)

        # Add advanced filters
        if min_price:
            query += " AND price >= %s"
            params.append(float(min_price))

        if max_price:
            query += " AND price <= %s"
            params.append(float(max_price))

        if min_bedrooms:
            query += " AND bedroom_number >= %s"
            params.append(int(min_bedrooms))

        if property_type:
            query += " AND property_type = %s"
            params.append(property_type)

        # Order by relevance (price by default)
        query += " ORDER BY price ASC LIMIT 500"

        # Execute query
        cursor.execute(query, params)
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert datetime objects to strings
        for row in results:
            for key, value in row.items():
                if hasattr(value, 'isoformat'):
                    row[key] = value.isoformat()

        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/property/<property_id>', methods=['GET'])
@login_required
def get_property_details(property_id):
    """Get details for a specific property"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM HouseData WHERE property_id = %s"
        cursor.execute(query, (property_id,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            # Convert datetime objects to strings
            for key, value in result.items():
                if hasattr(value, 'isoformat'):
                    result[key] = value.isoformat()

            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Property not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/status')
def auth_status():
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'username': current_user.username if current_user.is_authenticated else None
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001)  # or any unused port