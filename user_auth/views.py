from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required

# Login view

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'user_auth/login.html')

# Logout view
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect(reverse('login'))

# Dashboard placeholder view
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

# Templates:
# - user_auth/login.html (for login view)
# - base.html (global base template)
# - dashboard.html (dashboard placeholder)
# Place user_auth/login.html in a 'templates/user_auth/' directory inside your app or project root.
# Place base.html and dashboard.html in a global 'templates/' directory at the project root.
