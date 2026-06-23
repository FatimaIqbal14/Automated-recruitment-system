import google.generativeai as genai
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import Application
import traceback
import os


def extract_cv_text(cv_file):
    """Extract text from uploaded CV PDF file."""
    if not cv_file:
        print("CV DEBUG: No CV file provided")
        return ""
    try:
        import PyPDF2
        cv_path = cv_file.path
        print(f"CV DEBUG: CV path = {cv_path}")
        print(f"CV DEBUG: File exists = {os.path.exists(cv_path)}")

        if not os.path.exists(cv_path):
            print("CV DEBUG: File does not exist on disk")
            return ""

        if not cv_path.lower().endswith('.pdf'):
            print(f"CV DEBUG: Not a PDF: {cv_path}")
            return f"[CV uploaded as non-PDF file: {os.path.basename(cv_path)}]"

        text = ""
        with open(cv_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            print(f"CV DEBUG: PDF has {len(reader.pages)} pages")
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                print(f"CV DEBUG: Page {i+1} extracted {len(page_text) if page_text else 0} characters")
                if page_text:
                    text += page_text + "\n"

        print(f"CV DEBUG: Total extracted text length = {len(text)}")
        print(f"CV DEBUG: First 300 chars = {text[:300]}")
        return text.strip() if text.strip() else "[CV uploaded but no text could be extracted]"

    except Exception as e:
        print(f"CV DEBUG: Exception = {e}")
        print(traceback.format_exc())
        return f"[CV text extraction failed: {str(e)}]"


def get_next_interview_slot(job):
    """
    Find next available interview slot.
    Weekdays only, 9am-3pm, 1 hour each, no clashes across ALL jobs.
    """
    # Get ALL booked slots across all jobs (not just this one)
    # This prevents clashes even across different positions
    booked_slots = list(
        Application.objects.filter(
            interview_slot__isnull=False
        ).values_list('interview_slot', flat=True)
    )

    # Normalize all booked slots to naive datetimes for comparison
    normalized_booked = set()
    for slot in booked_slots:
        if hasattr(slot, 'tzinfo') and slot.tzinfo is not None:
            # Convert aware datetime to naive UTC
            slot = slot.replace(tzinfo=None)
        # Round to the hour for comparison
        normalized_booked.add(slot.replace(minute=0, second=0, microsecond=0))

    print(f"BOOKED SLOTS: {normalized_booked}")

    # Start from tomorrow 9am
    now = datetime.now()
    start = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)

    # Search up to 60 days ahead
    for day_offset in range(60):
        candidate_date = start + timedelta(days=day_offset)

        # Skip weekends (5=Saturday, 6=Sunday)
        if candidate_date.weekday() >= 5:
            continue

        # Try each hour slot from 9am to 3pm (last interview starts at 3, ends at 4)
        for hour in range(9, 15):
            slot = candidate_date.replace(
                hour=hour, minute=0, second=0, microsecond=0
            )

            if slot not in normalized_booked:
                print(f"ASSIGNED SLOT: {slot}")
                return slot

    return None

def get_next_available_interview_slot(job):
    """
    Find next available interview slot from the custom slots.
    First tries to find a slot specific to the job, then falls back to a global slot.
    """
    from django.utils import timezone
    from .models import InterviewSlot
    
    # 1. Try to find a slot specific to the job
    slot = InterviewSlot.objects.filter(
        availability__job=job,
        is_occupied=False,
        start_time__gt=timezone.now()
    ).order_by('start_time').first()
    
    if not slot:
        # 2. Try to find a global slot (job is null)
        slot = InterviewSlot.objects.filter(
            availability__job__isnull=True,
            is_occupied=False,
            start_time__gt=timezone.now()
        ).order_by('start_time').first()
        
    return slot


