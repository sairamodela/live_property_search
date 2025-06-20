from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

app = Flask(__name__)

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

@app.route('/')
def index():
    """Render the search page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)