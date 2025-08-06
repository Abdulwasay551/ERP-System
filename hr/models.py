from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from user_auth.models import Company, User
from crm.models import Partner  # Import centralized Partner model
from accounting.models import Account
from decimal import Decimal

class Department(models.Model):
    """Department model for organizational structure"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    parent_department = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_departments')
    department_head = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['company', 'name']

    def __str__(self):
        return self.name

class Designation(models.Model):
    """Job positions/titles within the company"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='designations')
    title = models.CharField(max_length=100)
    level = models.CharField(max_length=50, choices=[
        ('entry', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('manager', 'Manager'),
        ('director', 'Director'),
        ('executive', 'Executive')
    ], default='entry')
    salary_range_min = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salary_range_max = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['company', 'title']

    def __str__(self):
        return self.title

class SalaryStructure(models.Model):
    """Template for salary components"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='salary_structures')
    name = models.CharField(max_length=100)
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, related_name='salary_structures')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    house_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    provident_fund_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.designation.title}"

    @property
    def gross_salary(self):
        return (self.basic_salary + self.house_allowance + self.transport_allowance + 
                self.medical_allowance + self.other_allowances)

class Employee(models.Model):
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
        ('consultant', 'Consultant'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('resigned', 'Resigned'),
        ('terminated', 'Terminated'),
        ('on_leave', 'On Leave'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_profile')
    
    # Optional link to centralized Partner for consistency
    partner = models.OneToOneField(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_profile')
    
    # Employee-specific fields
    employee_id = models.CharField(max_length=50, unique=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    
    # Enhanced organizational fields
    department_old = models.CharField(max_length=100, blank=True, null=True)  # Temporary field to store old data
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    reporting_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    # Employment details
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time')
    date_joined = models.DateField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=50, blank=True)
    
    # Salary and benefits
    salary_structure = models.ForeignKey(SalaryStructure, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    current_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bank_account = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    resignation_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)
    
    # Documents
    profile_picture = models.ImageField(upload_to='employee_photos/', blank=True, null=True)
    cv_document = models.FileField(upload_to='employee_docs/cv/', blank=True, null=True)
    contract_document = models.FileField(upload_to='employee_docs/contracts/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    def save(self, *args, **kwargs):
        # Auto-generate employee ID if not provided
        if not self.employee_id:
            count = Employee.objects.filter(company=self.company).count()
            self.employee_id = f"EMP{count + 1:04d}"
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def current_age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

class Contractor(models.Model):
    """Contractor model that links to centralized Partner for external workers"""
    CONTRACT_TYPE_CHOICES = [
        ('hourly', 'Hourly'),
        ('project', 'Project Based'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    # Link to centralized Partner
    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, related_name='contractor_profile')
    
    # Contractor-specific fields
    contractor_id = models.CharField(max_length=50, unique=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contractors')
    contract_type = models.CharField(max_length=50, choices=CONTRACT_TYPE_CHOICES, default='hourly')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    contract_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    skills = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Contractor: {self.partner.name}"

    def save(self, *args, **kwargs):
        # Auto-generate contractor ID if not provided
        if not self.contractor_id:
            self.contractor_id = f"CONT{self.pk or Contractor.objects.count() + 1:04d}"
        
        # Ensure partner is marked as contractor/vendor
        if self.partner:
            self.partner.is_vendor = True
            self.partner.save()
        super().save(*args, **kwargs)

class ShiftType(models.Model):
    """Define different shift patterns"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='shift_types')
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration = models.DurationField(default='01:00:00')  # 1 hour default
    grace_period = models.DurationField(default='00:15:00')  # 15 minutes default
    working_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('on_leave', 'On Leave'),
        ('holiday', 'Holiday'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    shift_type = models.ForeignKey(ShiftType, on_delete=models.SET_NULL, null=True, blank=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    working_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    location = models.CharField(max_length=200, blank=True)  # For remote work tracking
    notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_attendance')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.status})"

    def calculate_working_hours(self):
        """Calculate actual working hours based on check-in/out times"""
        if self.check_in and self.check_out:
            from datetime import datetime, timedelta
            check_in_dt = datetime.combine(self.date, self.check_in)
            check_out_dt = datetime.combine(self.date, self.check_out)
            
            # Handle overnight shifts
            if check_out_dt < check_in_dt:
                check_out_dt += timedelta(days=1)
            
            total_time = check_out_dt - check_in_dt
            
            # Subtract break time if applicable
            if self.break_start and self.break_end:
                break_start_dt = datetime.combine(self.date, self.break_start)
                break_end_dt = datetime.combine(self.date, self.break_end)
                if break_end_dt > break_start_dt:
                    break_time = break_end_dt - break_start_dt
                    total_time -= break_time
            
            hours = total_time.total_seconds() / 3600
            self.working_hours = round(hours, 2)
            
            # Calculate overtime
            if self.shift_type and hours > float(self.shift_type.working_hours):
                self.overtime_hours = round(hours - float(self.shift_type.working_hours), 2)
            
        return self.working_hours

class LeaveType(models.Model):
    """Define different types of leave policies"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='leave_types')
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10)
    annual_entitlement = models.DecimalField(max_digits=5, decimal_places=1)  # Days per year
    carry_forward_allowed = models.BooleanField(default=False)
    max_carry_forward = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    encashment_allowed = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=True)
    advance_notice_days = models.IntegerField(default=0)  # Minimum days notice required
    is_paid = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['company', 'code']

    def __str__(self):
        return f"{self.name} ({self.code})"

class EmployeeLeaveBalance(models.Model):
    """Track leave balances for each employee"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='employee_balances')
    year = models.IntegerField()
    entitled_days = models.DecimalField(max_digits=5, decimal_places=1)
    used_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    carry_forward_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    
    class Meta:
        unique_together = ['employee', 'leave_type', 'year']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.year})"

    @property
    def available_days(self):
        return self.entitled_days + self.carry_forward_days - self.used_days

class Leave(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.DecimalField(max_digits=5, decimal_places=1)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    covering_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='covering_leaves')
    emergency_contact = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} {self.leave_type} ({self.start_date} - {self.end_date})"

    def calculate_days(self):
        """Calculate the number of leave days"""
        delta = self.end_date - self.start_date
        return delta.days + 1

