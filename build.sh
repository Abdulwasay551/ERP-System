#!/bin/bash

# Vercel build script for Django static files
echo "Building Django application for Vercel..."

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Creating static directories..."
mkdir -p static
mkdir -p staticfiles

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Build complete!"
