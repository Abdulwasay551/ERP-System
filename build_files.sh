#!/bin/bash

echo "Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Creating directories..."
mkdir -p staticfiles
mkdir -p static
mkdir -p media

echo "Running migrations..."
# Remove existing migrations and create fresh ones
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
sleep 2

# Make fresh migrations for all apps
python3 manage.py makemigrations user_auth --noinput
python3 manage.py makemigrations accounting --noinput
python3 manage.py makemigrations crm --noinput
python3 manage.py makemigrations sales --noinput
python3 manage.py makemigrations inventory --noinput
python3 manage.py makemigrations purchase --noinput
python3 manage.py makemigrations hr --noinput
python3 manage.py makemigrations manufacturing --noinput
python3 manage.py makemigrations project_mgmt --noinput
python3 manage.py makemigrations analytics --noinput
python3 manage.py makemigrations core --noinput
sleep 2

# Apply migrations
python3 manage.py migrate --noinput

echo "Collecting static files..."

# Clear staticfiles directory
rm -rf staticfiles/*
mkdir -p staticfiles

# Collect all static files including Django admin
echo "Collecting Django static files..."
python3 manage.py collectstatic --noinput --verbosity=2

# Copy your custom static files (if they exist)
echo "Copying custom static files..."
if [ -d "static" ]; then
    cp -r static/* staticfiles/
    echo "✓ Custom static files copied"
else
    echo "⚠ Custom static directory not found"
fi

echo "Build completed successfully!" 