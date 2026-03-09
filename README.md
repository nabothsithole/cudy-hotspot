# 📶 Cudy AX3000 Professional Hotspot System

A high-performance, MikroTik-inspired Captive Portal and Voucher Management System specifically designed for the **Cudy AX3000** (Indoor/Outdoor) Access Points.

## 🚀 Key Features

- **Professional Captive Portal:** Mobile-responsive login page for users to enter voucher codes.
- **Smart Admin Dashboard:** Secure management area to generate vouchers and monitor active sessions.
- **Dynamic Voucher Logic:** Generate unique codes with custom durations (1, 7, or 30 days).
- **Live Expiry System:** "Fail-safe" logic that calculates expiry in real-time on every request.
- **Printable Vouchers:** One-click "Print" view with a clean grid layout for selling physical vouchers.
- **MAC Address Binding:** Prevents voucher sharing by locking active codes to a specific device.
- **Cudy Handshake:** Seamlessly redirects authenticated users back to the Cudy gateway.

## 📁 Project Structure

```text
cudy-hotspot/
├── app.py              # Main Flask Backend & Logic
├── hotspot.db          # SQLite Database (Auto-generated)
├── requirements.txt    # Python Dependencies
├── .gitignore          # Keeps the repo clean (ignores venv/db)
├── static/             # CSS/Images (Optional)
└── templates/          # HTML Views
    ├── login.html          # User Login Portal
    ├── success.html        # Post-authentication screen
    ├── admin.html          # Voucher Management Dashboard
    ├── admin_login.html    # Secure Admin Access
    └── print_vouchers.html # Professional Printing Layout
```

## 🛠 Installation & Setup

### 1. Prerequisites
- Python 3.10+
- A Cudy AX3000 Access Point with "External Portal" support.

### 2. Local Setup
```bash
# Clone the repository
git clone https://github.com/nabothsithole/cudy-hotspot.git
cd cudy-hotspot

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 app.py
```

### 3. Cudy Configuration
1. Log into your Cudy admin panel (`cudy.net`).
2. Navigate to **Advanced > Captive Portal**.
3. Select **External Portal**.
4. Set the **Portal URL** to your hosted server address (e.g., `http://your-server-ip:5000/login`).

## 🛡 Security
- **Admin Password:** Default is `naboth123` (Change this in `app.py`).
- **Database:** Uses SQLite for local, persistent storage.
- **Session Security:** Protected via Flask's secret key.

## 🔜 Future Enhancements
- [ ] Integration with ZIM Fuel Pulse Dashboard.
- [ ] Real-time bandwidth monitoring per user.
- [ ] Automated SMS notifications for voucher purchases.

---
**Developed by Naboth Tech Solutions &copy; 2026**
