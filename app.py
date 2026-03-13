from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, Response
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import sqlite3
import random
import string
import os
import io
import csv
import qrcode
from datetime import datetime, timedelta
import functools

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
bcrypt = Bcrypt(app)

# --- DATABASE CONFIG ---
# On Render, use a Persistent Disk path like /data/hotspot.db
DB_PATH = os.getenv('DATABASE_PATH', 'hotspot.db')

# Helper to get DB connection
def get_db_conn():
    return sqlite3.connect(DB_PATH)

# --- HELPER: PRICING ---
def get_voucher_price(duration):
    p1 = float(get_setting('price_1d', 1))
    p7 = float(get_setting('price_7d', 5))
    p30 = float(get_setting('price_30d', 10))
    
    if duration == 1: return p1
    if duration == 7: return p7
    if duration == 30: return p30
    return duration # Default $1 per day

# --- DATABASE SETUP ---
def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    # Active Vouchers table
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
    
    # Voucher History table (for auditing and archiving)
    c.execute('''CREATE TABLE IF NOT EXISTS voucher_history (
                 id INTEGER PRIMARY KEY,
                 code TEXT,
                 duration_days INTEGER,
                 status TEXT,
                 created_at DATETIME,
                 activated_at DATETIME,
                 mac_address TEXT,
                 expires_at DATETIME,
                 last_seen DATETIME,
                 archived_at DATETIME
                 )''')
    
    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                 key TEXT PRIMARY KEY,
                 value TEXT
                 )''')

    # Stats table (for lifetime metrics)
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
                 key TEXT PRIMARY KEY,
                 value REAL
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
        'portal_url': os.getenv('PORTAL_URL', 'http://your-server-ip:5000/login'),
        'price_1d': '1',
        'price_7d': '5',
        'price_30d': '10',
        'cleanup_days': '10'
    }
    
    for key, value in default_settings.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    # Initialize stats
    default_stats = {
        'total_vouchers_generated': 0,
        'total_vouchers_used': 0,
        'total_revenue': 0
    }
    for key, value in default_stats.items():
        c.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)", (key, value))
        
    conn.commit()
    conn.close()
    sync_stats() # Synchronize stats on startup

def sync_stats():
    """Backfills stats from existing database records to ensure accuracy."""
    conn = get_db_conn()
    c = conn.cursor()
    
    # 1. Count Total Generated (Active table + History table)
    c.execute("SELECT COUNT(*) FROM vouchers")
    active_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM voucher_history")
    history_count = c.fetchone()[0]
    total_generated = active_count + history_count
    
    # 2. Count Total Used (Active with status 'active'/'expired' + History)
    c.execute("SELECT COUNT(*) FROM vouchers WHERE status IN ('active', 'expired')")
    active_used = c.fetchone()[0]
    total_used = active_used + history_count
    
    # 3. Calculate Total Revenue
    # We'll sum based on duration_days for all used/history vouchers
    c.execute("SELECT duration_days FROM vouchers WHERE status IN ('active', 'expired')")
    active_durations = c.fetchall()
    c.execute("SELECT duration_days FROM voucher_history")
    history_durations = c.fetchall()
    
    total_rev = 0
    for (d,) in active_durations + history_durations:
        total_rev += get_voucher_price(d)
        
    # Update the stats table
    c.execute("UPDATE stats SET value = ? WHERE key = 'total_vouchers_generated'", (total_generated,))
    c.execute("UPDATE stats SET value = ? WHERE key = 'total_vouchers_used'", (total_used,))
    c.execute("UPDATE stats SET value = ? WHERE key = 'total_revenue'", (total_rev,))
    
    conn.commit()
    conn.close()

init_db()

# --- HELPER: UPDATE STATS ---
def update_stat(key, increment):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("UPDATE stats SET value = value + ? WHERE key = ?", (increment, key))
    conn.commit()
    conn.close()

# --- HELPER: GET STATS ---
def get_all_stats():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT key, value FROM stats")
    res = dict(c.fetchall())
    conn.close()
    return res

# --- HELPER: GET DAILY REVENUE (Last 7 Days) ---
def get_daily_revenue():
    conn = get_db_conn()
    c = conn.cursor()
    days = []
    revenues = []
    # Ensure tables exist before querying
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='voucher_history'")
    if not c.fetchone():
        return {"days": [], "revenues": []}

    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        # Sum revenue from history and active vouchers for this date
        c.execute("SELECT duration_days FROM voucher_history WHERE activated_at LIKE ?", (f"{date}%",))
        hist_durations = c.fetchall()
        c.execute("SELECT duration_days FROM vouchers WHERE status IN ('active', 'expired') AND activated_at LIKE ?", (f"{date}%",))
        active_durations = c.fetchall()
        
        daily_total = 0
        for (d,) in hist_durations + active_durations:
            daily_total += get_voucher_price(d)
        
        days.append(date)
        revenues.append(daily_total)
    
    conn.close()
    return {"days": days, "revenues": revenues}

# --- HELPER: CLEANUP EXPIRED VOUCHERS (Global) ---
def cleanup_expired_vouchers():
    conn = get_db_conn()
    c = conn.cursor()
    now = datetime.now()
    
    # 1. Mark active vouchers as expired
    c.execute("UPDATE vouchers SET status='expired' WHERE status='active' AND expires_at < ?", (now,))
    
    # 2. Archive vouchers expired for more than X days
    days = int(get_setting('cleanup_days', 10))
    threshold = (now - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S.%f")
    
    # Select expired vouchers older than threshold
    c.execute("SELECT * FROM vouchers WHERE status='expired' AND expires_at < ?", (threshold,))
    to_archive = c.fetchall()
    
    for v in to_archive:
        # Insert into history table
        c.execute('''INSERT INTO voucher_history 
                     (id, code, duration_days, status, created_at, activated_at, mac_address, expires_at, last_seen, archived_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], now))
        
        # Delete from active table
        c.execute("DELETE FROM vouchers WHERE id=?", (v[0],))
        
    conn.commit()
    conn.close()

