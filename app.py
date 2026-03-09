from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import random
import string
from datetime import datetime, timedelta
import functools

app = Flask(__name__)
app.secret_key = 'HOTSPOT_SECURE_KEY' # In production, use a real secret

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vouchers (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 code TEXT UNIQUE,
                 duration_days INTEGER,
                 status TEXT DEFAULT 'unused',
                 created_at DATETIME,
                 activated_at DATETIME,
                 mac_address TEXT,
                 expires_at DATETIME
                 )''')
    conn.commit()
    conn.close()

init_db()

# --- SECURITY DECORATOR ---
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---

# 1. THE CAPTIVE PORTAL LOGIN (User View)
@app.route('/')
@app.route('/login')
def login():
    # Cudy redirects here with params: gw_id, client_mac, etc.
    mac = request.args.get('mac')
    gw_url = request.args.get('gw_url') # The Cudy's local URL for auth
    return render_template('login.html', mac=mac, gw_url=gw_url)

# 2. VOUCHER VALIDATION LOGIC
@app.route('/auth', methods=['POST'])
def authenticate():
    code = request.form.get('voucher').strip().upper()
    mac = request.form.get('mac')
    gw_url = request.form.get('gw_url')

    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM vouchers WHERE code=?", (code,))
    v = c.fetchone()

    if not v:
        flash("Invalid voucher code.")
        return redirect(url_for('login', mac=mac, gw_url=gw_url))

    # ID, CODE, DURATION, STATUS, CREATED, ACTIVATED, MAC, EXPIRES
    v_id, v_code, duration, status, created, activated, v_mac, expires = v

    if status == 'active' and v_mac != mac:
        flash("Voucher is already in use by another device.")
        return redirect(url_for('login', mac=mac, gw_url=gw_url))
    
    if status == 'expired':
        flash("Voucher has expired.")
        return redirect(url_for('login', mac=mac, gw_url=gw_url))

    # Activate Unused Voucher
    if status == 'unused':
        now = datetime.now()
        expiry = now + timedelta(days=duration)
        c.execute("UPDATE vouchers SET status='active', activated_at=?, mac_address=?, expires_at=? WHERE id=?",
                  (now, mac, expiry, v_id))
        conn.commit()

    conn.close()
    
    # WORLD-CLASS HANDSHAKE:
    # Tell Cudy to open the gate. Usually a redirect to Cudy's auth API.
    # Example: return redirect(f"{gw_url}/auth?mac={mac}&status=success")
    return f"<h1>Success!</h1><p>Voucher {code} activated. You are now connected to High-Speed Wi-Fi.</p>"

# 3. ADMIN LOGIN
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == 'naboth123': # Default admin password
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash("Invalid Admin Password")
    return render_template('admin_login.html')

# 4. ADMIN DASHBOARD (Check Vouchers & Users)
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM vouchers ORDER BY created_at DESC")
    all_vouchers = c.fetchall()
    conn.close()
    return render_template('admin.html', vouchers=all_vouchers)

# 5. GENERATE VOUCHERS (Admin tool)
@app.route('/admin/generate', methods=['POST'])
@admin_required
def generate():
    count = int(request.form.get('count', 10))
    duration = int(request.form.get('duration', 1)) # 1 to 30 days
    
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    for _ in range(count):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        c.execute("INSERT INTO vouchers (code, duration_days, created_at) VALUES (?, ?, ?)",
                  (f"ZIM-{code}", duration, datetime.now()))
    conn.commit()
    conn.close()
    flash(f"Generated {count} vouchers ({duration} days).")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
