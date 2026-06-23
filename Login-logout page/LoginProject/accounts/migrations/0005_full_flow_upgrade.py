from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # Replace '0004_application' with whatever your last migration is
        ('accounts', '0004_application'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add new fields to Application
        migrations.AddField(
            model_name='application',
            name='full_name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='application',
            name='age',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='experience_years',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='skills_text',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='application',
            name='cover_letter',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='application',
            name='cv',
            field=models.FileField(blank=True, null=True, upload_to='cvs/'),
        ),
        # Add STATUS_CHOICES to Application
        migrations.AlterField(
            model_name='application',
            name='status',
            field=models.CharField(
                choices=[
                    ('Pending', 'Pending'),
                    ('Reviewed', 'Reviewed'),
                    ('Accepted', 'Accepted'),
                    ('Rejected', 'Rejected'),
                ],
                default='Pending',
                max_length=20,
            ),
        ),
        # Add location and job_type to Job
        migrations.AddField(
            model_name='job',
            name='location',
            field=models.CharField(default='Remote', max_length=100),
        ),
        migrations.AddField(
            model_name='job',
            name='job_type',
            field=models.CharField(default='Full-time', max_length=50),
        ),
        # Allow Profile fields to be optional
        migrations.AlterField(
            model_name='profile',
            name='age',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='experience',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='gender',
            field=models.CharField(blank=True, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=1),
        ),
        migrations.AlterField(
            model_name='profile',
            name='cv',
            field=models.FileField(blank=True, null=True, upload_to='cvs/'),
        ),
    ]
