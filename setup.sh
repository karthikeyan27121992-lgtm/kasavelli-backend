#!/bin/bash

echo "=== Silver Jewellery Shop - Backend Setup ==="
echo ""

# Check if virtual environment exists
if [ ! -d "myenv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv myenv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source myenv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env file from .env.example and configure your database credentials"
    exit 1
fi

# Create migrations
echo "Creating migrations..."
python manage.py makemigrations users
python manage.py makemigrations products
python manage.py makemigrations notifications
python manage.py makemigrations payments

# Run migrations
echo "Running migrations..."
python manage.py migrate

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Create superuser: python manage.py createsuperuser"
echo "2. Start server: python manage.py runserver"
echo ""

# Made with Bob
