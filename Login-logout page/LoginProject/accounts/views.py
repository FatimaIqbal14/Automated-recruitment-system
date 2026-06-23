from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import models
from datetime import datetime

from .forms import RegisterForm, JobApplicationForm, EditProfileForm
from .models import Profile, Job, Application, Skill, ApplicationReview, InterviewAvailability, InterviewSlot


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
    latest_review = application.reviews.order_by('-created_at').first()

    cv_type = None
    if application.cv:
        name = application.cv.name.lower()
        if '.pdf' in name:
            cv_type = 'pdf'
        elif '.png' in name or '.jpg' in name or '.jpeg' in name:
            cv_type = 'image'
        else:
            cv_type = 'other'

    return render(request, 'accounts/admin_applicant_detail.html', {
        'application': application,
        'profile': profile,
        'applicant': applicant,
        'cv_type': cv_type,
        'latest_review': latest_review,
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

@staff_member_required
def admin_edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        department = request.POST.get('department')
        location = request.POST.get('location', 'Remote')
        job_type = request.POST.get('job_type', 'Full-time')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')

        if title and department and description:
            job.title = title
            job.department = department
            job.location = location
            job.job_type = job_type
            job.description = description
            job.requirements = requirements
            job.save()
            messages.success(request, f"Job '{title}' updated successfully.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Please fill out all required fields.")

    return render(request, 'accounts/admin_edit_job.html', {'job': job})


@login_required
def manage_developers(request):
    from django.core.exceptions import PermissionDenied
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("You do not have permission to access this page.")

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        target_user = get_object_or_404(User, id=user_id)
        profile, _ = Profile.objects.get_or_create(user=target_user)

        if action == 'grant':
            profile.is_developer = True
            profile.save()
            messages.success(request, f"Granted Developer status to {target_user.email or target_user.username}.")
        elif action == 'revoke':
            profile.is_developer = False
            profile.save()
            messages.success(request, f"Revoked Developer status from {target_user.email or target_user.username}.")

        return redirect('manage_developers')

    # Ensure all users have a profile to avoid template errors
    for u in User.objects.all():
        Profile.objects.get_or_create(user=u)

    users = User.objects.all().select_related('profile').order_by('username')
    return render(request, 'accounts/manage_developers.html', {'users': users})


# ── Phase 3: AI Review → Admin Approval pipeline ──────────────────────────────

@staff_member_required
def manage_reviews(request):
    """
    Admin-facing list of all AI-generated reviews, grouped by job,
    sectioned by review_status: Pending / Approved-not-sent / Sent.
    """
    jobs = Job.objects.all().order_by('-created_at')
    job_groups = []

    for job in jobs:
        reviews = (
            ApplicationReview.objects
            .filter(application__job=job)
            .select_related('application', 'application__user', 'application__user__profile')
            .order_by('-created_at')
        )
        pending = [r for r in reviews if r.review_status == 'PENDING']
        approved = [r for r in reviews if r.review_status in ('APPROVED', 'EDITED_APPROVED')]
        sent = [r for r in reviews if r.review_status == 'SENT']

        if pending or approved or sent:
            job_groups.append({
                'job': job,
                'pending': pending,
                'approved': approved,
                'sent': sent,
            })

    total_pending = ApplicationReview.objects.filter(review_status='PENDING').count()

    return render(request, 'accounts/manage_reviews.html', {
        'job_groups': job_groups,
        'total_pending': total_pending,
    })


@staff_member_required
def review_detail(request, review_id):
    """
    Admin can view the AI's suggested status + drafted email for a single
    application, edit the final status/email, save as a draft, or send it
    to the candidate. Nothing reaches the candidate until 'Send Response'
    is clicked explicitly.
    """
    review = get_object_or_404(
        ApplicationReview.objects.select_related(
            'application', 'application__user', 'application__user__profile', 'application__job'
        ),
        id=review_id
    )
    application = review.application

    # Available interview slots for this job (free, future), for the admin
    # to optionally (re)assign before sending an interview invite.
    available_slots = InterviewSlot.objects.filter(
        is_occupied=False
    ).filter(
        models.Q(availability__job=application.job) | models.Q(availability__job__isnull=True)
    ).order_by('start_time')[:50]

    if request.method == 'POST':
        action = request.POST.get('action')

        final_status = request.POST.get('final_status')
        final_email_subject = request.POST.get('final_email_subject', '').strip()
        final_email_body = request.POST.get('final_email_body', '').strip()
        slot_id = request.POST.get('interview_slot')

        if final_status not in dict(Application.STATUS_CHOICES):
            messages.error(request, "Invalid status selected.")
            return redirect('review_detail', review_id=review.id)

        edited = (
            final_status != (review.final_status or review.ai_suggested_status)
            or final_email_subject != (review.final_email_subject or review.ai_generated_email_subject)
            or final_email_body != (review.final_email_body or review.ai_generated_email_body)
        )

        review.final_status = final_status
        review.final_email_subject = final_email_subject
        review.final_email_body = final_email_body

        # Admin can attach/replace the interview slot before sending
        new_slot = None
        if slot_id:
            new_slot = InterviewSlot.objects.filter(id=slot_id, is_occupied=False).first()
            if new_slot:
                review.interview_slot = new_slot

        review.reviewed_by = request.user
        review.reviewed_at = timezone.now()

        if action == 'save':
            review.review_status = 'EDITED_APPROVED' if edited else 'APPROVED'
            review.save()
            messages.success(request, "Review saved. The candidate has not been notified yet.")
            return redirect('review_detail', review_id=review.id)

        elif action == 'send':
            # Send the actual email to the candidate now.
            try:
                send_mail(
                    subject=review.final_email_subject,
                    message=review.final_email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[application.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                messages.error(request, f"Failed to send email: {e}")
                review.review_status = 'EDITED_APPROVED' if edited else 'APPROVED'
                review.save()
                return redirect('review_detail', review_id=review.id)

            # Occupy the interview slot, if one is attached — re-check it's
            # still free right before committing, in case of a race.
            if review.interview_slot:
                review.interview_slot.refresh_from_db()
                if review.interview_slot.is_occupied and review.interview_slot.application_id != application.id:
                    messages.warning(
                        request,
                        "Heads up: the attached interview slot was just booked by someone else. "
                        "The response was still sent, but please assign a different slot."
                    )
                else:
                    review.interview_slot.is_occupied = True
                    review.interview_slot.application = application
                    review.interview_slot.save()

            application.status = review.final_status
            application.email_sent = review.final_email_body
            application.save()

            review.review_status = 'SENT'
            review.sent_at = timezone.now()
            review.save()

            messages.success(request, f"Response sent to {application.user.email}.")
            return redirect('manage_reviews')

    return render(request, 'accounts/review_detail.html', {
        'review': review,
        'application': application,
        'available_slots': available_slots,
        'selected_status': review.final_status or review.ai_suggested_status,
    })


# ── Phase 4: Interview Scheduling ─────────────────────────────────────────────

@staff_member_required
def manage_interview_availability(request):
    """Admin defines windows of available interview dates/times, per-job or global."""
    if request.method == 'POST':
        job_id = request.POST.get('job')
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        slot_duration = request.POST.get('slot_duration_minutes') or 30

        if date_str and start_time_str and end_time_str:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                parsed_start_time = datetime.strptime(start_time_str, '%H:%M').time()
                parsed_end_time = datetime.strptime(end_time_str, '%H:%M').time()
                slot_duration = int(slot_duration)
            except (ValueError, TypeError):
                messages.error(request, "Date, time, or slot duration format was invalid. Please try again.")
                return redirect('manage_interview_availability')

            if parsed_end_time <= parsed_start_time:
                messages.error(request, "End time must be after start time.")
                return redirect('manage_interview_availability')

            job = Job.objects.filter(id=job_id).first() if job_id else None
            InterviewAvailability.objects.create(
                job=job,
                date=parsed_date,
                start_time=parsed_start_time,
                end_time=parsed_end_time,
                slot_duration_minutes=slot_duration,
            )
            messages.success(request, "Interview availability window added and slots generated.")
            return redirect('manage_interview_availability')
        else:
            messages.error(request, "Please fill out date, start time, and end time.")

    jobs = Job.objects.all().order_by('-created_at')
    windows = InterviewAvailability.objects.select_related('job').order_by('-date')
    return render(request, 'accounts/manage_interview_availability.html', {
        'jobs': jobs,
        'windows': windows,
    })

@staff_member_required
def interview_timetable(request):
    """
    Admin-only grid of all interview slots: columns are dates (days),
    rows are times-of-day, and each cell shows Occupied/Free (or blank
    if no slot exists for that date+time combination).
    """
    job_id = request.GET.get('job')

    slots = InterviewSlot.objects.select_related(
        'availability', 'availability__job', 'application', 'application__user'
    ).order_by('start_time')

    if job_id:
        slots = slots.filter(availability__job_id=job_id)

    jobs = Job.objects.all().order_by('-created_at')

    occupied_count = slots.filter(is_occupied=True).count()
    free_count = slots.filter(is_occupied=False).count()

    # Build a date (column) x time-of-day (row) grid.
    dates = sorted({slot.start_time.date() for slot in slots})
    times = sorted({slot.start_time.time() for slot in slots})

    # grid[time][date] = slot (or None if nothing scheduled at that cell)
    grid_lookup = {}
    for slot in slots:
        grid_lookup[(slot.start_time.time(), slot.start_time.date())] = slot

    grid_rows = []
    for t in times:
        row_cells = []
        for d in dates:
            row_cells.append(grid_lookup.get((t, d)))
        grid_rows.append({'time': t, 'cells': row_cells})

    return render(request, 'accounts/interview_timetable.html', {
        'slots': slots,
        'jobs': jobs,
        'selected_job_id': int(job_id) if job_id else None,
        'occupied_count': occupied_count,
        'free_count': free_count,
        'dates': dates,
        'grid_rows': grid_rows,
    })