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