# 🔐 Quick Authentication Setup

## TL;DR - Get Started in 2 Minutes

### 1. Run Setup Script

```bash
python setup_auth.py
```

### 2. Enter Your Credentials

- Choose a username (default: admin)
- Create a strong password (12+ characters)

### 3. Start Dashboard

```bash
streamlit run dashboard.py
```

### 4. Login

- Enter your username and password
- Start analyzing your data!

## Default Credentials (Change Immediately!)

If you skip setup, these defaults will be used:

- **Username:** `admin`
- **Password:** `changeme123`

**⚠️ Security Risk:** Change these immediately for production use!

## Quick Commands

```bash
# Automated setup (recommended)
python setup_auth.py

# Manual setup
cp .env.example .env
nano .env  # Edit credentials

# Start dashboard
streamlit run dashboard.py

# Logout
Click "🚪 Logout" button in sidebar
```

## Password Requirements

✅ **Strong Password:**

- 12+ characters
- Mix of uppercase/lowercase
- Include numbers
- Include symbols (!@#$%^&\*)

❌ **Weak Password:**

- Short passwords
- Common words
- Personal information
- Sequential numbers

## Files Created

- `.env` - Your credentials (keep private!)
- `.env.example` - Template (safe to commit)
- `SECURITY_GUIDE.md` - Complete security docs

## Troubleshooting

**Can't login?**

1. Check username/password (case-sensitive)
2. Verify `.env` file exists
3. Reset to defaults in `.env`
4. Restart dashboard

**Forgot password?**

1. Edit `.env` file
2. Set new password
3. Restart dashboard

## Security Notes

🔒 **What's Protected:**

- All financial data
- Customer information
- Revenue/profit metrics
- Order details
- Inventory data

🛡️ **How It Works:**

- Password hashing (SHA-256)
- Session-based auth
- No plain text storage
- Automatic logout on close

## Next Steps

📖 **Read Full Guides:**

- `SECURITY_GUIDE.md` - Complete security documentation
- `DASHBOARD_USAGE_GUIDE.md` - Full user guide

🎯 **Best Practices:**

- Use password manager
- Change password regularly
- Don't share credentials
- Keep `.env` file secure
- Never commit `.env` to git

## Need Help?

Check documentation in this order:

1. This file (quick start)
2. `SECURITY_GUIDE.md` (security details)
3. `DASHBOARD_USAGE_GUIDE.md` (full guide)
4. `.env.example` (configuration template)

---

**Quick Setup:** `python setup_auth.py`  
**Start Dashboard:** `streamlit run dashboard.py`  
**Documentation:** `SECURITY_GUIDE.md`
