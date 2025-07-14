# FinSplit - Advanced Django Expense Splitting Application

![FinSplit Logo](https://img.shields.io/badge/FinSplit-Expense%20Splitting-blue?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-5.2.4-green?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![DRF](https://img.shields.io/badge/DRF-REST%20API-orange?style=flat-square)

**FinSplit** is a comprehensive Django-powered web application that makes expense splitting effortless. Built with advanced Django features including ORM, REST API, caching, threading, and clean UI design.

## 🚀 Live Demo

**Application URL:** [https://8000-iz9ylnzosrbbowc23yys9-42eab0c3.manus.computer](https://8000-iz9ylnzosrbbowc23yys9-42eab0c3.manus.computer)

### Test Credentials
- **Username:** `alice` | **Password:** `password123`
- **Username:** `bob` | **Password:** `password123`
- **Username:** `charlie` | **Password:** `password123`
- **Admin:** `admin` | **Password:** `admin123`

## ✨ Features

### Core Functionality
- 🏊‍♂️ **Pool Management** - Create and manage expense groups
- 💰 **Expense Tracking** - Log and categorize shared expenses
- 🔄 **Smart Splitting** - Equal, percentage, or manual splits
- 💳 **UPI Integration** - Seamless payments with UPI IDs
- ⚖️ **Balance Calculation** - Automatic debt optimization
- 📱 **Responsive Design** - Works on all devices

### Advanced Features
- 🔐 **Authentication System** - Secure user management
- 🌐 **REST API** - Complete CRUD operations
- ⚡ **Caching** - Performance optimization
- 📧 **Email Notifications** - Async email sending
- 🧵 **Threading** - Background task processing
- 🛡️ **Security** - CSRF protection and validation
- 📊 **Admin Interface** - Comprehensive management panel

## 🏗️ Architecture & Django Concepts Applied

### 1. Django Fundamentals
- **Project Structure** - Proper Django project organization
- **Apps** - Modular core app design
- **Views** - HttpResponse, render, redirect, JsonResponse
- **URLs** - Clean URL configuration and routing
- **Settings** - Comprehensive configuration management

### 2. Models & ORM
```python
# Advanced model relationships and methods
class Pool(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, through='Member')
    
    def get_balances(self):
        # Complex balance calculation logic
        pass
```

### 3. Templates & UI
- **Template Inheritance** - `base.html` with extends/includes
- **Context Processing** - Dynamic data rendering
- **Static Files** - CSS/JS organization
- **Responsive Design** - Bootstrap integration

### 4. Authentication & Admin
- **Django Auth** - Built-in authentication system
- **Custom Admin** - Enhanced admin interface
- **Permissions** - User access control
- **Sessions** - Secure session management

### 5. REST API (Django REST Framework)
- **ViewSets** - ModelViewSet for CRUD operations
- **Serializers** - Data validation and transformation
- **Authentication** - Session and Basic Auth
- **Filtering** - Search, ordering, pagination
- **Throttling** - Rate limiting implementation

### 6. Advanced Features
- **Caching** - Django cache framework
- **Email** - SMTP configuration and async sending
- **Threading** - Background task processing
- **Signals** - Automatic profile creation
- **Custom Utilities** - UPI validation, cache management

## 📁 Project Structure

```
FinSplit/
├── core/                          # Main application
│   ├── models.py                  # Data models
│   ├── views.py                   # View logic
│   ├── api_views.py              # REST API views
│   ├── serializers.py            # DRF serializers
│   ├── forms.py                  # Django forms
│   ├── admin.py                  # Admin configuration
│   ├── urls.py                   # URL routing
│   ├── api_urls.py              # API routing
│   ├── signals.py               # Django signals
│   ├── cache_utils.py           # Caching utilities
│   ├── email_utils.py           # Email functionality
│   ├── upi_utils.py             # UPI validation
│   ├── templates/               # HTML templates
│   │   ├── core/               # Core templates
│   │   ├── registration/       # Auth templates
│   │   └── emails/            # Email templates
│   └── static/                 # Static files
│       ├── css/               # Stylesheets
│       └── js/                # JavaScript
├── FinSplit/                    # Project settings
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Main URL config
│   └── wsgi.py                 # WSGI config
├── manage.py                   # Django management
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
└── TESTING_RESULTS.md         # Test results
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- Django 5.2.4
- SQLite (default) or PostgreSQL

### Quick Start

1. **Clone the Repository**
```bash
git clone <repository-url>
cd FinSplit
```

2. **Install Dependencies**
```bash
pip install django djangorestframework django-cors-headers django-filter
```

3. **Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Create Superuser**
```bash
python manage.py createsuperuser
```

5. **Load Test Data** (Optional)
```bash
python manage.py shell
# Run the test data creation script from TESTING_RESULTS.md
```

6. **Run Development Server**
```bash
python manage.py runserver 0.0.0.0:8000
```

7. **Access Application**
- **Web App:** http://localhost:8000
- **Admin:** http://localhost:8000/admin
- **API:** http://localhost:8000/api

## 📚 API Documentation

### Authentication
All API endpoints require authentication. Use session authentication or basic auth.

### Endpoints

#### Pools
- `GET /api/pools/` - List all pools
- `POST /api/pools/` - Create new pool
- `GET /api/pools/{id}/` - Get pool details
- `PUT /api/pools/{id}/` - Update pool
- `DELETE /api/pools/{id}/` - Delete pool

#### Expenses
- `GET /api/expenses/` - List expenses
- `POST /api/expenses/` - Create expense
- `GET /api/expenses/{id}/` - Get expense details
- `PUT /api/expenses/{id}/` - Update expense
- `DELETE /api/expenses/{id}/` - Delete expense

#### Members
- `GET /api/members/` - List members
- `POST /api/members/` - Add member
- `DELETE /api/members/{id}/` - Remove member

#### Transactions
- `GET /api/transactions/` - List transactions
- `POST /api/transactions/` - Create transaction

### API Features
- **Filtering** - `?search=term&ordering=field`
- **Pagination** - Automatic pagination with 20 items per page
- **Throttling** - Rate limiting (1000/hour for authenticated users)

## 🎯 Usage Guide

### Creating a Pool
1. Navigate to Dashboard
2. Click "New Pool"
3. Enter pool name and description
4. Choose default split method
5. Add members using UPI IDs or email

### Adding Expenses
1. Go to pool details
2. Click "Add Expense"
3. Enter expense details
4. Choose split method (equal/percentage/manual)
5. Assign splits to members

### Settling Up
1. View balances in pool details
2. Click on settlement suggestions
3. Use UPI payment links for quick payments
4. Mark transactions as completed

### Managing Members
1. Access pool settings
2. Add members by UPI ID or email
3. Set admin permissions
4. Remove inactive members

## 🔧 Configuration

### Environment Variables
```python
# settings.py key configurations
DEBUG = True  # Set to False in production
ALLOWED_HOSTS = ['*']  # Configure for production
SECRET_KEY = 'your-secret-key'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

### Caching Configuration
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,
    }
}
```

## 🧪 Testing

### Running Tests
```bash
# Run Django tests
python manage.py test

# Test API endpoints
python test_api.py

# Manual testing checklist in TESTING_RESULTS.md
```

### Test Coverage
- ✅ Authentication system
- ✅ Pool management
- ✅ Expense tracking
- ✅ Balance calculations
- ✅ API functionality
- ✅ UI/UX components

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Setup production database
- [ ] Configure static files serving
- [ ] Setup email backend
- [ ] Enable HTTPS
- [ ] Configure caching (Redis recommended)

### Docker Deployment (Optional)
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Follow Django best practices
4. Add tests for new features
5. Update documentation
6. Submit pull request

### Code Style
- Follow PEP 8
- Use Django conventions
- Add docstrings to functions
- Keep functions focused and small

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django Framework for the robust foundation
- Django REST Framework for API capabilities
- Bootstrap for responsive UI components
- The Django community for excellent documentation

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the testing results

---

**Built with ❤️ using Django and advanced Python concepts**

