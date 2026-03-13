# 📄 Hotspot System Admin Manual

Welcome to the **Naboth Tech Hotspot Admin**. This guide explains how to manage your vouchers, monitor users, and update settings.

## 1. Accessing the Dashboard
- **URL:** `https://cudy-hotspot.onrender.com/admin`
- **Password:** Use the secure password set in your `.env` file (Default: `naboth123`).

## 2. Generating Vouchers
1. From the main dashboard, go to the **Voucher Management** tab.
2. Enter the **Amount** of vouchers (e.g., 10).
3. Enter the **Duration (Days)**. 
   - **Quick Selection:** Click the 1D, 7D, or 30D buttons for standard durations.
   - **Flexible Pricing:** Any duration can be entered. The price is automatically calculated (1D=$1, 7D=$5, 30D=$10, others=$1/day).
4. The **GENERATE VOUCHERS** button will show the total revenue value in real-time.
5. Click to generate.

## 3. Managing and Filtering Vouchers
- **Search:** Use the search bar at the top to find a specific voucher code.
- **Status Filter:** Quickly view only 'Active', 'Unused', or 'Expired' vouchers.
- **Prioritization:** Active users always stay at the top of the list for easy monitoring.
- **Delete:** Click the red trash icon to remove any individual voucher.

## 4. Exporting and Printing
1. **Download PDF:** Click the **PRINT UNUSED VOUCHERS** button, then select **DOWNLOAD PDF**. This is perfect for saving vouchers to your phone to share via WhatsApp.
2. **Print:** Use the **PRINT NOW** button for physical vouchers with **QR Codes**.
3. **QR Codes:** Users can scan these codes to automatically fill in their voucher on the login page.
4. **CSV Export:** Use the **Export CSV** link in the sidebar to download your sales records for Excel.

## 5. Revenue Analytics
- **Dashboard Cards:** See your **Total Lifetime Revenue**, total **Vouchers Sold**, and total **Vouchers Generated**.
- **Daily Revenue Chart:** A visual bar chart shows your earnings for the last 7 days.

## 6. Monitoring Online Users
- Navigate to the **Users Online** tab.
- This view shows devices that have been active in the last **5 minutes**.
- **MAC Address:** Shows which specific phone or laptop is connected.
- **Last Seen:** Real-time updates every time their session is verified.
- **Expiry:** Shows exactly when that user will be automatically kicked off the internet.

## 7. System Settings
1. Go to the **Settings** tab.
2. **Hotspot Name:** Change what users see at the top of the login page.
3. **Admin Password:** You can update your dashboard password here for better security.
4. **Portal URL:** Read-only link for your Cudy router configuration.

## 8. Automatic Cleanup
- The system automatically moves vouchers that have been expired for more than **10 days** to a history table. This keeps the dashboard fast and clean while preserving your total lifetime stats.

---
**Developed by Naboth Sithole**  
*Naboth Tech Solutions &copy; 2026*
