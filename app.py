from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import sqlite3
import random
import string
import os
from datetime import datetime, timedelta
import functools

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
bcrypt = Bcrypt(app)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    # Vouchers table
    c.execute('''CREATE TABLE IF NOT EXISTS vouchers (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 code TEXT UNIQUE,
                 duration_days INTEGER,
                 status TEXT DEFAULT 'unused',
                 created_at DATETIME,
                 activated_at DATETIME,
                 mac_address TEXT,
                 expires_at DATETIME,
                 last_seen DATETIME
                 )''')
    
    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                 key TEXT PRIMARY KEY,
                 value TEXT
                 )''')
    
    # MIGRATION: Check if last_seen exists in vouchers (safety for existing DBs)
    c.execute("PRAGMA table_info(vouchers)")
    columns = [column[1] for column in c.fetchall()]
    if 'last_seen' not in columns:
        c.execute("ALTER TABLE vouchers ADD COLUMN last_seen DATETIME")
    
    # Initialize default settings if not exists
    default_settings = {
        'hotspot_name': os.getenv('HOTSPOT_NAME', 'Cudy AX3000 Hotspot'),
        'admin_password_hash': bcrypt.generate_password_hash(os.getenv('ADMIN_PASSWORD', 'naboth123')).decode('utf-8'),
        'portal_url': os.getenv('PORTAL_URL', 'http://your-server-ip:5000/login')
    }
    
    for key, value in default_settings.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
        
    conn.commit()
    conn.close()

init_db()

# --- HELPER: CLEANUP EXPIRED VOUCHERS (Global) ---
def cleanup_expired_vouchers():
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    now = datetime.now()
    # Batch update any active voucher whose expiry time has passed
    c.execute("UPDATE vouchers SET status='expired' WHERE status='active' AND expires_at < ?", (now,))
    conn.commit()
    conn.close()

# --- HELPER: GET SETTING ---
def get_setting(key, default=None):
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else default

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

    # ID, CODE, DURATION, STATUS, CREATED, ACTIVATED, MAC, EXPIRES, LAST_SEEN
    v_id, v_code, duration, status, created, activated, v_mac, expires_str, last_seen = v
    
    # LIVE CHECK: If it's active but the time is past, mark as expired now
    if status == 'active' and expires_str:
        expires_at = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S.%f")
        if datetime.now() > expires_at:
            c.execute("UPDATE vouchers SET status='expired' WHERE id=?", (v_id,))
            conn.commit()
            status = 'expired'
        else:
            # Update last_seen if it's currently being verified/checked
            c.execute("UPDATE vouchers SET last_seen=? WHERE id=?", (datetime.now(), v_id))
            conn.commit()
            
    conn.close()
    return {
        "id": v_id, "code": v_code, "status": status, 
        "mac": v_mac, "expires_at": expires_str, "last_seen": last_seen
    }

# --- ROUTES ---

@app.route('/')
@app.route('/login')
def login():
    mac = request.args.get('mac')
    gw_url = request.args.get('gw_url')
    hotspot_name = get_setting('hotspot_name')
    
    if mac:
        active_v = get_live_voucher(mac, is_mac=True)
        if active_v and active_v['status'] == 'active':
            return redirect(f"{gw_url}/auth?status=success&mac={mac}&voucher={active_v['code']}")

    return render_template('login.html', mac=mac, gw_url=gw_url, hotspot_name=hotspot_name)

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

    if v['status'] == 'unused':
        conn = sqlite3.connect('hotspot.db')
        c = conn.cursor()
        now = datetime.now()
        c.execute("SELECT duration_days FROM vouchers WHERE id=?", (v['id'],))
        duration = c.fetchone()[0]
        expiry = now + timedelta(days=duration)
        c.execute("UPDATE vouchers SET status='active', activated_at=?, mac_address=?, expires_at=?, last_seen=? WHERE id=?",
                  (now, mac, expiry, now, v['id']))
        conn.commit()
        conn.close()

    if gw_url:
        return redirect(f"{gw_url}/auth?status=success&mac={mac}&voucher={code}")
    
    return render_template('success.html', code=code)

@app.route('/verify/<mac>')
def verify_status(mac):
    v = get_live_voucher(mac, is_mac=True)
    if v and v['status'] == 'active':
        return {"status": "authorized", "expires": v['expires_at']}, 200
    return {"status": "unauthorized"}, 401

@app.route('/admin/print')
@admin_required
def print_vouchers():
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    c.execute("SELECT code, duration_days FROM vouchers WHERE status='unused' ORDER BY created_at DESC")
    unused = c.fetchall()
    conn.close()
    return render_template('print_vouchers.html', vouchers=unused)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        stored_hash = get_setting('admin_password_hash')
        if bcrypt.check_password_hash(stored_hash, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash("Invalid Admin Password")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    cleanup_expired_vouchers() # Ensure we see accurate data
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM vouchers ORDER BY created_at DESC")
    all_vouchers = c.fetchall()
    conn.close()
    return render_template('admin.html', vouchers=all_vouchers)

@app.route('/admin/online')
@admin_required
def admin_online():
    cleanup_expired_vouchers() # Remove expired ones first
    conn = sqlite3.connect('hotspot.db')
    c = conn.cursor()
    five_mins_ago = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S.%f")
    c.execute("SELECT * FROM vouchers WHERE status='active' AND last_seen > ? ORDER BY last_seen DESC", (five_mins_ago,))
    online_vouchers = c.fetchall()
    conn.close()
    return render_template('admin_online.html', vouchers=online_vouchers)

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        hotspot_name = request.form.get('hotspot_name')
        new_password = request.form.get('password')
        
        conn = sqlite3.connect('hotspot.db')
        c = conn.cursor()
        c.execute("UPDATE settings SET value=? WHERE key='hotspot_name'", (hotspot_name,))
        
        if new_password and len(new_password) > 0:
            new_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            c.execute("UPDATE settings SET value=? WHERE key='admin_password_hash'", (new_hash,))
            
        conn.commit()
        conn.close()
        flash("Settings updated successfully.")
        return redirect(url_for('admin_settings'))
    
    settings = {
        'hotspot_name': get_setting('hotspot_name'),
        'portal_url': get_setting('portal_url')
    }
    return render_template('admin_settings.html', settings=settings)

@app.route('/admin/generate', methods=['POST'])
@admin_required
def generate():
    count = int(request.form.get('count', 10))
    duration = int(request.form.get('duration', 1))
    
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