# --- HELPER: GET SETTING ---
def get_setting(key, default=None):
    conn = get_db_conn()
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
    conn = get_db_conn()
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
        try:
            expires_at = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            # Fallback for formats without microseconds if any
            expires_at = datetime.strptime(expires_str.split('.')[0], "%Y-%m-%d %H:%M:%S")

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
    # Detect MAC address from various brands (Cudy, TP-Link, UniFi, MikroTik)
    mac = request.args.get('mac') or request.args.get('clientMac') or request.args.get('id')
    
    # Detect Gateway Return URL
    gw_url = request.args.get('gw_url') or request.args.get('target') or request.args.get('url') or request.args.get('link-login-only')
    
    voucher = request.args.get('voucher', '') # Pre-fill from QR code
    hotspot_name = get_setting('hotspot_name')
    
    if mac and gw_url:
        active_v = get_live_voucher(mac, is_mac=True)
        if active_v and active_v['status'] == 'active':
            # Handle brand-specific auth success redirects
            if 'clientMac' in request.args: # TP-Link style
                separator = '&' if '?' in gw_url else '?'
                return redirect(f"{gw_url}{separator}status=success&clientMac={mac}&voucher={active_v['code']}")
            return redirect(f"{gw_url}/auth?status=success&mac={mac}&voucher={active_v['code']}")

    return render_template('login.html', mac=mac, gw_url=gw_url, voucher=voucher, hotspot_name=hotspot_name)

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
        conn = get_db_conn()
        c = conn.cursor()
        now = datetime.now()
        c.execute("SELECT duration_days FROM vouchers WHERE id=?", (v['id'],))
        duration = c.fetchone()[0]
        expiry = now + timedelta(days=duration)
        c.execute("UPDATE vouchers SET status='active', activated_at=?, mac_address=?, expires_at=?, last_seen=? WHERE id=?",
                  (now, mac, expiry, now, v['id']))
        conn.commit()
        conn.close()
        
        # Update Lifetime Stats
        update_stat('total_vouchers_used', 1)
        update_stat('total_revenue', get_voucher_price(duration))

    if gw_url:
        # Detect brand for redirection format
        is_tplink = 'clientMac' in request.form or 'target' in request.form
        separator = '&' if '?' in gw_url else '?'
        
        if is_tplink:
             return redirect(f"{gw_url}{separator}status=success&clientMac={mac}&voucher={code}")
        
        # Default Cudy / Standard style
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
    conn = get_db_conn()
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
    
    search = request.args.get('search', '').strip().upper()
    status_filter = request.args.get('status', '')
    
    conn = get_db_conn()
    c = conn.cursor()
    
    query = "SELECT * FROM vouchers WHERE 1=1"
    params = []
    
    if search:
        query += " AND code LIKE ?"
        params.append(f"%{search}%")
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
        
    # Order: Active first, then Unused, then Expired at the very bottom
    query += """ ORDER BY 
                 CASE 
                    WHEN status='active' THEN 0 
                    WHEN status='unused' THEN 1 
                    ELSE 2 
                 END, created_at DESC"""
                 
    c.execute(query, params)
    all_vouchers = c.fetchall()
    conn.close()
    
    stats = get_all_stats()
    return render_template('admin.html', 
                         vouchers=all_vouchers, 
                         stats=stats, 
                         search=search, 
                         status_filter=status_filter)

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    stats = get_all_stats()
    revenue_chart = get_daily_revenue()
    return render_template('admin_analytics.html', stats=stats, revenue_chart=revenue_chart)

