from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now
from django.contrib import messages
from django.db.models import Q, Count, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import User, Customer, SupportRepresentative
from .models import ServiceRequest
from .forms import ServiceRequestForm, ServiceRequestUpdateForm
from .serializers import (
    ServiceRequestSerializer, ServiceRequestCreateSerializer,
    ServiceRequestUpdateSerializer, ServiceRequestStatisticsSerializer
)

import logging

# Set up logger
logger = logging.getLogger(__name__)

# Custom permissions
class IsSupportStaff(permissions.BasePermission):
    """
    Permission to only allow support staff to access the view.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'support_staff'

class IsCustomer(permissions.BasePermission):
    """
    Permission to only allow customers to access the view.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'customer'

class IsOwnerOrSupportStaff(permissions.BasePermission):
    """
    Permission to only allow owners of an object or support staff to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Support staff can access any object
        if hasattr(request.user, 'role') and request.user.role == 'support_staff':
            return True
        
        # Check if the object has a customer field directly
        if hasattr(obj, 'customer'):
            try:
                customer = Customer.objects.get(user=request.user)
                return obj.customer == customer
            except Customer.DoesNotExist:
                return False
        
        # For other cases, deny access
        return False

# API ViewSets
class ServiceRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows service requests to be viewed or edited.
    """
    queryset = ServiceRequest.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'service_type']
    search_fields = ['description', 'customer__user__username', 'customer__user__email']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ServiceRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ServiceRequestUpdateSerializer
        return ServiceRequestSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsOwnerOrSupportStaff]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Limit service requests based on the requesting user's role.
        """
        user = self.request.user
        
        # Support staff can see all service requests
        if user.role == 'support_staff':
            return ServiceRequest.objects.all()
        
        # Regular users can only see their own service requests
        try:
            customer = Customer.objects.get(user=user)
            return ServiceRequest.objects.filter(customer=customer)
        except Customer.DoesNotExist:
            return ServiceRequest.objects.none()
    
    def perform_create(self, serializer):
        """
        Set the customer when creating a service request.
        """
        try:
            customer = Customer.objects.get(user=self.request.user)
            serializer.save(customer=customer)
        except Customer.DoesNotExist:
            raise ValidationError("Customer profile not found.")
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Return statistics about service requests.
        """
        if not (hasattr(request.user, 'role') and request.user.role == 'support_staff'):
            return Response(
                {"detail": "You don't have permission to access this data."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get basic statistics
            total = ServiceRequest.objects.count()
            pending = ServiceRequest.objects.filter(status='Pending').count()
            in_progress = ServiceRequest.objects.filter(status='In Progress').count()
            resolved = ServiceRequest.objects.filter(status='Resolved').count()
            
            # Get statistics by service type
            service_type_stats = ServiceRequest.objects.values('service_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Get statistics by priority
            priority_stats = ServiceRequest.objects.values('priority').annotate(
                count=Count('id')
            ).order_by('priority')
            
            # Calculate average resolution time for resolved requests
            resolved_requests = ServiceRequest.objects.filter(
                status='Resolved', 
                resolved_at__isnull=False
            )
            
            avg_resolution_days = None
            if resolved_requests.exists():
                resolution_times = []
                for req in resolved_requests:
                    if req.resolved_at and req.created_at:
                        delta = req.resolved_at - req.created_at
                        resolution_times.append(delta.total_seconds() / (60 * 60 * 24))  # Convert to days
                
                if resolution_times:
                    avg_resolution_days = sum(resolution_times) / len(resolution_times)
            
            data = {
                'total': total,
                'pending': pending,
                'in_progress': in_progress,
                'resolved': resolved,
                'by_service_type': list(service_type_stats),
                'by_priority': list(priority_stats),
                'avg_resolution_days': avg_resolution_days
            }
            
            serializer = ServiceRequestStatisticsSerializer(data)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error generating statistics: {str(e)}")
            return Response(
                {"error": "An error occurred while generating statistics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Traditional views for web interface
@login_required
def dashboard(request):
    """Display customer dashboard with paginated and filtered service requests."""
    # If user is a support staff, redirect to support dashboard
    if hasattr(request.user, 'role') and request.user.role == 'support_staff':
        return redirect('support_dashboard')
    
    try:
        # Get or create customer profile
        customer, created = Customer.objects.get_or_create(user=request.user)
        
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        service_type_filter = request.GET.get('service_type', '')
        
        # Build query
        requests_query = ServiceRequest.objects.filter(customer=customer)
        
        if status_filter:
            requests_query = requests_query.filter(status=status_filter)
        
        if service_type_filter:
            requests_query = requests_query.filter(service_type=service_type_filter)
        
        # Order by created_at (newest first)
        requests_query = requests_query.order_by('-created_at')
        
        # Paginate results
        paginator = Paginator(requests_query, 10)  # 10 requests per page
        page = request.GET.get('page')
        
        try:
            requests = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            requests = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page
            requests = paginator.page(paginator.num_pages)
        
        # Get unique status values and service types for filtering
        status_choices = ServiceRequest.STATUS_CHOICES
        service_type_choices = ServiceRequest.SERVICE_TYPES
        
        # Add user-specific request ID (starting from 1)
        for index, req in enumerate(requests, 1):
            req.user_request_id = index
            
    except Exception as e:
        logger.error(f"Error in dashboard view: {str(e)}")
        messages.error(request, "An error occurred while loading your dashboard.")
        requests = []
        status_choices = []
        service_type_choices = []
    
    context = {
        'requests': requests,
        'status_filter': status_filter,
        'service_type_filter': service_type_filter,
        'status_choices': status_choices,
        'service_type_choices': service_type_choices,
    }
    
    return render(request, 'dashboard.html', context)

# Submit a Service Request
@login_required
def submit_request(request):
    """Handle service request submission with validation."""
    # If user is a support staff, redirect to support dashboard
    if hasattr(request.user, 'role') and request.user.role == 'support_staff':
        return redirect('support_dashboard')
    
    try:
        # Get or create customer profile
        customer, created = Customer.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            form = ServiceRequestForm(request.POST, request.FILES)
            if form.is_valid():
                service_request = form.save(commit=False)
                service_request.customer = customer
                service_request.save()
                
                messages.success(request, "Service request submitted successfully!")
                return redirect('dashboard')
        else:
            form = ServiceRequestForm()

    except Exception as e:
        logger.error(f"Error in submit_request view: {str(e)}")
        messages.error(request, "An error occurred while processing your request.")
        form = ServiceRequestForm()

    return render(request, 'submit_request.html', {'form': form})

# View Service Request Details
@login_required
def request_detail(request, request_id):
    """Display service request details with access control."""
    try:
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Access control: ensure the user can only view their own requests
        if not (hasattr(request.user, 'role') and request.user.role == 'support_staff'):
            try:
                customer = Customer.objects.get(user=request.user)
                if service_request.customer != customer:
                    messages.error(request, "You don't have permission to view this request.")
                    return redirect('dashboard')
                
                # Add user-specific request ID
                user_requests = ServiceRequest.objects.filter(customer=customer).order_by('-created_at')
                
                for index, req in enumerate(user_requests, 1):
                    if req.id == service_request.id:
                        service_request.user_request_id = index
                        break
            except Customer.DoesNotExist:
                messages.error(request, "You don't have permission to view this request.")
                return redirect('dashboard')
    
    except Exception as e:
        logger.error(f"Error in request_detail view: {str(e)}")
        messages.error(request, "An error occurred while retrieving the request details.")
        return redirect('dashboard')

    return render(request, 'request_detail.html', {'service_request': service_request})

# Support Staff Dashboard
@method_decorator(login_required, name='dispatch')
class SupportDashboardView(ListView):
    """Class-based view for support staff dashboard with advanced filtering, sorting, and bulk actions."""
    model = ServiceRequest
    template_name = 'support_dashboard.html'
    context_object_name = 'service_requests'
    paginate_by = 15
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is a support staff
        if not (hasattr(request.user, 'role') and request.user.role == 'support_staff'):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter and sort service requests based on query parameters."""
        queryset = ServiceRequest.objects.all()
        
        # Apply filters
        status_filter = self.request.GET.get('status', '')
        priority_filter = self.request.GET.get('priority', '')
        service_type_filter = self.request.GET.get('service_type', '')
        search_query = self.request.GET.get('q', '')
        assigned_filter = self.request.GET.get('assigned', '')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
            
        if service_type_filter:
            queryset = queryset.filter(service_type=service_type_filter)
        
        if assigned_filter:
            if assigned_filter == 'me':
                # Get the support representative profile for the current user
                try:
                    support_rep = SupportRepresentative.objects.get(user=self.request.user)
                    queryset = queryset.filter(assigned_to=support_rep)
                except SupportRepresentative.DoesNotExist:
                    pass
            elif assigned_filter == 'unassigned':
                queryset = queryset.filter(assigned_to__isnull=True)
            
        if search_query:
            queryset = queryset.filter(
                Q(customer__user__username__icontains=search_query) |
                Q(customer__user__email__icontains=search_query) |
                Q(customer__user__first_name__icontains=search_query) |
                Q(customer__user__last_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Apply sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        valid_sort_fields = ['created_at', '-created_at', 'priority', '-priority', 'status', '-status']
        
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')
            
        return queryset
    
    def post(self, request, *args, **kwargs):
        """Handle bulk actions on service requests."""
        action = request.POST.get('action')
        selected_requests = request.POST.getlist('selected_requests')
        
        if not selected_requests:
            messages.warning(request, "No requests were selected.")
            return redirect('support_dashboard')
        
        if action == 'update_status':
            new_status = request.POST.get('new_status')
            if new_status:
                count = 0
                for req_id in selected_requests:
                    try:
                        req = ServiceRequest.objects.get(id=req_id)
                        req.status = new_status
                        req.save()
                        count += 1
                    except ServiceRequest.DoesNotExist:
                        continue
                
                messages.success(request, f"Updated status of {count} service requests to {new_status}.")
        
        elif action == 'assign':
            rep_id = request.POST.get('support_rep')
            try:
                if rep_id:
                    rep = SupportRepresentative.objects.get(id=rep_id)
                    count = 0
                    for req_id in selected_requests:
                        try:
                            req = ServiceRequest.objects.get(id=req_id)
                            req.assigned_to = rep
                            req.save()
                            count += 1
                        except ServiceRequest.DoesNotExist:
                            continue
                    
                    messages.success(request, f"Assigned {count} service requests to {rep.get_full_name()}.")
                else:
                    # Unassign
                    count = 0
                    for req_id in selected_requests:
                        try:
                            req = ServiceRequest.objects.get(id=req_id)
                            req.assigned_to = None
                            req.save()
                            count += 1
                        except ServiceRequest.DoesNotExist:
                            continue
                    
                    messages.success(request, f"Unassigned {count} service requests.")
            except SupportRepresentative.DoesNotExist:
                messages.error(request, "Invalid support representative selected.")
        
        return redirect('support_dashboard')
    
    def get_context_data(self, **kwargs):
        """Add additional context for filtering and statistics."""
        context = super().get_context_data(**kwargs)
        
        # Add filter values to context
        context['status'] = self.request.GET.get('status', '')
        context['priority'] = self.request.GET.get('priority', '')
        context['service_type'] = self.request.GET.get('service_type', '')
        context['q'] = self.request.GET.get('q', '')
        context['sort'] = self.request.GET.get('sort', '-created_at')
        context['assigned'] = self.request.GET.get('assigned', '')
        
        # Add statistics
        context['total_requests'] = ServiceRequest.objects.count()
        context['pending_requests'] = ServiceRequest.objects.filter(status='Pending').count()
        context['in_progress_requests'] = ServiceRequest.objects.filter(status='In Progress').count()
        context['resolved_requests'] = ServiceRequest.objects.filter(status='Resolved').count()
        
        # Add request choices for filtering
        context['status_choices'] = ServiceRequest.STATUS_CHOICES
        context['priority_choices'] = ServiceRequest.PRIORITY_CHOICES
        context['service_type_choices'] = ServiceRequest.SERVICE_TYPES
        
        # Add support representatives for assignment
        context['support_reps'] = SupportRepresentative.objects.all()
        
        # Add current user's support rep profile if it exists
        try:
            context['current_support_rep'] = SupportRepresentative.objects.get(user=self.request.user)
        except SupportRepresentative.DoesNotExist:
            context['current_support_rep'] = None
        
        return context

# Simplified function-based view for support dashboard for backward compatibility
@login_required
def support_dashboard(request):
    """Function-based view that redirects to the class-based support dashboard view."""
    # Check if user is a support staff
    if not (hasattr(request.user, 'role') and request.user.role == 'support_staff'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # Use the class-based view
    view = SupportDashboardView.as_view()
    return view(request)

# Support Staff Request Detail View
@login_required
def support_request_detail(request, request_id):
    """Handle support staff view and update of service request details."""
    # Check if user is a support staff
    if not (hasattr(request.user, 'role') and request.user.role == 'support_staff'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    try:
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Add user-specific request ID
        user_requests = ServiceRequest.objects.filter(
            customer=service_request.customer
        ).order_by('-created_at')
        
        for index, req in enumerate(user_requests, 1):
            if req.id == service_request.id:
                service_request.user_request_id = index
                break
        
        if request.method == 'POST':
            form = ServiceRequestUpdateForm(request.POST, instance=service_request)
            if form.is_valid():
                updated_request = form.save(commit=False)
                
                # Handle notes - append new notes to existing ones
                new_notes = form.cleaned_data.get('notes')
                if new_notes:
                    timestamp = now().strftime('%Y-%m-%d %H:%M:%S')
                    if updated_request.notes:
                        updated_request.notes += f"\n\n{timestamp} - {request.user.username}:\n{new_notes}"
                    else:
                        updated_request.notes = f"{timestamp} - {request.user.username}:\n{new_notes}"
                
                # Track status changes
                if 'status' in form.changed_data:
                    old_status = service_request.status
                    new_status = updated_request.status
                    status_change_note = f"\n\n{timestamp} - {request.user.username}:\nStatus changed from {old_status} to {new_status}"
                    
                    if updated_request.notes:
                        updated_request.notes += status_change_note
                    else:
                        updated_request.notes = status_change_note
                
                updated_request.save()
                messages.success(request, "Service request updated successfully!")
                
                # Redirect to the same page to show the updated information
                return redirect('support_request_detail', request_id=request_id)
        else:
            form = ServiceRequestUpdateForm(instance=service_request)
        
        # Get all support representatives for assignment dropdown
        support_reps = SupportRepresentative.objects.all()
        
        # Get customer details
        customer = service_request.customer
        
        # Get request history (other requests from the same customer)
        customer_requests = ServiceRequest.objects.filter(
            customer=customer
        ).exclude(id=service_request.id).order_by('-created_at')[:5]
        
        context = {
            'service_request': service_request,
            'form': form,
            'support_reps': support_reps,
            'customer': customer,
            'customer_requests': customer_requests
        }
        
    except Exception as e:
        logger.error(f"Error in support_request_detail view: {str(e)}")
        messages.error(request, "An error occurred while processing the request.")
        return redirect('support_dashboard')
    
    return render(request, 'support_request_detail.html', context)

# Delete Service Request (only for support staff)
@login_required
@require_http_methods(["POST"])
def delete_request(request, request_id):
    """Handle deletion of service requests with proper authorization."""
    # Check if user is a support staff
    if not (hasattr(request.user, 'role') and request.user.role == 'support_staff'):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('dashboard')
    
    try:
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        service_request.delete()
        messages.success(request, "Service request deleted successfully!")
    except Exception as e:
        logger.error(f"Error deleting request {request_id}: {str(e)}")
        messages.error(request, "An error occurred while deleting the request.")
    
    return redirect('support_dashboard')