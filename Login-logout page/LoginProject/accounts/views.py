from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from .forms import RegisterForm, JobApplicationForm, EditProfileForm
from .models import Profile, Job, Application, Skill


# ── Public pages ─────────────────────────────────────────────────────────────

def home(request):
    """Landing page — shows featured job openings."""
    jobs = Job.objects.all().order_by('-created_at')[:6]
    return render(request, 'accounts/home.html', {'jobs': jobs})


def about(request):
    return render(request, 'accounts/about.html')


def job_openings(request):
    """Full list of available jobs."""
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'accounts/job_openings.html', {'jobs': jobs})


def job_detail(request, job_id):
    """Single job detail page."""
    job = get_object_or_404(Job, id=job_id)
    has_applied = False
    if request.user.is_authenticated:
        has_applied = Application.objects.filter(user=request.user, job=job).exists()
    return render(request, 'accounts/job_detail.html', {'job': job, 'has_applied': has_applied})


# ── Apply flow ────────────────────────────────────────────────────────────────

def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    user_logged_in = request.user.is_authenticated

    if user_logged_in:
        if Application.objects.filter(user=request.user, job=job).exists():
            messages.error(request, "You have already applied for this job.")
            return redirect('dashboard')

    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if user_logged_in:
            request.POST = request.POST.copy()
            request.POST['create_account'] = False
            form = JobApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            cd = form.cleaned_data

            if user_logged_in:
                applicant = request.user
            else:
                applicant = User.objects.create_user(
                    username=cd['email'],
                    email=cd['email'],
                    password=cd['password1'],
                )
                profile = Profile.objects.create(
                    user=applicant,
                    display_name=cd['username'],
                    age=cd['age'],
                    gender=cd.get('gender', ''),
                    experience=cd['experience_years'],
                    cv=cd.get('cv')
                )
                skills_str = cd.get('skills_text', '')
                skill_names = [s.strip() for s in skills_str.split(',') if s.strip()]
                skill_objects = []
                for name in skill_names:
                    skill, _ = Skill.objects.get_or_create(name=name)
                    skill_objects.append(skill)
                profile.skills.set(skill_objects)
                profile.save()
                login(request, applicant)

            # Create application record
            application = Application.objects.create(
                user=applicant,
                job=job,
                full_name=cd['full_name'],
                age=cd['age'],
                experience_years=cd['experience_years'],
                skills_text=cd['skills_text'],
                cover_letter=cd.get('cover_letter', ''),
                cv=cd.get('cv') or (applicant.profile.cv if user_logged_in else None),
            )

            # Save gender to profile
            gender = cd.get('gender', '')
            if gender:
                if user_logged_in:
                    profile = Profile.objects.filter(user=applicant).first()
                    if profile:
                        profile.gender = gender
                        profile.save()
                else:
                    Profile.objects.filter(user=applicant).update(gender=gender)

            # Run AI screening and send email automatically
            from .ai_screening import screen_application
            screen_application(application)

            return redirect('application_success')

    else:
        initial = {}
        if user_logged_in:
            profile = Profile.objects.filter(user=request.user).first()
            initial['full_name'] = request.user.get_full_name() or (profile.display_name if profile else request.user.username)
            if profile:
                initial['age'] = profile.age
                initial['experience_years'] = profile.experience
                initial['skills_text'] = ", ".join([s.name for s in profile.skills.all()])
                initial['gender'] = profile.gender
        form = JobApplicationForm(initial=initial)

    return render(request, 'accounts/apply_job.html', {
        'form': form,
        'job': job,
        'user_logged_in': user_logged_in,
    })


def application_success(request):
    return render(request, 'accounts/application_success.html')


# ── Auth ──────────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile, _ = Profile.objects.get_or_create(user=user)

            profile.display_name = form.cleaned_data.get('display_name', '')
            profile.age = form.cleaned_data.get('age')
            profile.gender = form.cleaned_data.get('gender', '')
            profile.experience = form.cleaned_data.get('experience')

            skills_str = form.cleaned_data.get('skills_text', '')
            skill_names = [s.strip() for s in skills_str.split(',') if s.strip()]
            skill_objects = []
            for name in skill_names:
                skill, _ = Skill.objects.get_or_create(name=name)
                skill_objects.append(skill)
            profile.skills.set(skill_objects)

            profile.save()

            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


# ── Dashboard & profile ───────────────────────────────────────────────────────

@login_required
def dashboard(request):
    profile = Profile.objects.filter(user=request.user).first()
    applications = Application.objects.filter(user=request.user).select_related('job')
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'accounts/dashboard.html', {
        'profile': profile,
        'applications': applications,
        'jobs': jobs,
    })


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = EditProfileForm(instance=profile)
    return render(request, 'accounts/edit_profile.html', {'form': form})


def skills_autocomplete(request):
    q = request.GET.get('q', '').strip()
    if q:
        skills = Skill.objects.filter(name__icontains=q)[:10]
    else:
        skills = Skill.objects.none()
    results = [{'id': s.id, 'name': s.name} for s in skills]
    return JsonResponse(results, safe=False)


# ── Custom Admin Dashboard Views (Staff/Superuser only) ────────────────────────

@staff_member_required
def admin_dashboard(request):
    jobs = Job.objects.all().order_by('-created_at')
    for job in jobs:
        job.app_count = Application.objects.filter(job=job).count()

    users = User.objects.filter(is_staff=False).select_related('profile')
    total_applications = Application.objects.count()

    return render(request, 'accounts/admin_dashboard.html', {
        'jobs': jobs,
        'users': users,
        'total_applications': total_applications,
    })


@staff_member_required
def admin_job_applicants(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applications = Application.objects.filter(job=job).select_related('user', 'user__profile').order_by('-applied_at')
    return render(request, 'accounts/admin_job_applicants.html', {'job': job, 'applications': applications})


@staff_member_required
def admin_applicant_detail(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    applicant = application.user
    profile = getattr(applicant, 'profile', None)

    cv_type = None
    if application.cv:
        name = application.cv.name.lower()
        if '.pdf' in name:
            cv_type = 'pdf'
        elif '.png' in name or '.jpg' in name or '.jpeg' in name:
            cv_type = 'image'
        else:
            cv_type = 'other'

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Application.STATUS_CHOICES):
            application.status = status
            application.save()
            messages.success(request, f"Application status updated to '{status}'.")
            return redirect('admin_applicant_detail', application_id=application.id)

    return render(request, 'accounts/admin_applicant_detail.html', {
        'application': application,
        'profile': profile,
        'applicant': applicant,
        'cv_type': cv_type,
    })


@staff_member_required
def admin_create_job(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        department = request.POST.get('department')
        location = request.POST.get('location', 'Remote')
        job_type = request.POST.get('job_type', 'Full-time')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')

        if title and department and description:
            job = Job.objects.create(
                title=title,
                department=department,
                location=location,
                job_type=job_type,
                description=description,
                requirements=requirements
            )
            messages.success(request, f"Job '{title}' created successfully.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Please fill out all required fields.")

    return render(request, 'accounts/admin_create_job.html')