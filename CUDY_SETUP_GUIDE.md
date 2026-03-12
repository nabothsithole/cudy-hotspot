# 📡 Cudy AX3000 Hardware Setup Guide

This document explains how to connect your Cudy AX3000 (Indoor/Outdoor) Access Point to the Professional Hotspot System hosted on Render.

## 1. Accessing Cudy Admin
1. Connect your computer to the Cudy router via Ethernet or Wi-Fi.
2. Open a browser and go to `http://cudy.net` (or `192.168.10.1`).
3. Log in with your Cudy admin password.

## 2. Captive Portal Configuration
1. Navigate to **Advanced Settings** > **Captive Portal**.
2. Toggle **Enable Captive Portal** to **ON**.
3. **Portal Method:** Select `External Portal`.
4. **Portal URL:** 
   `https://cudy-hotspot.onrender.com/login`
5. **Authentication Mode:** Set to `Voucher` or `External API`.
6. **Success Redirect:** Set to `Original URL` or a custom website (e.g., `https://google.com`).

## 3. Walled Garden (Critical Step)
The "Walled Garden" allows users to reach your login page *before* they have internet access. If this is not set, the login page will not load.

1. Find the **Walled Garden** or **Allowed Domain List** section.
2. Add the following domains:
   - `cudy-hotspot.onrender.com`
   - `onrender.com`
3. (Optional) If using custom fonts or external CSS:
   - `fonts.googleapis.com`
   - `fonts.gstatic.com`

## 4. Testing the Connection
1. Disconnect your phone from the Wi-Fi and reconnect.
2. A "Sign in to Wi-Fi" notification should appear.
3. Tap it, and you should see the **ZIM-Fuel Hotspot** login page.

---
**Troubleshooting:**
- **Page won't load:** Check if the Walled Garden domains are typed correctly.
- **"Invalid GW_URL":** Ensure the Cudy firmware is up to date; it must support passing `mac` and `gw_url` parameters.
