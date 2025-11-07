#!/usr/bin/env python3
"""
Dashboard Authentication Setup Script
Interactive script to configure dashboard credentials
"""

import os
import getpass
import shutil
from pathlib import Path

def print_header():
    """Print setup header"""
    print("🔐 Etsy Analytics Dashboard - Authentication Setup")
    print("=" * 50)
    print()

def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    env_example = Path(".env.example")
    
    if env_path.exists():
        print("⚠️  .env file already exists!")
        print()
        response = input("Do you want to update credentials? (y/n): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return False
    else:
        if env_example.exists():
            print("📝 Creating new .env file from template...")
            shutil.copy(env_example, env_path)
        else:
            print("📝 Creating new .env file...")
            with open(env_path, 'w') as f:
                f.write("# Database Configuration\n")
                f.write('DATABASE_URL="postgresql://username:password@localhost:5432/database_name"\n\n')
                f.write("# Dashboard Authentication\n")
    
    return True

def get_username():
    """Get username from user"""
    username = input("Enter username (default: admin): ").strip()
    return username if username else "admin"

def get_password():
    """Get password from user with validation"""
    print()
    print("Password requirements:")
    print("  - Minimum 12 characters")
    print("  - Mix of letters, numbers, and symbols")
    print("  - Avoid common words")
    print()
    
    while True:
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        
        if password != password_confirm:
            print("❌ Passwords don't match! Please try again.")
            print()
            continue
        
        if len(password) < 12:
            print(f"⚠️  Warning: Password is only {len(password)} characters (recommended: 12+)")
            response = input("Continue anyway? (y/n): ").lower()
            if response != 'y':
                print("Please try again with a stronger password.")
                print()
                continue
        
        return password

def update_env_file(username, password):
    """Update .env file with credentials"""
    env_path = Path(".env")
    
    # Read existing content
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update or add credentials
    username_found = False
    password_found = False
    new_lines = []
    
    for line in lines:
        if line.startswith('DASHBOARD_USERNAME='):
            new_lines.append(f'DASHBOARD_USERNAME={username}\n')
            username_found = True
        elif line.startswith('DASHBOARD_PASSWORD='):
            new_lines.append(f'DASHBOARD_PASSWORD={password}\n')
            password_found = True
        else:
            new_lines.append(line)
    
    # Add if not found
    if not username_found:
        new_lines.append(f'DASHBOARD_USERNAME={username}\n')
    if not password_found:
        new_lines.append(f'DASHBOARD_PASSWORD={password}\n')
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    # Secure the file (Unix-like systems)
    try:
        os.chmod(env_path, 0o600)
        secure_msg = "✓ File permissions set to 600 (owner read/write only)"
    except:
        secure_msg = "⚠️  Could not set file permissions (Windows system)"
    
    return secure_msg

def main():
    """Main setup function"""
    print_header()
    
    if not check_env_file():
        return
    
    print()
    print("🔧 Setting up authentication credentials")
    print("=" * 40)
    print()
    
    username = get_username()
    password = get_password()
    
    print()
    print("💾 Saving credentials to .env file...")
    
    secure_msg = update_env_file(username, password)
    
    print("✅ Credentials saved successfully!")
    print()
    print("🔒 Security measures applied:")
    print(f"  {secure_msg}")
    print(f"  ✓ Username: {username}")
    print(f"  ✓ Password: {'*' * len(password)}")
    print()
    print("📋 Next steps:")
    print("  1. Verify your DATABASE_URL in .env is correct")
    print("  2. Start the dashboard: streamlit run dashboard.py")
    print("  3. Login with your new credentials")
    print()
    print("⚠️  Important:")
    print("  - Never share your credentials")
    print("  - Never commit .env file to git")
    print("  - Keep your password secure")
    print("  - Change default database credentials")
    print()
    print("✅ Setup complete!")
    print()
    
    # Offer to start dashboard
    start = input("Would you like to start the dashboard now? (y/n): ").lower()
    if start == 'y':
        print()
        print("🚀 Starting dashboard...")
        print("=" * 40)
        os.system("streamlit run dashboard.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Setup interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your setup and try again.")
