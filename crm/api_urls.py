from rest_framework.routers import DefaultRouter
from .api_views import CustomerViewSet, CustomerLedgerAdjustmentViewSet, LeadViewSet, OpportunityViewSet, CommunicationLogViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'customer-ledger-adjustments', CustomerLedgerAdjustmentViewSet, basename='customerledgeradjustment')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'communications', CommunicationLogViewSet, basename='communicationlog')

urlpatterns = router.urls 