def screen_application(application):
    print("SCREEN_APPLICATION CALLED")
    """Use Gemini AI to screen application and create a pending review draft."""
    job = application.job
    cv_text = extract_cv_text(application.cv) if application.cv else "No CV uploaded."
    print(f"CV TEXT SENT TO AI:\n{cv_text[:500]}")  

    prompt = f"""
You are an AI recruitment screener for SOORTY Denimkind, a denim manufacturing company.

JOB TITLE: {job.title}
DEPARTMENT: {job.department}
JOB REQUIREMENTS:
{job.requirements}

CANDIDATE APPLICATION FORM:
- Full Name: {application.full_name}
- Age: {application.age}
- Years of Experience: {application.experience_years}
- Skills (self-reported): {application.skills_text}
- Cover Letter: {application.cover_letter or 'Not provided'}

CANDIDATE CV CONTENT (extracted from uploaded CV):
{cv_text}

Analyze BOTH the application form AND the CV content together.
The CV may contain additional skills, experience, education, or projects — consider all of it.
Give a match score from 0 to 100.
Respond ONLY in this exact format with no extra text:
SCORE: <number>
REASON: <one sentence explanation>
"""

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        print("USING MODEL: gemini-2.5-flash")
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()

        score = 0
        reason = ""

        for line in text.splitlines():
            if line.startswith("SCORE:"):
                try:
                    score = int(line.replace("SCORE:", "").strip())
                except ValueError:
                    score = 0
            elif line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()

    except Exception as e:
        print(f"AI screening error: {e}")
        print(traceback.format_exc())
        application.ai_score = None
        application.ai_reason = f"AI screening failed: {str(e)}"
        application.save()
        return

    print("AI SCORE:", score)
    application.ai_score = score
    application.ai_reason = reason
    application.save()

    candidate_name = application.full_name or application.user.email
    ai_suggested_status = 'Accepted' if score >= 70 else 'Rejected'
    
    email_subject = ""
    email_body = ""
    assigned_slot = None
    
    if score >= 70:
        # Find next available interview slot
        assigned_slot = get_next_available_interview_slot(job)
        if assigned_slot:
            slot_str = assigned_slot.start_time.strftime("%A, %B %d, %Y at %I:%M %p")
            email_subject = f"Interview Invitation – {job.title} | SOORTY Denimkind"
            email_body = f"""Dear {candidate_name},

Congratulations! We have reviewed your application for the {job.title} position at SOORTY Denimkind and are pleased to invite you for an interview.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERVIEW DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Position    : {job.title}
Department  : {job.department}
Date & Time : {slot_str}
Location    : SOORTY Denimkind Office
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please reply to this email to confirm your attendance or to reschedule if needed.

We look forward to meeting you!

Best regards,
HR Team
SOORTY Denimkind
"""
        else:
            # Fallback if no slot is defined yet
            email_subject = f"Application Update – {job.title} | SOORTY Denimkind"
            email_body = f"""Dear {candidate_name},

Congratulations! We have reviewed your application for the {job.title} position and are pleased to inform you that you have been shortlisted.

Our HR team will contact you shortly to schedule your interview.

Best regards,
HR Team
SOORTY Denimkind
"""
    else:
        email_subject = f"Your Application for {job.title} – SOORTY Denimkind"
        email_body = f"""Dear {candidate_name},

Thank you for your interest in the {job.title} position at SOORTY Denimkind and for taking the time to submit your application.

After carefully reviewing your profile and CV, we regret to inform you that we will not be moving forward with your application at this time. We received applications from many talented candidates, and the competition was strong.

We encourage you to apply for future openings that match your skills and experience. You can visit our careers page regularly for new opportunities.

We wish you all the best in your career journey.

Warm regards,
HR Team
SOORTY Denimkind
"""

    # Create the review draft
    from .models import ApplicationReview
    ApplicationReview.objects.create(
        application=application,
        match_percentage=score,
        ai_suggested_status=ai_suggested_status,
        ai_generated_email_subject=email_subject,
        ai_generated_email_body=email_body,
        review_status='PENDING',
        final_status=ai_suggested_status,
        final_email_subject=email_subject,
        final_email_body=email_body,
        interview_slot=assigned_slot
    )
