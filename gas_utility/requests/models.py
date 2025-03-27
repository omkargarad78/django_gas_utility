from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import Customer, SupportRepresentative

class ServiceRequest(models.Model):
    """
    Service Request model representing a customer's request for gas utility service.
    
    Tracks the entire lifecycle of a service request from creation to resolution.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]
    
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]
    
    SERVICE_TYPES = [
        ('New Connection', 'New Connection'),
        ('Billing Issue', 'Billing Issue'),
        ('Gas Leak', 'Gas Leak'),
        ('Meter Problem', 'Meter Problem'),
        ('Other', 'Other'),
    ]

    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='service_requests'
    )
    service_type = models.CharField(
        max_length=100,
        choices=SERVICE_TYPES,
        help_text="Type of service requested"
    )
    description = models.TextField(help_text="Detailed description of the issue")
    attached_file = models.FileField(
        upload_to='service_requests/', 
        blank=True, 
        null=True,
        help_text="Supporting documentation or images"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='Pending',
        db_index=True
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='Medium',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(
        blank=True, 
        null=True, 
        help_text="Support staff notes"
    )
    assigned_to = models.ForeignKey(
        SupportRepresentative,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests'
    )

    class Meta:
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['priority', 'status']),
        ]

    def __str__(self):
        return f"{self.service_type} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Override save to automatically set resolved_at timestamp."""
        if self.status == 'Resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != 'Resolved':
            self.resolved_at = None
        super().save(*args, **kwargs)
    
    def get_days_open(self):
        """Return the number of days this request has been open."""
        if self.resolved_at:
            return (self.resolved_at - self.created_at).days
        return (timezone.now() - self.created_at).days
