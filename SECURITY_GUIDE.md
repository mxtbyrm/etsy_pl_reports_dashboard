# 🔐 Dashboard Security Guide

## Authentication System

The Etsy Analytics Dashboard now includes a secure authentication system to protect your sensitive business data from unauthorized access.

## How It Works

### 1. **Login Protection**

- Dashboard requires username and password to access
- Passwords are hashed using SHA-256 before comparison
- Session-based authentication (stays logged in during session)
- Automatic logout on browser close or manual logout

### 2. **Credential Storage**

- Credentials stored in `.env` file (not in code)
- Environment variables keep sensitive data separate
- `.env` file should never be committed to version control

### 3. **Session Management**

- Streamlit session state tracks authentication
- Each user session is isolated
- Logout clears session data

## Setup Instructions

### Step 1: Configure Credentials

1. **Copy the example file:**

   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file:**

   ```bash
   nano .env
   # or use any text editor
   ```

3. **Set your credentials:**
   ```env
   DASHBOARD_USERNAME=your_username
   DASHBOARD_PASSWORD=your_secure_password
   ```

### Step 2: Choose a Strong Password

**Password Requirements:**

- Minimum 12 characters
- Mix of uppercase and lowercase letters
- Include numbers
- Include special characters (!@#$%^&\*)
- Avoid common words or patterns

**Example Strong Passwords:**

- `MyEtsy$hop2024!Secure`
- `Analytics#Dashboard9*Pro`
- `Biz@Data!2024$Protect`

**Tools for Password Generation:**

- Use a password manager (1Password, LastPass, Bitwarden)
- Online generator: https://passwordsgenerator.net/
- Command line: `openssl rand -base64 20`

### Step 3: Test Login

1. Start the dashboard:

   ```bash
   streamlit run dashboard.py
   ```

2. You should see the login page
3. Enter your credentials
4. Click "Login"

## Security Features

### ✅ What's Protected

1. **All Dashboard Pages**

   - Shop Overview
   - Listing Analysis
   - Product Analysis
   - Comparative Analysis

2. **Sensitive Business Data**

   - Revenue and profit information
   - Customer analytics
   - Cost and margin data
   - Order details
   - Inventory information

3. **Data Export**
   - CSV downloads
   - JSON exports
   - Report data

### 🔒 Security Measures

1. **Password Hashing**

   - Passwords never stored in plain text
   - SHA-256 cryptographic hashing
   - Comparison happens on hashed values

2. **Session Isolation**

   - Each browser session is separate
   - Sessions don't persist across restarts
   - Automatic timeout on browser close

3. **Environment Variables**
   - Credentials stored outside code
   - Easy to change without code modifications
   - Supports different environments (dev/prod)

## Default Credentials

**⚠️ IMPORTANT:** The default credentials are:

- **Username:** `admin`
- **Password:** `changeme123`

**YOU MUST CHANGE THESE IMMEDIATELY!**

These defaults are only for initial setup and testing. Using default credentials in production is a serious security risk.

## Changing Credentials

### Method 1: Edit .env File

1. Open `.env` file:

   ```bash
   nano .env
   ```

2. Update credentials:

   ```env
   DASHBOARD_USERNAME=new_username
   DASHBOARD_PASSWORD=new_password
   ```

3. Save and restart dashboard

### Method 2: Export Environment Variables

For temporary testing:

```bash
export DASHBOARD_USERNAME=test_user
export DASHBOARD_PASSWORD=test_pass123
streamlit run dashboard.py
```

## Multi-User Support

### Current Implementation

- Single user authentication (one username/password pair)
- Suitable for personal use or small teams sharing credentials

### Future Enhancement Options

If you need multiple users, you can extend the system:

1. **Multiple Credential Pairs**

   ```env
   DASHBOARD_USER1=admin:hashed_password1
   DASHBOARD_USER2=analyst:hashed_password2
   DASHBOARD_USER3=viewer:hashed_password3
   ```

2. **User Roles**

   - Admin: Full access
   - Analyst: View and export
   - Viewer: View only

3. **Database-Backed Users**
   - Store users in database
   - Support user management UI
   - Track login history

## Logout

### Manual Logout

1. Click "🚪 Logout" button in sidebar
2. Session cleared immediately
3. Redirected to login page

### Automatic Logout

- Closing browser/tab
- Browser crash
- Dashboard restart
- Session timeout (configurable)

## Troubleshooting

### Can't Login - Forgot Password

1. **Check `.env` file:**

   ```bash
   cat .env | grep DASHBOARD
   ```

2. **Reset to defaults:**

   ```env
   DASHBOARD_USERNAME=admin
   DASHBOARD_PASSWORD=changeme123
   ```

3. **Restart dashboard**

### Can't Login - Wrong Credentials

1. Verify username is correct (case-sensitive)
2. Verify password is correct (case-sensitive)
3. Check for extra spaces in `.env` file
4. Ensure no quotes around values in `.env`

### Environment Variables Not Loading

1. **Check `.env` file location:**

   - Must be in same directory as `dashboard.py`
   - Must be named exactly `.env`

2. **Verify file format:**

   ```env
   DASHBOARD_USERNAME=admin
   DASHBOARD_PASSWORD=changeme123
   ```

   - No spaces around `=`
   - No quotes needed
   - One variable per line

3. **Check file permissions:**
   ```bash
   ls -la .env
   # Should be readable
   chmod 600 .env  # Make it readable/writable by owner only
   ```

### Still Using Default Credentials

If you see this warning, it means credentials haven't been changed:

1. Edit `.env` file
2. Set new `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD`
3. Restart dashboard
4. Login with new credentials

## Best Practices

### 🛡️ Security Recommendations

1. **Change Defaults Immediately**

   - Never use default credentials in production
   - Change on first run

2. **Use Strong Passwords**

   - Minimum 12 characters
   - Mix character types
   - Use password manager

3. **Protect .env File**

   ```bash
   chmod 600 .env  # Owner read/write only
   ```

4. **Never Commit .env**

   - Add to `.gitignore`
   - Keep credentials secret
   - Use `.env.example` for documentation

5. **Regular Password Changes**

   - Change every 90 days
   - Change if compromised
   - Change when team member leaves

6. **Secure Access**

   - Use HTTPS if deploying remotely
   - Use VPN for remote access
   - Restrict network access
   - Use firewall rules

7. **Monitor Access**
   - Check who has credentials
   - Remove access for former team members
   - Use unique credentials per user

### 🌐 Network Security

#### Local Access Only (Default)

Dashboard runs on `localhost:8501` - only accessible from your computer.

#### Remote Access (Advanced)

If deploying for remote access:

1. **Use Reverse Proxy**

   - Nginx or Apache with SSL
   - Enforce HTTPS
   - Add IP restrictions

2. **Use VPN**

   - Access through secure tunnel
   - Corporate VPN
   - Personal VPN (WireGuard, OpenVPN)

3. **Cloud Deployment**

   - Use Streamlit Cloud (built-in auth)
   - AWS/GCP with IAM
   - Azure with AD integration

4. **Firewall Rules**
   ```bash
   # Example: Only allow specific IPs
   sudo ufw allow from 192.168.1.0/24 to any port 8501
   ```

## Compliance

### Data Protection

- GDPR: Customer data protection
- PCI DSS: If handling payment info
- CCPA: California consumer privacy

### Access Control

- Implement principle of least privilege
- Regular access audits
- Document who has access

### Data Retention

- Backup encrypted credentials
- Secure credential storage
- Document security procedures

## Additional Security Enhancements

### Optional: Two-Factor Authentication (2FA)

For extra security, you could implement:

- TOTP (Time-based One-Time Password)
- SMS verification
- Email verification
- Authenticator apps (Google Authenticator, Authy)

### Optional: IP Whitelisting

Restrict access to specific IP addresses:

```python
ALLOWED_IPS = ['192.168.1.100', '10.0.0.50']
```

### Optional: Audit Logging

Track who accesses what and when:

- Login attempts
- Page views
- Data exports
- Failed authentication

### Optional: Rate Limiting

Prevent brute force attacks:

- Limit login attempts
- Temporary lockout after failures
- CAPTCHA after multiple failures

## Support

### Security Issues

If you discover a security vulnerability:

1. Do not create a public issue
2. Document the issue privately
3. Change credentials immediately
4. Review access logs

### Questions

For authentication questions:

1. Check this guide first
2. Review `.env.example`
3. Test with default credentials
4. Check troubleshooting section

## Summary

✅ **Setup Checklist:**

- [ ] Copy `.env.example` to `.env`
- [ ] Set custom username
- [ ] Set strong password
- [ ] Test login
- [ ] Secure `.env` file permissions
- [ ] Add `.env` to `.gitignore`
- [ ] Document credentials securely
- [ ] Configure logout timeout (if needed)

🔒 **Security Checklist:**

- [ ] Changed default credentials
- [ ] Using strong password (12+ chars)
- [ ] `.env` file has restricted permissions
- [ ] `.env` not committed to git
- [ ] Only authorized users have credentials
- [ ] Regular password rotation plan
- [ ] Backup credentials securely
- [ ] Monitor access regularly

---

**Version:** 1.0  
**Last Updated:** 2025-11-07  
**Dashboard Version:** 1.1+
