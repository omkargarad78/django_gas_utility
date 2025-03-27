from django.core.management.base import BaseCommand
from accounts.models import User
from requests.models import SupportRepresentative

class Command(BaseCommand):
    help = 'Create a new support representative user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the support rep')
        parser.add_argument('email', type=str, help='Email for the support rep')
        parser.add_argument('password', type=str, help='Password for the support rep')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        email = kwargs['email']
        password = kwargs['password']
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User with username {username} already exists.'))
            return
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.role = 'support_staff'
        user.is_staff = True  # Give access to admin site
        user.save()
        
        # Create support representative
        SupportRepresentative.objects.create(user=user)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created support representative: {username}')) 