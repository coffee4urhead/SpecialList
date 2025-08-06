# 💼 SpecialList

**SpecialList** is a web platform built to help **service seekers** and **service providers** showcase their skills,
establish a presence on the job market world, and find internship opportunities as well as get something done. It
combines community features, personal profile pages, and resource sharing into one centralized hub focused on personal
growth and career discovery.

---

## 🌟 Purpose

The main goal of SpecialList is to **accelerate the career journey** of personal and large scale businesses by:

- Enabling users to **build a profile** that reflects their skills and links
- Creating a **space for collaboration**, community engagement, and visibility
- Helping them **connect with CEOs, recruiters, and other service providers/seekers**

---

## 🧩 Features

### 🔐 Authentication

- User registration, login, and logout system
- The first building block for your opportunities in SpecialList

### 👤 SpecialList Profiles

- Public profiles including:
    - Username, bio, and location
    - General information about the account such as the followers and the following
    - Portfolio certificates and past organization positions
    - Flagged services
    - Account reviews

### 👨‍💼 Service Providers Profiles

- Public profiles including:
    - Username, bio, and location
    - General information about the account such as the followers and the following
    - Portfolio certificates and past organization positions
    - Flagged services
    - Account reviews

### 🗂️ Home Page

-Displays our Gold partners that are ready for internships and sponsorships

- Displays website reviews and offers business-grade plans that are the following
-
    1. Basic Plan — “Starter” price: 9.99$/month

1. Offer 3 active services
2. Appear in standard search results
3. Access to basic analytics

-
    2. Professional Plan — “Growth” price: 29.99$/month

1. Up to 10 active service listings
2. Priority placement in search results
3. Unlimited bookings
4. Full analytics dashboard

-
    3. Business Plan — “Elite” price: 79.99$/month

1. Unlimited listings
2. Featured badge and homepage spotlight
3. Early access to new features
4. Become eligible for gold partner

## 🌟 About SpecialList

SpecialList is a global marketplace connecting skilled service providers with clients seeking quality services. Our
platform fosters meaningful professional relationships through transparency, trust, and personalized matching.

### 🔍 For Service Seekers

- **Discover Professionals**: Search by service category, skills, location, or ratings
- **Verified Providers**: View complete profiles with portfolios and client reviews
- **Transparent Process**: See pricing, availability, and service details upfront
- **Secure Booking**: Schedule and pay for services with confidence

### 🛠 For Service Providers

- **Showcase Your Skills**: Create detailed service listings with photos/videos
- **Manage Availability**: Set your own schedule and service parameters
- **Build Reputation**: Earn reviews and ratings from satisfied clients
- **Get Discovered**: Appear in targeted searches based on your specialties

### ✨ Platform Features

- **Secure Messaging**: Built-in communication system
- **Review System**: Rate and review completed services
- **Availability Calendar**: Real-time booking management
- **Payment Protection**: Secure escrow system for transactions

### 🛠 Admin Panel (admins only)

- **Blacklist Management** – Manage reported content like comments, services, user and reviews
- **Bookings Management** – Oversee total bookings made and visualised on Plotly graphs
- **Users and Organization Management** – Track user registration, organizations and pending certificates to be verified
- **Services Management** – Track total services, availabilities and comments
- **Chats Management** - Admins can oversee conversations between users and see the messages
- **Reviews Management** - Discover user/website reviews form users
- **Subscriptions Management** - Manage the subscriptions across the SpecialList platform users

### 📄 Additional Pages

- **Home** – Introduction to the platform and its purpose
- **Verification application** - the start of verified personal certificates
- **Contact Us** – Users can reach out to the support team via email
- **Privacy Policy** – Explains how user data is collected and handled
- **Customer Support** – chat directly with our service customer 24/7 support
- **Careers** - Explore SpecialList opportunities

---
### Follow these steps to get the SpecialList application up and running on your local machine for development and testing purposes.
---

### **Client Application Setup**

1. **Clone the Repository**:  
   You can clone the repository using the following command or download it as a ZIP file and extract it on your
   computer.

   ```bash
   git clone https://github.com/coffee4urhead/SpecialList.git
   ```

2. **Navigate to the Project Directory**:  
   Use the terminal to navigate to the project directory.

   ```bash
   cd JobJab
   ```

4. **Install Dependencies**:  
   Install all the necessary dependencies by running the following command in your terminal:

   ```bash
   pip install -r requirements.txt
   ```
5. **Manage settings.py**:  
   List all the apps in the JobJab application by typing in under the INSTALLED_APPS setting - "JobJab.services",
   "JobJab.booking",
   "JobJab.reviews",
   'JobJab.dashboard',
   "JobJab.subscriptions",
   'JobJab.chats',
   You will also need to list the static dir settings STATIC_URL = '/static/'
   MEDIA_URL = '/media/'
   MEDIA_ROOT = BASE_DIR / 'media'
   STATICFILES_DIRS = [
   os.path.join(BASE_DIR, 'static'),
   ]

