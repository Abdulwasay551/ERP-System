from django.urls import path
from . import views
from .views import CustomerPageView
from .views import LeadPageView
from .views import OpportunityPageView
from .views import CommunicationLogPageView

urlpatterns = [
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/add/', views.CustomerCreateView.as_view(), name='customer_add'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
]

urlpatterns += [
    path('customers-ui/', CustomerPageView.as_view(), name='customer_page'),
]

urlpatterns += [
    path('leads-ui/', LeadPageView.as_view(), name='lead_page'),
]

urlpatterns += [
    path('opportunities-ui/', OpportunityPageView.as_view(), name='opportunity_page'),
]

urlpatterns += [
    path('communications-ui/', CommunicationLogPageView.as_view(), name='communicationlog_page'),
] 