@app.route('/admin/export')
@admin_required
def export_vouchers():
    conn = get_db_conn()
    c = conn.cursor()
    # Also include history in export? For now, just active table.
    c.execute("SELECT code, duration_days, status, created_at, activated_at, mac_address, expires_at FROM vouchers")
    rows = c.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Code', 'Duration (Days)', 'Status', 'Created At', 'Activated At', 'MAC Address', 'Expires At'])
    writer.writerows(rows)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=vouchers_export.csv"}
    )

@app.route('/qr/<code>')
def generate_qr(code):
    portal_url = get_setting('portal_url', 'http://your-server-ip:5000/login')
    # Append the voucher code to the login URL
    url = f"{portal_url}?voucher={code}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/admin/online')
@admin_required
def admin_online():
    cleanup_expired_vouchers() # Remove expired ones first
    conn = get_db_conn()
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
        price_1d = request.form.get('price_1d')
        price_7d = request.form.get('price_7d')
        price_30d = request.form.get('price_30d')
        cleanup_days = request.form.get('cleanup_days')
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("UPDATE settings SET value=? WHERE key='hotspot_name'", (hotspot_name,))
        c.execute("UPDATE settings SET value=? WHERE key='price_1d'", (price_1d,))
        c.execute("UPDATE settings SET value=? WHERE key='price_7d'", (price_7d,))
        c.execute("UPDATE settings SET value=? WHERE key='price_30d'", (price_30d,))
        c.execute("UPDATE settings SET value=? WHERE key='cleanup_days'", (cleanup_days,))
        
        if new_password and len(new_password) > 0:
            new_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            c.execute("UPDATE settings SET value=? WHERE key='admin_password_hash'", (new_hash,))
            
        conn.commit()
        conn.close()
        flash("Settings updated successfully.")
        return redirect(url_for('admin_settings'))
    
    settings = {
        'hotspot_name': get_setting('hotspot_name'),
        'portal_url': get_setting('portal_url'),
        'price_1d': get_setting('price_1d', '1'),
        'price_7d': get_setting('price_7d', '5'),
        'price_30d': get_setting('price_30d', '10'),
        'cleanup_days': get_setting('cleanup_days', '10')
    }
    return render_template('admin_settings.html', settings=settings)

@app.route('/admin/generate', methods=['POST'])
@admin_required
def generate():
    count = int(request.form.get('count', 10))
    duration = int(request.form.get('duration', 1))
    
    conn = get_db_conn()
    c = conn.cursor()
    for _ in range(count):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        c.execute("INSERT INTO vouchers (code, duration_days, created_at) VALUES (?, ?, ?)",
                  (f"ZIM-{code}", duration, datetime.now()))
    conn.commit()
    conn.close()
    
    update_stat('total_vouchers_generated', count)
    
    flash(f"Generated {count} vouchers ({duration} days).")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:voucher_id>')
@admin_required
def delete_voucher(voucher_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("DELETE FROM vouchers WHERE id=?", (voucher_id,))
    conn.commit()
    conn.close()
    flash("Voucher deleted successfully.")
    # Preserve search/filter if they exist
    return redirect(url_for('admin_dashboard', search=request.args.get('search'), status=request.args.get('status')))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
