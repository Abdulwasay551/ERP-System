from rest_framework.routers import DefaultRouter
from .api_views import EmployeeViewSet, AttendanceViewSet, LeaveViewSet, PayrollViewSet, PayslipViewSet, HRReportViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'leaves', LeaveViewSet, basename='leave')
router.register(r'payrolls', PayrollViewSet, basename='payroll')
router.register(r'payslips', PayslipViewSet, basename='payslip')
router.register(r'hreports', HRReportViewSet, basename='hrreport')

urlpatterns = router.urls 