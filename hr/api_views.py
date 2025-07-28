from rest_framework import viewsets, permissions
from .models import Employee, Contractor, Attendance, Leave, Payroll, Payslip, HRReport
from .serializers import EmployeeSerializer, ContractorSerializer, AttendanceSerializer, LeaveSerializer, PayrollSerializer, PayslipSerializer, HRReportSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Employee.objects.filter(company=self.request.user.company)

class ContractorViewSet(viewsets.ModelViewSet):
    serializer_class = ContractorSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Contractor.objects.filter(company=self.request.user.company)

class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Attendance.objects.filter(employee__company=self.request.user.company)

class LeaveViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Leave.objects.filter(employee__company=self.request.user.company)

class PayrollViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Payroll.objects.filter(employee__company=self.request.user.company)

class PayslipViewSet(viewsets.ModelViewSet):
    serializer_class = PayslipSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Payslip.objects.filter(payroll__employee__company=self.request.user.company)

class HRReportViewSet(viewsets.ModelViewSet):
    serializer_class = HRReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return HRReport.objects.filter(company=self.request.user.company) 