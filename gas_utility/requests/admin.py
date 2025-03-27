from django.contrib import admin
from .models import Customer, ServiceRequest, SupportRepresentative

class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'customer', 'status', 'created_at', 'resolved_at')
    list_filter = ('status', 'service_type')
    search_fields = ('service_type', 'description', 'customer__user__username')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If the user is a support staff (not admin), only show their assigned requests
        if request.user.is_superuser:
            return qs
        return qs.filter(status__in=['Pending', 'In Progress'])

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__username', 'user__email', 'phone_number')

class SupportRepresentativeAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__email')

admin.site.register(Customer, CustomerAdmin)
admin.site.register(ServiceRequest, ServiceRequestAdmin)
admin.site.register(SupportRepresentative, SupportRepresentativeAdmin)