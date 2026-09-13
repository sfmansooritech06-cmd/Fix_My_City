from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('officer', 'Officer'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='citizen'
    )

    def __str__(self):
        return self.username


class Citizen(models.Model):

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

    def __str__(self):
        return f"{self.full_name} ({self.citizen_id})"


class Officer(models.Model):

    DEPARTMENT_CHOICES = (
        ('road', 'Road & Infrastructure'),
        ('sanitation', 'Sanitation'),
        ('streetlight', 'Streetlight / Electricity'),
        ('water', 'Water Supply'),
        ('property', 'Public Property'),
        ('other', 'Other'),
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

    is_approved = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"