# Etsy Analytics Dashboard

A comprehensive analytics dashboard for Etsy shop data with authentication.

## Features

- 📊 Multiple report types (Shop Overview, Listing Analysis, Product Analysis)
- 📈 Interactive visualizations with Plotly
- 🔒 Password-protected access
- 📅 Flexible date range selection
- 💾 Data export (CSV/JSON)

## Deployment

### Environment Variables Required

```
DATABASE_URL=postgresql://user:password@host:port/database
DASHBOARD_USERNAME=your_username
DASHBOARD_PASSWORD=your_hashed_password
```

### Generate Password Hash

```python
import hashlib
password = "your_password"
hashed = hashlib.sha256(password.encode()).hexdigest()
print(hashed)
```

## Local Development

```bash
pip install -r requirements_dashboard.txt
streamlit run dashboard.py
```

## Security Notes

- Never commit `.env` file to Git
- Use strong passwords
- Rotate credentials regularly
- Monitor access logs
