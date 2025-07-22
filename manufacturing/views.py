from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import BillOfMaterials

# Create your views here.

@login_required
def boms_ui(request):
    boms = BillOfMaterials.objects.filter(company=request.user.company)
    return render(request, 'manufacturing/boms-ui.html', {'boms': boms})
