from rest_framework import serializers
from .models import User, Customer, SupportRepresentative


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id']


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for the Customer model with nested User data."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Customer
        fields = ['id', 'user', 'phone_number', 'address', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new Customer with User."""
    
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Customer
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 
                  'phone_number', 'address']
    
    def create(self, validated_data):
        """Create a new user and customer profile."""
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'role': 'customer'
        }
        
        # Add optional fields if present
        if 'first_name' in validated_data:
            user_data['first_name'] = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            user_data['last_name'] = validated_data.pop('last_name')
        
        # Create user
        user = User.objects.create_user(**user_data)
        
        # Create customer profile
        customer = Customer.objects.create(user=user, **validated_data)
        return customer


class SupportRepresentativeSerializer(serializers.ModelSerializer):
    """Serializer for the SupportRepresentative model with nested User data."""
    
    user = UserSerializer(read_only=True)
    active_requests_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportRepresentative
        fields = ['id', 'user', 'department', 'employee_id', 'active_requests_count', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_active_requests_count(self, obj):
        """Get the count of active requests assigned to this representative."""
        return obj.get_active_requests_count()


class SupportRepresentativeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new SupportRepresentative with User."""
    
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = SupportRepresentative
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 
                  'department', 'employee_id']
    
    def create(self, validated_data):
        """Create a new user and support representative profile."""
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'role': 'support_staff'
        }
        
        # Add optional fields if present
        if 'first_name' in validated_data:
            user_data['first_name'] = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            user_data['last_name'] = validated_data.pop('last_name')
        
        # Create user
        user = User.objects.create_user(**user_data)
        
        # Create support representative profile
        support_rep = SupportRepresentative.objects.create(user=user, **validated_data)
        return support_rep