STATICFILES_FINDERS = [
'django.contrib.staticfiles.finders.FileSystemFinder',
'django.contrib.staticfiles.finders.AppDirectoriesFinder',
'compressor.finders.CompressorFinder',
]
STATIC_ROOT = os.path.join(BASE_DIR, 'compiledsass')
The project uses Sass Django Compressor that you can configure with these settings: COMPRESS_PRECOMPILERS = (
('text/x-scss', 'django_libsass.SassCompiler'),
)
COMPRESS_ENABLED = True
COMPRESS_ROOT = STATIC_ROOT
You will also have to include these dependencies in the INSTALLED_APPS setting: 'compressor',
'pdf2image',
'django_cron',
'channels',
'django.contrib.postgres',

Use POSTGRES for the DB as the project uses psycopg2 as a PostgreSQL database adapter for Python. It allows Python
applications to interact with PostgreSQL databases efficiently and securely.
Under the MIDDLEWARE settings list the following: 'django.contrib.messages.middleware.MessageMiddleware',
'django.middleware.clickjacking.XFrameOptionsMiddleware', as we are using asgi application in the chats app
Also add CHANNEL_LAYERS setting: CHANNEL_LAYERS = {
"default": {
"BACKEND": "channels.layers.InMemoryChannelLayer"
},
}
FOR AUTH_PASSWORD_VALIDATORS I USE THE DEFAULT ONES WITH A SMALL CHANGE - {
'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
'OPTIONS': {'min_length': 10},
},
Here are the redirect url and login url as well as the base AUTH user model settings i use: AUTH_USER_MODEL = '
core.CustomUser'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = '/user/login/'

i set sessions to age SESSION_COOKIE_AGE = 1209600

6. **Prepare Django Stripe**:  
   To integrate Stripe payments into your Django app, follow these steps to create a Stripe account and obtain the
   required credentials (Publishable Key and Secret Key).

## 🚀 Getting Started

### Stripe Account Setup

1. **Sign up at [stripe.com](https://stripe.com/)**
2. **Get API Keys**:
    - Test Mode → `pk_test_...` (frontend) and `sk_test_...` (backend)
    - Live Mode → `pk_live_...` and `sk_live_...` (after verification)
3. **Add to Django Settings**:
   ```python
   # settings.py
   STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')  # Frontend
   STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')  # Backend
   STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')  # Webhooks
4. **Setup Webhooks**:
   For this to work you need to have installed stripe CLI - visit this website to learn more about the installation and
   stripe account login - 'https://docs.stripe.com/stripe-cli#install'

```bash
   stripe listen --forward-to localhost:8000/subscriptions/stripe-webhook/

stripe listen --forward-to localhost:8000/booking/stripe-webhook/ 

   ```

7. **Run the Client Part**:  
   Start the Python Django Framework development server with this command:

   ```bash
   python manage.py runserver
   ```

8. **Open the Project**:  
   Access the application by opening the following URL in a web browser:  
   For other device connections discover your IP address by typing in   ```bash ipconfig ``` then start the server with
   ```bash python manage.py runserver 0.0.0.0:8000 ``` - this will forward the django website through your IP (Be
   careful because this exposes your actual IP). Then you will access your website at `http://<your-ip-address>:8000/`
   `http://127.0.0.0:8000/`

---


🛠️ **Technologies and Tools**

<p align="left">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/redis/redis-original.svg" width="40" height="40" />
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/plotly/plotly-original-wordmark.svg" width="40" height="40"/>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postgresql/postgresql-original-wordmark.svg" width="40" height="40" />
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/sass/sass-original.svg" width="40" height="40" />
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/socketio/socketio-original-wordmark.svg" width="40" height="40"/>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/pandas/pandas-original-wordmark.svg" width="40" height="40"/>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/ngrok/ngrok-original.svg" width="40" height="40"/>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/django/django-plain.svg" width="40" height="40"/>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/djangorest/djangorest-line.svg" width="40" height="40"/>
</p>

---

### 📚 Libraries

- **pdf2image==1.17.0** – Converts PDF documents to images (supports PNG/JPEG formats)
- **pandas==2.3.1** – Data analysis and manipulation tool for structured data operations
- **numpy==2.3.2** – Fundamental package for numerical computing with array support
- **ngrok==1.4.0** – Secure tunneling service for exposing local servers to the internet
- **pillow==11.2.1** – Python Imaging Library for image processing capabilities
- **djangorestframework==3.16.0** – Toolkit for building Web APIs with Django
- **channels==4.2.2** – Extends Django to handle WebSockets and async protocols
- **channels_redis==4.2.1** – Redis channel layer backend for Django Channels
- **django-stripe-payments==2.0.0** – Django integration for Stripe payment processing
- **django-compressor==4.1** – Combines and minifies static files (CSS/JS)
- **cryptography==45.0.5** – Provides cryptographic recipes and primitives
- **daphne==4.2.1** – HTTP/WebSocket protocol server for Django Channels
- **Django==5.0.1** – High-level Python web framework (core dependency)
- **plotly==6.2.0** – Interactive graphing library for data visualization
- **psycopg2==2.9.10** – PostgreSQL database adapter for Python
- **python-dotenv==1.1.1** – Reads key-value pairs from .env files
- **stripe==12.3.0** – Official Stripe API library for payment processing

🛠️ **Key Integrations**:

- **Stripe** for payment processing
- **PostgreSQL** via psycopg2 for database operations
- **Redis** for Channels backend
- **Plotly** for admin dashboard visualizations