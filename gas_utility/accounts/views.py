from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import User, Customer, SupportRepresentative
from .serializers import (
    UserSerializer, CustomerSerializer, CustomerCreateSerializer,
    SupportRepresentativeSerializer, SupportRepresentativeCreateSerializer
)

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
        
        # Check if the object has a user field directly
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For other cases, deny access
        return False

# API ViewSets
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Limit users based on the requesting user's role.
        """
        user = self.request.user
        
        # Support staff can see all users
        if user.role == 'support_staff':
            return User.objects.all()
        
        # Regular users can only see themselves
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the authenticated user's details.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class CustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows customers to be viewed or edited.
    """
    queryset = Customer.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrSupportStaff]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CustomerCreateSerializer
        return CustomerSerializer
    
    def get_queryset(self):
        """
        Limit customers based on the requesting user's role.
        """
        user = self.request.user
        
        # Support staff can see all customers
        if user.role == 'support_staff':
            return Customer.objects.all()
        
        # Regular users can only see their own customer profile
        return Customer.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the authenticated user's customer profile.
        """
        try:
            customer = Customer.objects.get(user=request.user)
            serializer = self.get_serializer(customer)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {"detail": "Customer profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class SupportRepresentativeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows support representatives to be viewed or edited.
    """
    queryset = SupportRepresentative.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SupportRepresentativeCreateSerializer
        return SupportRepresentativeSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            # Only admin users can create, update, or delete support representatives
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Limit support representatives based on the requesting user's role.
        """
        user = self.request.user
        
        # Support staff can see all support representatives
        if user.role == 'support_staff':
            return SupportRepresentative.objects.all()
        
        # Regular users can only see their own support profile if they have one
        return SupportRepresentative.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the authenticated user's support representative profile.
        """
        if request.user.role != 'support_staff':
            return Response(
                {"detail": "You do not have a support representative profile."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            support_rep = SupportRepresentative.objects.get(user=request.user)
            serializer = self.get_serializer(support_rep)
            return Response(serializer.data)
        except SupportRepresentative.DoesNotExist:
            return Response(
                {"detail": "Support representative profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

# Traditional views for authentication
@require_http_methods(["GET", "POST"])
def register(request):
    """Handle user registration with customer profile creation."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        from .forms import CustomerRegistrationForm
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Form now handles customer creation
            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
    else:
        from .forms import CustomerRegistrationForm
        form = CustomerRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

@require_http_methods(["GET", "POST"])
def user_login(request):
    """Handle user login with role-based redirection."""
    if request.user.is_authenticated:
        if hasattr(request.user, 'role') and request.user.role == 'support_staff':
            return redirect('support_dashboard')
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, "Please provide both username and password.")
            return render(request, 'login.html')
            
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Get the next URL or use default based on role
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
                
            # Redirect based on user role
            if hasattr(user, 'role') and user.role == 'support_staff':
                return redirect('support_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login.html')

@login_required
def user_logout(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')
