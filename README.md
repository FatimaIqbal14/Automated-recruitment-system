# SOORTY Denimkind — AI-Powered Recruitment Portal

> A full-stack Django web application for end-to-end recruitment management, featuring AI-driven CV screening, automated interview scheduling, and email notifications.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [AI Screening System](#ai-screening-system)
- [User Roles](#user-roles)
- [Screenshots](#screenshots)
- [Database Models](#database-models)
- [Contributing](#contributing)

---

## Project Overview

SOORTY Denimkind Recruitment Portal is a complete hiring management system built for SOORTY Denimkind, a denim manufacturing company. The platform allows candidates to browse job openings, submit applications with their CV, and automatically receive interview invitations or rejection emails — all powered by Google Gemini AI.

Admins get a dedicated dashboard to post jobs, review applicants, preview CVs, and update application statuses, while candidates get a personal dashboard to track their applications.

---

## Features

### For Candidates
- Browse all open job positions with details
- Apply for jobs with a full application form (name, age, experience, skills, cover letter, CV upload)
- Guest application with inline account creation — no need to register first
- Personal dashboard showing profile info and all submitted applications with statuses
- Edit profile at any time (display name, age, gender, experience, skills, CV)
- LinkedIn-style skills autocomplete with tag-based input
- Password visibility toggle on all password fields
- Automatic email notification on application result

### For Admins
- Dedicated admin dashboard (separate from Django's built-in admin)
- Post new job openings with title, department, location, type, description, and requirements
- View all applicants per job with candidate details
- Full applicant detail page with CV preview (PDF rendered inline via PDF.js)
- Update application status (Pending / Reviewed / Accepted / Rejected)
- View registered users with their profiles and application counts
- Quick stats: total jobs, total users, total applications
- Link to raw Django admin for advanced data management

### AI Screening (Automated)
- Every application is automatically screened by Google Gemini AI
- AI reads both the application form AND the uploaded CV (text extracted from PDF)
- Candidates scoring ≥ 70% are accepted and sent an interview invitation email
- Candidates scoring < 70% are rejected and sent a polite rejection email
- Interview slots are auto-assigned: weekdays 9am–3pm, 1 hour each, no clashes
- AI match score and reasoning visible to admin in applicant detail view

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, Django 6.0 |
| Database | SQLite (development) |
| AI Screening | Google Gemini 2.5 Flash (`google-generativeai`) |
| CV Parsing | PyPDF2 |
| PDF Preview | PDF.js (via cdnjs) |
| Email | Django SMTP (Gmail / Mailtrap) |
| Frontend | HTML5, CSS3 (custom design system), Vanilla JavaScript |
| Fonts | Cormorant Garamond (serif headings), Segoe UI (body) |
| Static Files | Django staticfiles |
| Media Files | Django FileField with local media storage |

---

## Project Structure

```
LoginProject/
│
├── accounts/                   # Main Django app
│   ├── models.py               # Profile, Job, Application, Skill models
│   ├── views.py                # All views (public, auth, dashboard, admin)
│   ├── forms.py                # RegisterForm, JobApplicationForm, EditProfileForm
│   ├── urls.py                 # URL routing
│   ├── admin.py                # Django admin registration + customization
│   ├── ai_screening.py         # Gemini AI screening + email logic
│   └── migrations/             # Database migrations
│
├── config/                     # Django project config
│   ├── settings.py             # Settings (DB, email, static, AI keys)
│   ├── urls.py                 # Root URL config
│   ├── wsgi.py
│   └── asgi.py
│
├── templates/
│   └── accounts/
│       ├── base.html                   # Base layout with navbar & footer
│       ├── home.html                   # Landing page
│       ├── about.html                  # About page
│       ├── job_openings.html           # All jobs listing
│       ├── job_detail.html             # Single job detail
│       ├── apply_job.html              # Application form
│       ├── application_success.html    # Post-application confirmation
│       ├── register.html               # Registration form
│       ├── login.html                  # Login form
│       ├── dashboard.html              # Candidate dashboard
│       ├── edit_profile.html           # Edit profile page
│       ├── admin_dashboard.html        # Admin overview
│       ├── admin_job_applicants.html   # Applicants per job
│       ├── admin_applicant_detail.html # Full applicant view with CV
│       └── admin_create_job.html       # Post new job form
│
├── static/
│   ├── css/style.css           # Full custom design system
│   └── js/skills_autocomplete.js  # LinkedIn-style skills widget
│
├── media/
│   └── cvs/                    # Uploaded CV files
│
├── db.sqlite3                  # SQLite database
└── manage.py
```

---

## Installation & Setup

### Prerequisites

- Python 3.10+
- pip
- A Gmail account (for sending emails) or Mailtrap (for testing)
- A Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/soorty-recruitment-portal.git
cd soorty-recruitment-portal
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install django
pip install google-generativeai
pip install PyPDF2
```

### 4. Apply database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

---

## Configuration

Open `config/settings.py` and add the following at the bottom:

```python
# ── Google Gemini AI ──
GEMINI_API_KEY = 'your-gemini-api-key-here'

# ── Email Configuration ──
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-gmail@gmail.com'
EMAIL_HOST_PASSWORD = 'your-gmail-app-password'
DEFAULT_FROM_EMAIL = 'SOORTY HR <your-gmail@gmail.com>'
```

### Getting a Gemini API Key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **Get API Key** → **Create API key**
4. Copy and paste it into `settings.py`

### Getting a Gmail App Password

1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** if not already on
3. Go to **App Passwords**
4. Select **Mail** → Generate
5. Copy the 16-character password into `EMAIL_HOST_PASSWORD`

### Using Mailtrap (for testing without real emails)

Replace the email settings with:

```python
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_PORT = 2525
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-mailtrap-username'
EMAIL_HOST_PASSWORD = 'your-mailtrap-password'
```

---

## Usage Guide

### As a Candidate

1. Visit the home page at `/`
2. Browse job openings via **Job Openings** in the navbar
3. Click **View Details** on any job, then **Apply Now**
4. Fill in the application form — if you don't have an account, create one inline
5. Submit — you'll receive an email within seconds with your result
6. Log in and visit **Dashboard** to track your applications

### As an Admin

1. Log in with your superuser credentials
2. You'll be redirected to the **Admin Dashboard** at `/admin-dashboard/`
3. Click **+ Post New Job** to create a job opening
4. Click **View Candidates →** next to any job to see all applicants
5. Click **Open Dashboard** on any candidate to see their full profile, CV, AI score, and interview slot
6. Update the application status using the dropdown in the candidate view
7. Access raw Django admin via **Go to Django Admin** in the navbar

---

## AI Screening System

When a candidate submits an application, the following happens automatically:

```
Candidate submits form
        ↓
Application saved to database
        ↓
PDF CV text extracted (PyPDF2)
        ↓
Gemini AI analyzes:
  - Application form fields
  - Extracted CV content
  - Against job requirements
        ↓
Score returned (0–100)
        ↓
Score ≥ 70%                    Score < 70%
     ↓                               ↓
Next free interview slot       Rejection email sent
assigned (weekdays 9am–3pm,    Status → Rejected
no clashes)
     ↓
Interview invitation email sent
Status → Accepted
```

### Interview Slot Logic

- Slots are Monday–Friday, 9:00 AM to 3:00 PM
- Each slot is 1 hour long (9am, 10am, 11am, 12pm, 1pm, 2pm, 3pm)
- All existing booked slots across all jobs are checked before assigning
- No two candidates ever get the same date and time
- Searches up to 60 days ahead to find a free slot

---

## User Roles

| Role | Access |
|---|---|
| **Guest** | Browse jobs, view job details, apply (creates account inline) |
| **Candidate** | All guest access + personal dashboard, edit profile, track applications |
| **Admin/Staff** | Admin dashboard, post jobs, view all applicants, update statuses, Django admin |

Admins do not see the public job browsing or apply buttons — their navbar only shows Admin Dashboard and Dashboard links.

---

## Database Models

### Profile
Extends Django's built-in User model with candidate-specific fields.

| Field | Type | Description |
|---|---|---|
| user | OneToOneField | Links to Django User |
| display_name | CharField | Public display name |
| custom_id | CharField | Auto-generated (USR-0001) |
| gender | CharField | M / F / O |
| age | IntegerField | Candidate age |
| experience | IntegerField | Years of experience |
| skills | ManyToManyField | Linked Skill objects |
| cv | FileField | Uploaded CV file |

### Job
Represents a job posting created by admin.

| Field | Type | Description |
|---|---|---|
| title | CharField | Job title |
| department | CharField | Department name |
| description | TextField | Full job description |
| requirements | TextField | Requirements (used by AI) |
| location | CharField | Location or Remote |
| job_type | CharField | Full-time / Part-time / etc. |
| created_at | DateTimeField | Auto timestamp |

### Application
Represents a candidate's job application.

| Field | Type | Description |
|---|---|---|
| user | ForeignKey | Applicant user |
| job | ForeignKey | Job applied to |
| full_name | CharField | Name from form |
| age | IntegerField | Age from form |
| experience_years | IntegerField | Experience from form |
| skills_text | TextField | Comma-separated skills |
| cover_letter | TextField | Cover letter text |
| cv | FileField | Uploaded CV |
| status | CharField | Pending/Reviewed/Accepted/Rejected |
| ai_score | IntegerField | AI match percentage |
| ai_reason | TextField | AI one-line assessment |
| interview_slot | DateTimeField | Auto-assigned interview time |

---

## Key URLs

| URL | Description |
|---|---|
| `/` | Home / landing page |
| `/about/` | About SOORTY Denimkind |
| `/jobs/` | All job openings |
| `/jobs/<id>/` | Job detail page |
| `/jobs/<id>/apply/` | Application form |
| `/register/` | Candidate registration |
| `/login/` | Login |
| `/logout/` | Logout |
| `/dashboard/` | Candidate dashboard |
| `/edit-profile/` | Edit profile |
| `/admin-dashboard/` | Admin overview |
| `/admin-dashboard/jobs/<id>/` | Applicants for a job |
| `/admin-dashboard/applications/<id>/` | Applicant detail |
| `/admin-dashboard/jobs/create/` | Post new job |
| `/django-admin/` | Raw Django admin |

---

## Design System

The UI uses a warm beige/clay luxury palette with custom CSS variables:

```css
--clr-bg: #FAF7F2        /* Page background */
--clr-surface: #F6F0E6   /* Card backgrounds */
--clr-primary: #9A8472   /* Brand color */
--clr-accent: #B8956A    /* Accent / highlight */
--clr-text: #4B3B2F      /* Body text */
```

Headings use **Cormorant Garamond** (serif) for an elegant editorial feel. Body text uses **Segoe UI** for clean readability.

---

## Built By

**Fatima Iqbal** — AI Engineering Student, Batch 25F  
Famma Ash | Famma Ash Studio | Famma Ash Creatives

---

*Built with Django · Powered by Google Gemini AI · Designed for SOORTY Denimkind*
