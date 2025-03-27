from django import forms
from accounts.models import User, Customer
from .models import ServiceRequest
from django.core.validators import RegexValidator

# User Registration Form
class CustomerRegistrationForm(forms.ModelForm):
    """Form for customer registration with validation."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (optional)'})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'placeholder': 'Address (optional)',
            'rows': 3
        }),
        required=False
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }
        
    def clean(self):
        """Validate that passwords match and username/email are unique."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        # Check if username already exists
        username = cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            self.add_error('username', "This username is already taken.")
            
        # Check if email already exists
        email = cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', "This email is already registered.")
            
        return cleaned_data
    
    def save(self, commit=True):
        """Save user and create customer profile."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'customer'
        
        if commit:
            user.save()
            # Create customer profile with additional fields
            Customer.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number'),
                address=self.cleaned_data.get('address')
            )
        
        return user

# Service Request Form
class ServiceRequestForm(forms.ModelForm):
    """Form for submitting service requests."""
    class Meta:
        model = ServiceRequest
        fields = ['service_type', 'priority', 'description', 'attached_file']
        widgets = {
            'service_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Please describe your issue in detail'
            }),
            'attached_file': forms.FileInput(attrs={'class': 'form-control'})
        }
        help_texts = {
            'service_type': 'Select the type of service you need',
            'priority': 'Select the priority of your request',
            'description': 'Provide as much detail as possible about your issue',
            'attached_file': 'Attach any relevant documents or images (optional)'
        }
    
    def clean_attached_file(self):
        """Validate file size and type."""
        attached_file = self.cleaned_data.get('attached_file')
        if attached_file:
            # Check file size (5MB limit)
            if attached_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 5MB")
            
            # Check file extension
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            file_ext = attached_file.name.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                raise forms.ValidationError(
                    f"Only {', '.join(allowed_extensions)} files are allowed"
                )
        
        return attached_file

# Support Staff Update Form
class ServiceRequestUpdateForm(forms.ModelForm):
    """Form for support staff to update service requests."""
    class Meta:
        model = ServiceRequest
        fields = ['status', 'priority', 'notes', 'assigned_to']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add notes about this request'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with custom notes field behavior."""
        super().__init__(*args, **kwargs)
        
        # Make assigned_to field optional
        self.fields['assigned_to'].required = False
        
        # If the instance has existing notes, show them in the placeholder
        if self.instance and self.instance.pk and self.instance.notes:
            self.fields['notes'].widget.attrs['placeholder'] = 'Add to existing notes'
