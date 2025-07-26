"""
WSGI config for setting project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setting.settings')

# Check if we're in a Vercel environment and static files need to be collected
if os.environ.get('VERCEL') == True:
    try:
        # Get the project directory
        project_dir = Path(__file__).parent.parent
        staticfiles_dir = project_dir / 'staticfiles'
        
        # If staticfiles directory doesn't exist or is empty, collect static files
        if not staticfiles_dir.exists() or not any(staticfiles_dir.iterdir()):
            print("Collecting static files for Vercel deployment...")
            # Set up Django settings
            import django
            django.setup()
            
            # Collect static files
            from django.core.management import call_command
            call_command('collectstatic', '--noinput', '--clear')
            print("Static files collected successfully!")
            
            # Verify files were collected
            if staticfiles_dir.exists():
                files = list(staticfiles_dir.rglob('*'))
                print(f"Collected {len([f for f in files if f.is_file()])} static files")
    except Exception as e:
        print(f"Warning: Could not collect static files: {e}")

try:
    application = get_wsgi_application()
    app = application  # For Vercel compatibility
except Exception as e:
    # Log the error for debugging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error(f"WSGI application failed to load: {e}")
    raise