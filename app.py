from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={  # Enable CORS for WDC and API
    r"/api/*": {"origins": "*"},
    r"/tableau-connector*": {"origins": "*"}
})

# Database configuration
DATABASE_FILE = os.getenv('DATABASE_FILE', 'feedback.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Return dictionaries
    return conn

def initialize_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comments TEXT NOT NULL,
                submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# Initialize database
initialize_database()

# --- Routes ---
@app.route('/')
def index():
    """Serve the feedback form"""
    return render_template('index.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """Handle form submissions"""
    try:
        data = request.form
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (name, email, rating, comments) VALUES (?, ?, ?, ?)",
            (data.get('name'), data.get('email'), data.get('rating'), data.get('comments')))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    """API endpoint for Tableau WDC"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id,
                name,
                email,
                rating,
                comments,
                datetime(submission_date, 'localtime') as submission_date
            FROM feedback 
            ORDER BY submission_date DESC
        """)
        feedback = [dict(row) for row in cursor.fetchall()]
        return jsonify(feedback)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/tableau-connector')
def tableau_connector():
    """Serve the Tableau WDC HTML file"""
    return send_from_directory('.', 'tableau_wdc.html')

# --- Tableau WDC Utilities ---
def generate_wdc_html():
    """Dynamically generates the WDC HTML (optional)"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Feedback WDC</title>
        <script src="https://connectors.tableau.com/libs/tableauwdc-2.3.latest.js"></script>
        <script>
            // Same WDC JavaScript as before
        </script>
    </head>
    <body>
        <button id="submitButton">Load Data</button>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)