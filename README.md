# Gas Utility Customer Service Application

A Django-based application to streamline customer service for gas utility companies. This application allows customers to submit service requests, track their status, and provides support representatives with tools to manage and respond to these requests efficiently.


## User Credentials

### Support Representative
- **Username**: support_admin
- **Password**: password123
- **Access**: Support dashboard, all customer requests, ability to update and delete requests

### Sample Customer
- **Username**: admin1
- **Password**: plokm?123

### Sample Customer
- **Username**: admin2
- **Password**: plokm?12

## Technical Details

### Application Structure
- **accounts**: Handles user authentication and management
  - Custom User model with role-based permissions
- **requests**: Manages service requests and support operations
  - Customer profiles
  - Support representative dashboard 

### Database Models
- **User**: Extended Django user model with role field (customer/support_staff)
- **Customer**: Profile for users with customer role
- **ServiceRequest**: Contains request details, status, timestamps, and file attachments
- **SupportRepresentative**: Profile for users with support_staff role


## Setup Instructions

1. Clone the repository
2. Create a virtual environment: `python -m venv env`
3. Activate the virtual environment:
   - Windows: `env\Scripts\activate`
   - macOS/Linux: `source env/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Apply migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`
7. Create a support representative:
   ```
   python manage.py create_support_rep <username> <email> <password>
   ```
8. Run the development server: `python manage.py runserver`
9. Access the application at http://127.0.0.1:8000/

## Usage Workflow

### Customer Flow
1. Register a new account or log in with existing credentials
2. Submit a new service request with details and optional attachments
3. Click on a request to view details and track status updates

### Support Representative Flow
1. Log in with support staff credentials
2. View all customer requests in the support dashboard
3. Filter requests by status as needed
4. Click on a request to view details
5. Update status and add notes to communicate with customers
6. Delete requests when necessary 

## Security Features
- Password hashing for secure authentication
- CSRF protection for form submissions
- Permission checks to ensure appropriate access
- Confirmation dialogs for destructive actions

