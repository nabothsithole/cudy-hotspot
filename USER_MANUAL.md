# 📄 Hotspot System Admin Manual

Welcome to the **Naboth Tech Hotspot Admin**. This guide explains how to manage your vouchers, monitor users, and update settings.

## 1. Accessing the Dashboard
- **URL:** `https://cudy-hotspot.onrender.com/admin`
- **Password:** Use the secure password set in your `.env` file (Default: `naboth123`).

## 2. Generating Vouchers
1. From the main dashboard, go to the **Voucher Management** tab.
2. Enter the **Amount** of vouchers you want to create (e.g., 50).
3. Select the **Duration** (1, 7, or 30 Days).
4. Click **GENERATE VOUCHERS**.

## 3. Printing Vouchers
1. Once generated, click the **PRINT UNUSED VOUCHERS** button.
2. A new tab will open with a clean, grid-style layout ready for printing.
3. Click **PRINT NOW** to open your computer's print dialog.
4. **Tip:** These vouchers include dashed lines for easy cutting and selling.

## 4. Monitoring Online Users
- Navigate to the **Users Online** tab.
- This view shows devices that have been active in the last **5 minutes**.
- **MAC Address:** Shows which specific phone or laptop is connected.
- **Last Seen:** Real-time updates every time their session is verified.
- **Expiry:** Shows exactly when that user will be automatically kicked off the internet.

## 5. System Settings
1. Go to the **Settings** tab.
2. **Hotspot Name:** Change what users see at the top of the login page.
3. **Admin Password:** You can update your dashboard password here for better security.
4. **Portal URL:** Read-only link for your Cudy router configuration.

## 6. Understanding Voucher Statuses
- **UNUSED:** Ready to be sold or used.
- **ACTIVE:** A user is currently connected to the Wi-Fi with this code.
- **EXPIRED:** The duration has passed; the code is no longer valid.

---
**Developed by Naboth Sithole**  
*Naboth Tech Solutions &copy; 2026*
