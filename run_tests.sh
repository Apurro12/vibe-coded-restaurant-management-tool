#!/bin/bash

# Quick test runner script for the restaurant management system

echo "🧪 Restaurant Management System Test Runner"
echo "=========================================="

# Install dependencies if needed
if [ ! -f ".venv/pyvenv.cfg" ]; then
    echo "📦 Installing dependencies with uv..."
    uv pip install -r requirements.txt
    echo "✅ Dependencies installed"
    echo ""
fi

# Check if server is running
if ! curl -s "http://127.0.0.1:5001/" > /dev/null; then
    echo "❌ Server not running at http://127.0.0.1:5001/"
    echo "   Please start the server first: cd app && python app.py"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Run the comprehensive test
echo "🚀 Running comprehensive E2E tests..."
python3 test_app.py

echo ""
echo "🏁 Test run completed!"