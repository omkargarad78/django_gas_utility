from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for our API ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'customers', views.CustomerViewSet)
router.register(r'support-representatives', views.SupportRepresentativeViewSet)

# URL patterns for the accounts app
urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Authentication views
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]
