# 📶 Cudy AX3000 Professional Hotspot System

A high-performance, MikroTik-inspired Captive Portal and Voucher Management System specifically designed for the **Cudy AX3000** (Indoor/Outdoor) Access Points.

## 🚀 Key Features

- **Professional Captive Portal:** Mobile-responsive login page for users to enter voucher codes.
- **Smart Admin Dashboard:** Secure management area with real-time statistics and prioritized sorting.
- **QR Code Integration:** Vouchers now include scan-to-connect QR codes for a faster user experience.
- **Revenue Analytics:** Visual bar charts showing daily revenue for the last 7 days.
- **Export & Download:** Save vouchers as high-quality PDFs or export all records to CSV for bookkeeping.
- **Flexible Pricing:** Support for any duration (1D=$1, 7D=$5, 30D=$10, others=$1/day) with dynamic price calculation.
- **Mobile-Optimized Admin:** Responsive dashboard with a card-based layout for management on-the-go.
- **10-Day Auto-Archive:** Automatically moves expired vouchers to a history table after 10 days to maintain peak performance.
- **MAC Address Binding:** Prevents voucher sharing by locking active codes to a specific device.

## 📁 Project Structure

```text
cudy-hotspot/
├── app.py              # Main Flask Backend, Pricing, and Analytics Logic
├── hotspot.db          # SQLite Database (Auto-generated with Stats and History)
├── requirements.txt    # Python Dependencies (Flask, qrcode, Bcrypt, etc.)
├── .env                # Environment variables (Portal URL, Hotspot Name)
├── .gitignore          # Keeps the repo clean (ignores venv/db/.env)
├── static/             # CSS/Images (Optional)
└── templates/          # HTML Views
    ├── login.html          # User Login Portal (with QR pre-fill)
    ├── success.html        # Post-authentication screen
    ├── admin.html          # Dashboard with Analytics and Filtering
    ├── admin_login.html    # Secure Admin Access with Eye Icon Toggle
    ├── admin_settings.html # Site Settings and Password Management
    ├── admin_online.html   # Real-time Monitoring of Connected Users
    └── print_vouchers.html # PDF/Print Layout with QR Codes
```
...
## 🔜 Future Enhancements

- [ ] Real-time bandwidth monitoring per user (via Cudy API).
- [ ] Automated SMS/WhatsApp notifications for voucher purchases.
- [ ] Multi-admin support with different permission levels.

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

- [ ] Real-time bandwidth monitoring per user.
- [ ] Automated SMS notifications for voucher purchases.

---
**Developed by Naboth Tech Solutions &copy; 2026**
