from django.contrib.auth.models import User
from django.db import models


class Skill(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=150, blank=True)
    custom_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    age = models.IntegerField(null=True, blank=True)
    experience = models.IntegerField(help_text="Years of Experience", null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    cv = models.FileField(upload_to='cvs/', blank=True, null=True)
    is_developer = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or not self.custom_id:
            self.custom_id = f"USR-{self.id:04d}"
            super().save(update_fields=['custom_id'])

    def __str__(self):
        return self.user.username


class Job(models.Model):
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=100, default='Remote')
    job_type = models.CharField(max_length=50, default='Full-time')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Application(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=200, blank=True)
    age = models.IntegerField(null=True, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)

    skills_text = models.TextField(
        blank=True,
        help_text="Comma-separated skills"
    )

    cover_letter = models.TextField(blank=True)

    cv = models.FileField(
        upload_to='cvs/',
        blank=True,
        null=True
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    # AI fields
    ai_score = models.IntegerField(null=True, blank=True)
    ai_reason = models.TextField(blank=True)
    interview_slot = models.DateTimeField(null=True, blank=True)

    # Email actually sent
    email_sent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} → {self.job.title}"


class InterviewAvailability(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.IntegerField(default=30)

    def __str__(self):
        return f"{self.job.title if self.job else 'Global'} on {self.date} ({self.start_time}-{self.end_time})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # Auto-generate slots
            from datetime import datetime, timedelta
            start_dt = datetime.combine(self.date, self.start_time)
            end_dt = datetime.combine(self.date, self.end_time)
            duration = timedelta(minutes=self.slot_duration_minutes)

            current_dt = start_dt
            while current_dt + duration <= end_dt:
                InterviewSlot.objects.get_or_create(
                    availability=self,
                    start_time=current_dt,
                    end_time=current_dt + duration
                )
                current_dt += duration


class InterviewSlot(models.Model):
    availability = models.ForeignKey(InterviewAvailability, on_delete=models.CASCADE, related_name='slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    application = models.OneToOneField(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booked_slot'
    )
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        status = "Occupied" if self.is_occupied else "Free"
        return f"{self.start_time.strftime('%Y-%m-%d %H:%M')} ({status})"


class ApplicationReview(models.Model):
    REVIEW_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('EDITED_APPROVED', 'Edited Approved'),
        ('SENT', 'Sent'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='reviews')
    match_percentage = models.IntegerField(null=True, blank=True)
    ai_suggested_status = models.CharField(max_length=20, choices=Application.STATUS_CHOICES)
    ai_generated_email_subject = models.CharField(max_length=255, blank=True)
    ai_generated_email_body = models.TextField(blank=True)
    
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='PENDING')
    
    final_status = models.CharField(max_length=20, choices=Application.STATUS_CHOICES, null=True, blank=True)
    final_email_subject = models.CharField(max_length=255, null=True, blank=True)
    final_email_body = models.TextField(null=True, blank=True)
    
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    interview_slot = models.ForeignKey(InterviewSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Review for {self.application.user.username} → {self.application.job.title} ({self.review_status})"