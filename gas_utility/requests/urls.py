from django.urls import path, include
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from .views import (
    dashboard, submit_request, request_detail,
    support_dashboard, support_request_detail, delete_request,
    ServiceRequestViewSet
)

# Create a router for our API ViewSets
router = DefaultRouter()
router.register(r'service-requests', ServiceRequestViewSet)

def home(request):
    return redirect('login')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Web interface URLs
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('submit-request/', submit_request, name='submit_request'),
    path('request/<int:request_id>/', request_detail, name='request_detail'),
    
    # Support staff URLs
    path('support/dashboard/', support_dashboard, name='support_dashboard'),
    path('support/request/<int:request_id>/', support_request_detail, name='support_request_detail'),
    path('support/request/<int:request_id>/delete/', delete_request, name='delete_request'),
]
