from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions
from .serializers import CompanySerializer, RoleSerializer, UserSerializer
from .models import Company, Role, User
from crm.models import Customer
from sales.models import SalesOrder
from inventory.models import StockItem
from hr.models import Employee

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
    context= {
        "public": True,  # Example context variable
        "title": "Welcome to FutureERP",
        "description": "Your comprehensive ERP solution for managing business operations efficiently."
    }
    return render(request, 'user_auth/login.html', context)

# Logout view
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect(reverse('login'))

# Dashboard view
@login_required
def dashboard(request):
    from purchase.models import Supplier, PurchaseOrder
    from products.models import Product
    from manufacturing.models import WorkOrder
    from project_mgmt.models import Project
    from accounting.models import Account
    
    company = request.user.company if request.user.company else None
    
    if company:
        # Core statistics
        stat_customers = Customer.objects.filter(company=company).count()
        stat_sales = SalesOrder.objects.filter(company=company).count()
        stat_inventory = StockItem.objects.filter(company=company).count()
        stat_employees = Employee.objects.filter(company=company).count()
        
        # Additional comprehensive statistics
        stat_suppliers = Supplier.objects.filter(company=company).count()
        stat_products = Product.objects.filter(company=company).count()
        stat_purchase_orders = PurchaseOrder.objects.filter(company=company).count()
        stat_work_orders = WorkOrder.objects.filter(company=company).count()
        stat_projects = Project.objects.filter(company=company).count()
        stat_accounts = Account.objects.filter(company=company).count()
        
        # Recent activities
        recent_sales = SalesOrder.objects.filter(company=company).order_by('-created_at')[:5]
        recent_purchases = PurchaseOrder.objects.filter(company=company).order_by('-created_at')[:5]
        recent_products = Product.objects.filter(company=company).order_by('-created_at')[:5]
        
        # Quick metrics
        total_revenue = sum([so.total for so in recent_sales if so.total])
        pending_orders = SalesOrder.objects.filter(company=company, status='pending').count()
        low_stock_items = StockItem.objects.filter(company=company, quantity__lt=10).count()
        
    else:
        # Default values for users without company
        stat_customers = stat_sales = stat_inventory = stat_employees = 0
        stat_suppliers = stat_products = stat_purchase_orders = 0
        stat_work_orders = stat_projects = stat_accounts = 0
        recent_sales = recent_purchases = recent_products = []
        total_revenue = pending_orders = low_stock_items = 0
    
    context = {
        # Core stats
        'stat_customers': stat_customers,
        'stat_sales': stat_sales,
        'stat_inventory': stat_inventory,
        'stat_employees': stat_employees,
        
        # Extended stats
        'stat_suppliers': stat_suppliers,
        'stat_products': stat_products,
        'stat_purchase_orders': stat_purchase_orders,
        'stat_work_orders': stat_work_orders,
        'stat_projects': stat_projects,
        'stat_accounts': stat_accounts,
        
        # Recent activities
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
        'recent_products': recent_products,
        
        # Quick metrics
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'low_stock_items': low_stock_items,
        'public':True,
    }
    return render(request, 'dashboard_complete.html', context)

def index(request):
    context= {
        "public": True,  # Example context variable
        "title": "Welcome to FutureERP",
        "description": "Your comprehensive ERP solution for managing business operations efficiently."
    }
    return render(request, 'index.html', context)

# Templates:
# - user_auth/login.html (for login view)
# - base.html (global base template)
# - dashboard.html (dashboard placeholder)
# Place user_auth/login.html in a 'templates/user_auth/' directory inside your app or project root.
# Place base.html and dashboard.html in a global 'templates/' directory at the project root.

class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Company.objects.all()

class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Role.objects.all()

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
