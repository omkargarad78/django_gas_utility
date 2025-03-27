from rest_framework import serializers
from .models import ServiceRequest
from accounts.models import Customer, SupportRepresentative
from accounts.serializers import CustomerSerializer, SupportRepresentativeSerializer


class ServiceRequestSerializer(serializers.ModelSerializer):
    """Serializer for the ServiceRequest model."""
    
    customer_details = CustomerSerializer(source='customer', read_only=True)
    assigned_to_details = SupportRepresentativeSerializer(source='assigned_to', read_only=True)
    days_open = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'customer', 'customer_details', 'service_type', 'description',
            'attached_file', 'status', 'priority', 'created_at', 'updated_at',
            'resolved_at', 'notes', 'assigned_to', 'assigned_to_details', 'days_open'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'resolved_at']
    
    def get_days_open(self, obj):
        """Get the number of days this request has been open."""
        return obj.get_days_open()


class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new ServiceRequest."""
    
    class Meta:
        model = ServiceRequest
        fields = ['customer', 'service_type', 'description', 'attached_file', 'priority']
    
    def validate_customer(self, value):
        """Validate that the customer exists."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # If user is a customer, they can only create requests for themselves
            if request.user.role == 'customer':
                try:
                    customer = Customer.objects.get(user=request.user)
                    if value.id != customer.id:
                        raise serializers.ValidationError(
                            "You can only create service requests for yourself."
                        )
                except Customer.DoesNotExist:
                    raise serializers.ValidationError("Customer profile not found.")
        return value


class ServiceRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a ServiceRequest."""
    
    class Meta:
        model = ServiceRequest
        fields = ['status', 'priority', 'notes', 'assigned_to']
    
    def validate(self, data):
        """Validate the update based on user role."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Only support staff can update certain fields
            if request.user.role != 'support_staff':
                restricted_fields = ['status', 'assigned_to']
                for field in restricted_fields:
                    if field in data:
                        raise serializers.ValidationError(
                            f"Only support staff can update the {field} field."
                        )
        return data


class ServiceRequestStatisticsSerializer(serializers.Serializer):
    """Serializer for service request statistics."""
    
    total = serializers.IntegerField()
    pending = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    resolved = serializers.IntegerField()
    avg_resolution_days = serializers.FloatField(allow_null=True)
    by_service_type = serializers.ListField(child=serializers.DictField())
    by_priority = serializers.ListField(child=serializers.DictField())
