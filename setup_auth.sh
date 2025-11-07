#!/bin/bash

# Dashboard Authentication Setup Script
echo "🔐 Etsy Analytics Dashboard - Authentication Setup"
echo "=================================================="
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists!"
    echo ""
    read -p "Do you want to update credentials? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
else
    echo "📝 Creating new .env file..."
    cp .env.example .env
fi

echo ""
echo "🔧 Setting up authentication credentials"
echo "=========================================="
echo ""

# Get username
read -p "Enter username (default: admin): " username
username=${username:-admin}

# Get password
echo ""
echo "Password requirements:"
echo "  - Minimum 12 characters"
echo "  - Mix of letters, numbers, and symbols"
echo "  - Avoid common words"
echo ""
read -s -p "Enter password: " password
echo ""
read -s -p "Confirm password: " password_confirm
echo ""

# Check if passwords match
if [ "$password" != "$password_confirm" ]; then
    echo "❌ Passwords don't match!"
    exit 1
fi

# Check password length
if [ ${#password} -lt 12 ]; then
    echo "⚠️  Warning: Password is less than 12 characters"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Please run again with a stronger password."
        exit 1
    fi
fi

# Update .env file
echo ""
echo "💾 Saving credentials to .env file..."

# Check if .env has DATABASE_URL, if not copy from example
if ! grep -q "DATABASE_URL" .env; then
    echo "# Database Configuration" > .env
    echo "DATABASE_URL=\"postgresql://username:password@localhost:5432/database_name\"" >> .env
    echo "" >> .env
fi

# Update authentication settings
sed -i.bak "s/DASHBOARD_USERNAME=.*/DASHBOARD_USERNAME=$username/" .env 2>/dev/null || \
    echo "DASHBOARD_USERNAME=$username" >> .env

sed -i.bak "s/DASHBOARD_PASSWORD=.*/DASHBOARD_PASSWORD=$password/" .env 2>/dev/null || \
    echo "DASHBOARD_PASSWORD=$password" >> .env

# Remove backup file
rm -f .env.bak

# Secure the file
chmod 600 .env

echo "✅ Credentials saved successfully!"
echo ""
echo "🔒 Security measures applied:"
echo "  ✓ .env file permissions set to 600 (owner read/write only)"
echo "  ✓ Username: $username"
echo "  ✓ Password: $(echo "$password" | sed 's/./*/g')"
echo ""
echo "📋 Next steps:"
echo "  1. Verify your DATABASE_URL in .env is correct"
echo "  2. Start the dashboard: streamlit run dashboard.py"
echo "  3. Login with your new credentials"
echo ""
echo "⚠️  Important:"
echo "  - Never share your credentials"
echo "  - Never commit .env file to git"
echo "  - Keep your password secure"
echo ""
echo "✅ Setup complete!"
