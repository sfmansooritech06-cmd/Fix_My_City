from django.contrib.auth.models import AbstractUser
from django.db import models


# =====================================================
# USER
# =====================================================

class User(AbstractUser):

    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('officer', 'Officer'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(
        unique=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='citizen'
    )

    def __str__(self):
        return self.username


# =====================================================
# CITIZEN
# =====================================================

class Citizen(models.Model):

    SECURITY_QUESTION_CHOICES = (
        ("pet", "What was the name of your first pet?"),
        ("school", "What was the name of your first school?"),
        ("city", "What city were you born in?"),
        ("nickname", "What was your childhood nickname?"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='citizen_profile'
    )

    citizen_id = models.CharField(
        max_length=20,
        unique=True
    )

    full_name = models.CharField(
        max_length=150
    )

    phone = models.CharField(
        max_length=15
    )

    # Security question used for password recovery
    security_question = models.CharField(
        max_length=30,
        choices=SECURITY_QUESTION_CHOICES,
        default=""
    )

    # Stores hashed security answer
    security_answer = models.CharField(
        max_length=255,
        default=""
    )

    is_approved = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.full_name} ({self.citizen_id})"


# =====================================================
# OFFICER
# =====================================================

class Officer(models.Model):

    DEPARTMENT_CHOICES = (
        ('road', 'Road & Infrastructure'),
        ('sanitation', 'Sanitation'),
        ('streetlight', 'Streetlight / Electricity'),
        ('water', 'Water Supply'),
        ('property', 'Public Property'),
        ('other', 'Other'),
    )

    SECURITY_QUESTION_CHOICES = (
        ("pet", "What was the name of your first pet?"),
        ("school", "What was the name of your first school?"),
        ("city", "What city were you born in?"),
        ("nickname", "What was your childhood nickname?"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='officer_profile'
    )

    employee_id = models.CharField(
        max_length=10,
        unique=True
    )

    full_name = models.CharField(
        max_length=150
    )

    phone = models.CharField(
        max_length=15
    )

    department = models.CharField(
        max_length=30,
        choices=DEPARTMENT_CHOICES
    )

    # Security question used for password recovery
    security_question = models.CharField(
        max_length=30,
        choices=SECURITY_QUESTION_CHOICES,
        default=""
    )

    # Stores hashed security answer
    security_answer = models.CharField(
        max_length=255,
        default=""
    )

    is_approved = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"


# =====================================================
# COMPLAINT
# =====================================================

class Complaint(models.Model):

    CATEGORY_CHOICES = (
        ('pothole', 'Pothole'),
        ('garbage', 'Garbage'),
        ('streetlight', 'Streetlight'),
        ('water', 'Water Leakage'),
        ('property', 'Damaged Public Property'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('reported', 'Reported'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    )

    complaint_id = models.CharField(
        max_length=20,
        unique=True
    )

    citizen = models.ForeignKey(
        Citizen,
        on_delete=models.CASCADE,
        related_name='complaints'
    )

    assigned_officer = models.ForeignKey(
        Officer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints'
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    photo = models.ImageField(
        upload_to='complaints/',
        blank=True,
        null=True
    )

    address = models.TextField()

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='reported'
    )

    upvotes = models.PositiveIntegerField(
        default=0
    )

    # =================================================
    # OFFICER PROGRESS
    # =================================================

    progress = models.PositiveIntegerField(
        default=0
    )

    progress_note = models.TextField(
        blank=True,
        null=True
    )

    progress_updated_at = models.DateTimeField(
        auto_now=True
    )

    # =================================================
    # TIMESTAMPS
    # =================================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.complaint_id} - {self.title}"