class PayrollPeriod(models.Model):
    """Define payroll processing periods"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payroll_periods')
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    pay_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ], default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payrolls', null=True, blank=True)

    # Salary components
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    house_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Deductions
    provident_fund = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    income_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Totals
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Working days and hours
    working_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    present_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    
    # Accounting integration
    salary_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='payroll_salary')
    benefits_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='payroll_benefits')
    liability_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='payroll_liabilities')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payrolls')

    class Meta:
        unique_together = ['employee', 'period']

    def __str__(self):
        return f"Payroll {self.employee} ({self.period})"

    def calculate_totals(self):
        """Calculate gross salary, total deductions, and net salary"""
        self.gross_salary = (
            self.basic_salary + self.house_allowance + self.transport_allowance +
            self.medical_allowance + self.other_allowances + self.overtime_amount + self.bonus
        )
        
        self.total_deductions = (
            self.provident_fund + self.income_tax + self.loan_deduction +
            self.advance_deduction + self.other_deductions
        )
        
        self.net_salary = self.gross_salary - self.total_deductions
        return self.net_salary

class Payslip(models.Model):
    payroll = models.OneToOneField(Payroll, on_delete=models.CASCADE, related_name='payslip')
    pdf_file = models.FileField(upload_to='payslips/', blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Payslip {self.payroll}"

class EmployeeLoan(models.Model):
    """Employee loans and advances"""
    LOAN_TYPE_CHOICES = [
        ('personal', 'Personal Loan'),
        ('salary_advance', 'Salary Advance'),
        ('emergency', 'Emergency Loan'),
        ('house', 'House Loan'),
        ('vehicle', 'Vehicle Loan'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Annual percentage
    installment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_installments = models.IntegerField()
    paid_installments = models.IntegerField(default=0)
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purpose = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.loan_type} ({self.amount})"

class PerformanceAppraisal(models.Model):
    """Employee performance appraisals"""
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]

    STATUS_CHOICES = [
        ('pending_self', 'Pending Self Review'),
        ('pending_manager', 'Pending Manager Review'),
        ('pending_hr', 'Pending HR Review'),
        ('completed', 'Completed'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='appraisals')
    period_start = models.DateField()
    period_end = models.DateField()
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviewed_appraisals')
    
    # Self assessment
    self_goals_achievement = models.TextField(blank=True)
    self_strengths = models.TextField(blank=True)
    self_areas_improvement = models.TextField(blank=True)
    self_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    
    # Manager assessment
    manager_goals_achievement = models.TextField(blank=True)
    manager_strengths = models.TextField(blank=True)
    manager_areas_improvement = models.TextField(blank=True)
    manager_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    manager_comments = models.TextField(blank=True)
    
    # Overall
    final_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    promotion_recommended = models.BooleanField(default=False)
    increment_recommended = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    training_recommendations = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_self')
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee} Appraisal ({self.period_start} - {self.period_end})"

class Training(models.Model):
    """Training courses and programs"""
    TRAINING_TYPE_CHOICES = [
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('course', 'Course'),
        ('conference', 'Conference'),
        ('webinar', 'Webinar'),
        ('certification', 'Certification Program'),
        ('on_job', 'On-the-Job Training'),
        ('orientation', 'Orientation'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='trainings')
    title = models.CharField(max_length=200)
    description = models.TextField()
    training_type = models.CharField(max_length=50, choices=TRAINING_TYPE_CHOICES, default='workshop')
    instructor = models.CharField(max_length=100, blank=True)
    duration_hours = models.DecimalField(max_digits=5, decimal_places=1)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_participants = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    is_mandatory = models.BooleanField(default=False)
    certificate_issued = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class TrainingEnrollment(models.Model):
    """Employee enrollment in training programs"""
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('failed', 'Failed'),
    ]

    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='enrollments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='training_enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    certificate_path = models.FileField(upload_to='certificates/', blank=True, null=True)

    class Meta:
        unique_together = ['training', 'employee']

    def __str__(self):
        return f"{self.employee} - {self.training}"

class ExitInterview(models.Model):
    """Exit interview for departing employees"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='exit_interview')
    interviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conducted_exit_interviews')
    interview_date = models.DateField()
    reason_for_leaving = models.TextField()
    job_satisfaction_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    would_recommend_company = models.BooleanField()
    suggestions = models.TextField(blank=True)
    assets_returned = models.BooleanField(default=False)
    final_settlement_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Exit Interview - {self.employee}"

class HRReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('attendance', 'Attendance Report'),
        ('payroll', 'Payroll Report'),
        ('leaves', 'Leave Report'),
        ('employee_directory', 'Employee Directory'),
        ('recruitment', 'Recruitment Report'),
        ('appraisal', 'Appraisal Report'),
        ('training', 'Training Report'),
        ('attrition', 'Attrition Report'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='hr_reports')
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    period_start = models.DateField()
    period_end = models.DateField()
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_hr_reports',null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    file_path = models.FileField(upload_to='hr_reports/', blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} ({self.period_start} - {self.period_end})"

class JobVacancy(models.Model):
    """Job vacancy model for recruitment"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('on_hold', 'On Hold'),
        ('closed', 'Closed'),
        ('filled', 'Filled'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_vacancies')
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='vacancies')
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, related_name='vacancies', null=True, blank=True)
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField(blank=True)
    salary_range = models.CharField(max_length=100, blank=True)
    experience_required = models.CharField(max_length=100, blank=True)
    qualification_required = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=50, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time')
    no_of_positions = models.IntegerField(default=1)
    application_deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_vacancies', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.department}"

class JobApplication(models.Model):
    """Job application model"""
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('screening', 'Under Screening'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interviewed', 'Interviewed'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
        ('on_hold', 'On Hold'),
    ]
    
    vacancy = models.ForeignKey(JobVacancy, on_delete=models.CASCADE, related_name='applications')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    current_position = models.CharField(max_length=200, blank=True)
    current_company = models.CharField(max_length=200, blank=True)
    experience_years = models.IntegerField(default=0)
    expected_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.vacancy}"

class EmployeeBenefit(models.Model):
    """Employee benefits model"""
    BENEFIT_TYPE_CHOICES = [
        ('health_insurance', 'Health Insurance'),
        ('life_insurance', 'Life Insurance'),
        ('dental', 'Dental'),
        ('vision', 'Vision'),
        ('retirement', 'Retirement Plan'),
        ('paid_time_off', 'Paid Time Off'),
        ('sick_leave', 'Sick Leave'),
        ('maternity_leave', 'Maternity Leave'),
        ('paternity_leave', 'Paternity Leave'),
        ('education', 'Education Assistance'),
        ('gym_membership', 'Gym Membership'),
        ('meal_allowance', 'Meal Allowance'),
        ('transport_allowance', 'Transport Allowance'),
        ('phone_allowance', 'Phone Allowance'),
        ('other', 'Other'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employee_benefits')
    name = models.CharField(max_length=200)
    benefit_type = models.CharField(max_length=50, choices=BENEFIT_TYPE_CHOICES)
    description = models.TextField()
    eligibility_criteria = models.TextField(blank=True)
    cost_to_company = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employee_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_mandatory = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.benefit_type}"

class EmployeeBenefitEnrollment(models.Model):
    """Employee benefit enrollment"""
    benefit = models.ForeignKey(EmployeeBenefit, on_delete=models.CASCADE, related_name='enrollments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='benefit_enrollments')
    enrollment_date = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['benefit', 'employee']
    
    def __str__(self):
        return f"{self.employee} - {self.benefit}"

class HRPolicy(models.Model):
    """HR policies and procedures"""
    POLICY_TYPE_CHOICES = [
        ('attendance', 'Attendance Policy'),
        ('leave', 'Leave Policy'),
        ('conduct', 'Code of Conduct'),
        ('dress_code', 'Dress Code'),
        ('harassment', 'Anti-Harassment'),
        ('safety', 'Safety Policy'),
        ('it_usage', 'IT Usage Policy'),
        ('social_media', 'Social Media Policy'),
        ('confidentiality', 'Confidentiality'),
        ('disciplinary', 'Disciplinary Action'),
        ('grievance', 'Grievance Procedure'),
        ('other', 'Other'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='hr_policies')
    title = models.CharField(max_length=200)
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPE_CHOICES)
    content = models.TextField()
    version = models.CharField(max_length=20, default='1.0')
    effective_date = models.DateField()
    review_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approved_policies')
    document_file = models.FileField(upload_to='hr_policies/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} (v{self.version})"

class EmployeeRelation(models.Model):
    """Employee relations and disciplinary actions"""
    RELATION_TYPE_CHOICES = [
        ('grievance', 'Grievance'),
        ('complaint', 'Complaint'),
        ('disciplinary', 'Disciplinary Action'),
        ('counseling', 'Counseling'),
        ('warning', 'Warning'),
        ('appreciation', 'Appreciation'),
        ('feedback', 'Feedback'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='relations')
    relation_type = models.CharField(max_length=50, choices=RELATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_relations', null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_relations', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    action_taken = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee} - {self.relation_type}: {self.subject}"
