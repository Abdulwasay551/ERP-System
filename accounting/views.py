from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Account

# Create your views here.

@login_required
def accounts_ui(request):
    accounts = Account.objects.filter(company=request.user.company)
    return render(request, 'accounting/accounts-ui.html', {'accounts': accounts})
