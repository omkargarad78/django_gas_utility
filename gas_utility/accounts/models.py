from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Adds role-based access control for customers and support staff.
    """
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('support_staff', 'Support Staff'),
    )
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='customer',
        verbose_name=_("User Role"),
        help_text=_("Determines the user's permissions and access level")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ['-date_joined']

    def is_support_staff(self):
        """Check if user is a support staff member."""
        return self.role == 'support_staff'
    
    def is_customer(self):
        """Check if user is a customer."""
        return self.role == 'customer'


class Customer(models.Model):
    """
    Customer model representing a user who can submit service requests.
    
    This model extends the base User model with additional customer-specific fields.
    """
    user = models.OneToOneField(
        'accounts.User', 
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )
    phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        help_text=_("Customer's phone number for contact purposes")
    )
    address = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Customer's address for service visits")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return self.user.username
    
    def get_full_name(self):
        """Return the customer's full name or username if not available."""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username


class SupportRepresentative(models.Model):
    """
    Support Representative model representing staff who handle service requests.
    
    This model extends the base User model with additional support staff specific fields.
    """
    user = models.OneToOneField(
        'accounts.User', 
        on_delete=models.CASCADE,
        related_name='support_profile'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Department the support representative belongs to")
    )
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Employee ID for internal reference")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Support Representative")
        verbose_name_plural = _("Support Representatives")
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return self.user.username
    
    def get_full_name(self):
        """Return the support representative's full name or username if not available."""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username
    
    def get_active_requests_count(self):
        """Return the count of active requests assigned to this representative."""
        return self.assigned_requests.exclude(status='Resolved').count()
