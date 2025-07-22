from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PurchaseOrder

# Create your views here.

@login_required
def purchaseorders_ui(request):
    purchaseorders = PurchaseOrder.objects.filter(company=request.user.company)
    return render(request, 'purchase/purchaseorders-ui.html', {'purchaseorders': purchaseorders})
