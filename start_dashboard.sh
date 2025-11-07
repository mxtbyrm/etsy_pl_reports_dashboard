#!/bin/bash

# Etsy Analytics Dashboard Launcher
# Quick start script for launching the Streamlit dashboard

echo "🚀 Etsy Analytics Dashboard Launcher"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python3 -c "import streamlit" &> /dev/null; then
    echo ""
    echo "📥 Installing dashboard dependencies..."
    pip install -r requirements_dashboard.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  Warning: .env file not found"
    echo "Please create a .env file with your DATABASE_URL"
    echo "Example:"
    echo "DATABASE_URL=\"postgresql://user:password@localhost:5432/dbname\""
    exit 1
fi

echo "✅ Environment configuration found"

# Check if reports exist in database
echo ""
echo "🔍 Checking for reports in database..."
python3 -c "
import asyncio
from prisma import Prisma
async def check():
    db = Prisma()
    await db.connect()
    count = await db.shopreport.count()
    await db.disconnect()
    return count
try:
    count = asyncio.run(check())
    if count == 0:
        print('⚠️  Warning: No reports found in database')
        print('Please run: python reportsv4_optimized.py --cost-file cost.csv')
        exit(1)
    else:
        print(f'✅ Found {count} shop reports')
except Exception as e:
    print(f'⚠️  Could not verify reports: {e}')
    print('Continuing anyway...')
"

# Launch dashboard
echo ""
echo "🎉 Launching dashboard..."
echo "======================================"
echo ""
echo "📊 Dashboard will open in your browser"
echo "🌐 URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""
streamlit run dashboard.py

# Deactivate virtual environment on exit
deactivate
