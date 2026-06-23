from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('jobs/', views.job_openings, name='job_openings'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('application-success/', views.application_success, name='application_success'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('skills/autocomplete/', views.skills_autocomplete, name='skills_autocomplete'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/jobs/<int:job_id>/', views.admin_job_applicants, name='admin_job_applicants'),
    path('admin-dashboard/applications/<int:application_id>/', views.admin_applicant_detail, name='admin_applicant_detail'),
    path('admin-dashboard/jobs/create/', views.admin_create_job, name='admin_create_job'),
]
