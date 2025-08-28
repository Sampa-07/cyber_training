from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Render-compatible configuration
app.secret_key = os.environ.get('SECRET_KEY', 'cybersecurity-demo-key-2024-change-in-production')

# Database configuration - works on Render and locally
DATABASE_PATH = 'database.db'
app.config['DATABASE'] = DATABASE_PATH

# Database setup
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id INTEGER NOT NULL,
                module_name TEXT NOT NULL,
                completion_status INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                score INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, module_name),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create password history table (for password module)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_history (
                user_id INTEGER NOT NULL,
                password TEXT NOT NULL,
                strength_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        db.commit()

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

# Initialize database on first request
@app.before_first_request
def create_tables():
    init_db()

# User authentication routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if user is None or not check_password_hash(user['password'], password):
        flash('Invalid username or password', 'danger')
        return redirect(url_for('index'))
    
    session.clear()
    session['user_id'] = user['id']
    session['username'] = user['username']
    
    # Initialize progress if not exists
    modules = ['password', 'phishing']
    for module in modules:
        progress = db.execute(
            'SELECT 1 FROM user_progress WHERE user_id = ? AND module_name = ?',
            (user['id'], module)
        ).fetchone()
        
        if not progress:
            db.execute(
                'INSERT INTO user_progress (user_id, module_name) VALUES (?, ?)',
                (user['id'], module)
            )
    
    db.commit()
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        
        if not username or not password:
            flash('Please enter username and password', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'danger')
            return redirect(url_for('register'))
        
        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Protected routes
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    db = get_db()
    
    # Get user progress
    progress = db.execute(
        'SELECT module_name, completion_status, score FROM user_progress WHERE user_id = ?',
        (session['user_id'],)
    ).fetchall()
    
    # Calculate overall progress
    completed_modules = sum(1 for p in progress if p['completion_status'] == 1)
    total_modules = len(progress)
    overall_percent = round((completed_modules / total_modules) * 100) if total_modules > 0 else 0
    
    return render_template('dashboard.html', 
                         username=session['username'],
                         progress=progress,
                         overall_percent=overall_percent)

@app.route('/module/password')
def password_module():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    db = get_db()
    
    # Get password history for the user
    history = db.execute(
        'SELECT password, strength_score, created_at FROM password_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (session['user_id'],)
    ).fetchall()
    
    # Get module progress
    module_progress = db.execute(
        'SELECT completion_status, score FROM user_progress WHERE user_id = ? AND module_name = ?',
        (session['user_id'], 'password')
    ).fetchone()
    
    return render_template('module_password.html',
                         history=history,
                         module_progress=module_progress)

@app.route('/module/phishing')
def phishing_module():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    db = get_db()
    
    # Get module progress
    module_progress = db.execute(
        'SELECT completion_status, score FROM user_progress WHERE user_id = ? AND module_name = ?',
        (session['user_id'], 'phishing')
    ).fetchone()
    
    return render_template('module_phishing.html',
                         module_progress=module_progress)

# API endpoints for module interactions
@app.route('/api/check_password', methods=['POST'])
def check_password():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    password = data.get('password', '')
    
    # Calculate password strength score
    strength_score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        strength_score += 20
    else:
        feedback.append("Use at least 8 characters")
    
    # Uppercase check
    if any(c.isupper() for c in password):
        strength_score += 20
    else:
        feedback.append("Add uppercase letters")
    
    # Lowercase check
    if any(c.islower() for c in password):
        strength_score += 20
    else:
        feedback.append("Add lowercase letters")
    
    # Number check
    if any(c.isdigit() for c in password):
        strength_score += 20
    else:
        feedback.append("Add numbers")
    
    # Special character check
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        strength_score += 20
    else:
        feedback.append("Add special characters")
    
    # Store password attempt
    db = get_db()
    db.execute(
        'INSERT INTO password_history (user_id, password, strength_score) VALUES (?, ?, ?)',
        (session['user_id'], password, strength_score)
    )
    db.commit()
    
    return jsonify({
        'status': 'success',
        'strength_score': strength_score,
        'feedback': feedback,
        'message': get_password_message(strength_score)
    })

def get_password_message(score):
    if score >= 80:
        return "Excellent! Very strong password."
    elif score >= 60:
        return "Good password, but could be stronger."
    elif score >= 40:
        return "Fair password. Add more variety."
    else:
        return "Weak password. Needs improvement."

@app.route('/api/update_password_progress', methods=['POST'])
def update_password_progress():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    quiz_score = data.get('quiz_score', 0)
    module_completed = data.get('module_completed', False)
    
    db = get_db()
    db.execute(
        'UPDATE user_progress SET score = ?, completion_status = ? '
        'WHERE user_id = ? AND module_name = ?',
        (quiz_score, 1 if module_completed else 0, session['user_id'], 'password')
    )
    db.commit()
    
    return jsonify({'status': 'success'})

@app.route('/api/update_phishing_progress', methods=['POST'])
def update_phishing_progress():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    quiz_score = data.get('quiz_score', 0)
    module_completed = data.get('module_completed', False)
    
    db = get_db()
    db.execute(
        'UPDATE user_progress SET score = ?, completion_status = ? '
        'WHERE user_id = ? AND module_name = ?',
        (quiz_score, 1 if module_completed else 0, session['user_id'], 'phishing')
    )
    db.commit()
    
    return jsonify({'status': 'success'})

# Health check endpoint for hosting platforms
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy', 
        'message': 'Cybersecurity Training Platform is running',
        'database': 'connected' if os.path.exists(DATABASE_PATH) else 'initializing'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Get port from environment (Render sets this automatically)
    port = int(os.environ.get('PORT', 5000))
    
    # Initialize database if it doesn't exist
    if not os.path.exists(DATABASE_PATH):
        init_db()
        print("Database initialized successfully!")
    
    # Run the application
    print(f"Starting Cybersecurity Training Platform on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
