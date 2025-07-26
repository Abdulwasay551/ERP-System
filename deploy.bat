@echo off
echo =======================================
echo  Django ERP - Vercel Deployment Script
echo =======================================

echo.
echo 1. Installing/Updating Vercel CLI...
npm install -g vercel

echo.
echo 2. Checking project structure...
if not exist "manage.py" (
    echo ERROR: manage.py not found. Run this script from the Django project root.
    pause
    exit /b 1
)

echo.
echo 3. Testing Django configuration...
python manage.py check --deploy
if errorlevel 1 (
    echo ERROR: Django configuration issues found. Please fix them first.
    pause
    exit /b 1
)

echo.
echo 4. Collecting static files...
python manage.py collectstatic --noinput
if errorlevel 1 (
    echo WARNING: Static files collection failed. Continuing anyway...
)

echo.
echo 5. Starting Vercel deployment...
echo Choose your deployment type:
echo [1] Development deployment (preview)
echo [2] Production deployment
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo Deploying to preview environment...
    vercel
) else if "%choice%"=="2" (
    echo Deploying to production...
    vercel --prod
) else (
    echo Invalid choice. Deploying to preview environment...
    vercel
)

echo.
echo =======================================
echo  Deployment Complete!
echo =======================================
echo.
echo Your app should be available at the URL shown above.
echo.
echo Next steps:
echo 1. Set up environment variables in Vercel dashboard
echo 2. Configure your custom domain (optional)
echo 3. Test all functionality
echo.
pause
