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

# --- HELPER: GET VOUCHER STATUS (Live Calculation) ---
def get_live_voucher(code_or_mac, is_mac=False):
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    if is_mac:
        c.execute("SELECT * FROM vouchers WHERE mac_address=? AND status='active'", (code_or_mac,))
    else:
        c.execute("SELECT * FROM vouchers WHERE code=?", (code_or_mac,))
    v = c.fetchone()
    
    if not v:
        conn.close()
        return None

    # ID, CODE, DURATION, STATUS, CREATED, ACTIVATED, MAC, EXPIRES
    v_id, v_code, duration, status, created, activated, v_mac, expires_str = v
    
    # LIVE CHECK: If it's active but the time is past, mark as expired now
    if status == 'active' and expires_str:
        expires_at = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S.%f")
        if datetime.now() > expires_at:
            c.execute("UPDATE vouchers SET status='expired' WHERE id=?", (v_id,))
            conn.commit()
            status = 'expired'
            
    conn.close()
    # Return as a dictionary for easy use
    return {
        "id": v_id, "code": v_code, "status": status, 
        "mac": v_mac, "expires_at": expires_str
    }

# --- ROUTES ---

@app.route('/')
@app.route('/login')
def login():
    mac = request.args.get('mac')
    gw_url = request.args.get('gw_url')
    
    # Check if this MAC already has a LIVE active voucher
    if mac:
        active_v = get_live_voucher(mac, is_mac=True)
        if active_v and active_v['status'] == 'active':
            # Already active! Skip login and reconnect them.
            return redirect(f"{gw_url}/auth?status=success&mac={mac}&voucher={active_v['code']}")

    return render_template('login.html', mac=mac, gw_url=gw_url)

# 2. VOUCHER VALIDATION LOGIC
@app.route('/auth', methods=['POST'])
def authenticate():
    code = request.form.get('voucher').strip().upper()
    mac = request.form.get('mac')
    gw_url = request.form.get('gw_url')

    v = get_live_voucher(code)

    if not v:
        flash("Invalid voucher code.")
        return redirect(url_for('login', mac=mac, gw_url=gw_url))

    if v['status'] == 'active' and v['mac'] != mac:
        flash("Voucher is already in use by another device.")
        return redirect(url_for('login', mac=mac, gw_url=gw_url))
    
    if v['status'] == 'expired':
        flash("Voucher has expired.")
        return redirect(url_for('login', mac=mac, gw_url=gw_url))

    # Activate Unused Voucher
    if v['status'] == 'unused':
        conn = sqlite3.connect('hotspot.db')
        c = conn.cursor()
        now = datetime.now()
        # Fetch the original duration from the DB to calculate expiry
        c.execute("SELECT duration_days FROM vouchers WHERE id=?", (v['id'],))
        duration = c.fetchone()[0]
        expiry = now + timedelta(days=duration)
        c.execute("UPDATE vouchers SET status='active', activated_at=?, mac_address=?, expires_at=? WHERE id=?",
                  (now, mac, expiry, v['id']))
        conn.commit()
        conn.close()

    if gw_url:
        return redirect(f"{gw_url}/auth?status=success&mac={mac}&voucher={code}")
    
    return render_template('success.html', code=code)

# API for Cudy AP to check if a user should be kicked off
@app.route('/verify/<mac>')
def verify_status(mac):
    v = get_live_voucher(mac, is_mac=True)
    if v and v['status'] == 'active':
        return {"status": "authorized", "expires": v['expires_at']}, 200
    return {"status": "unauthorized"}, 401

# 3. PRINTABLE VOUCHERS VIEW
@app.route('/admin/print')
@admin_required
def print_vouchers():
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    # Only show unused vouchers for printing
    c.execute("SELECT code, duration_days FROM vouchers WHERE status='unused' ORDER BY created_at DESC")
    unused = c.fetchall()
    conn.close()
    return render_template('print_vouchers.html', vouchers=unused)

# 4. ADMIN LOGIN
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
