from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Skill, Application


# ── Register Form (for the Register page via dropdown) ──────────────────────
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    display_name = forms.CharField(
        label='Username / Display Name',
        widget=forms.TextInput(attrs={'placeholder': 'Choose a display username'}),
        help_text='Your username does not have to be unique.'
    )
    age = forms.IntegerField(
        required=False,
        min_value=16, max_value=100,
        widget=forms.NumberInput(attrs={'placeholder': 'Age'})
    )
    gender = forms.ChoiceField(
        required=False,
        choices=[('', 'Select Gender')] + Profile.GENDER_CHOICES,
        widget=forms.Select()
    )
    experience = forms.IntegerField(
        required=False,
        min_value=0,
        label='Years of Experience',
        widget=forms.NumberInput(attrs={'placeholder': '0'})
    )
    skills_text = forms.CharField(
        required=False,
        label='Skills',
        widget=forms.TextInput(attrs={'placeholder': 'Add skills (e.g. Python, Django, React)'}),
        help_text='Type a skill and select from the dropdown, or press Enter/comma to add a custom one.'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide the built-in unique username field and make it not required
        # since we will automatically assign it to the email value in clean()
        if 'username' in self.fields:
            self.fields['username'].widget = forms.HiddenInput()
            self.fields['username'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        if email:
            cleaned_data['username'] = email
            self.instance.username = email
        return cleaned_data


# ── Job Application Form (the main apply flow) ───────────────────────────────
class JobApplicationForm(forms.Form):
    """
    Filled by EVERYONE who clicks "Apply Now".
    If the person is not logged in, we also collect account credentials.
    """
    # Personal details
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Your full name'})
    )
    age = forms.IntegerField(
        min_value=16, max_value=100,
        widget=forms.NumberInput(attrs={'placeholder': 'Age'})
    )
    gender = forms.ChoiceField(
        required=False,
        choices=[('', 'Select Gender')] + Profile.GENDER_CHOICES,
        widget=forms.Select()
    )
    experience_years = forms.IntegerField(
        min_value=0,
        label='Years of Experience',
        widget=forms.NumberInput(attrs={'placeholder': '0'})
    )
    skills_text = forms.CharField(
        label='Skills',
        widget=forms.TextInput(attrs={'placeholder': 'Add skills (e.g. Python, Django, React)'}),
        help_text='Type a skill and select from the dropdown, or press Enter/comma to add a custom one.'
    )
    cover_letter = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us why you are a great fit…'})
    )
    cv = forms.FileField(required=False, label='Upload CV (PDF)')

    # Account creation fields — only shown when user is NOT logged in
    create_account = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput())
    username = forms.CharField(
        required=False,
        label='Username / Display Name',
        widget=forms.TextInput(attrs={'placeholder': 'Choose a display username'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'})
    )
    password1 = forms.CharField(
        required=False,
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        required=False,
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat password'})
    )

    def clean(self):
        cleaned = super().clean()
        create = cleaned.get('create_account')
        if create:
            if not cleaned.get('username'):
                self.add_error('username', 'Username is required.')
            if not cleaned.get('email'):
                self.add_error('email', 'Email is required.')
            else:
                email = cleaned.get('email')
                if User.objects.filter(email=email).exists():
                    self.add_error('email', 'A user with this email address already exists.')
            p1 = cleaned.get('password1')
            p2 = cleaned.get('password2')
            if not p1:
                self.add_error('password1', 'Password is required.')
            elif p1 != p2:
                self.add_error('password2', 'Passwords do not match.')
        return cleaned


# ── Edit Profile Form ────────────────────────────────────────────────────────
class EditProfileForm(forms.ModelForm):
    cv = forms.FileField(required=False)
    skills_text = forms.CharField(
        required=False,
        label='Skills',
        widget=forms.TextInput(attrs={'placeholder': 'Add skills (e.g. Python, Django, React)'}),
        help_text='Type a skill and select from the dropdown, or press Enter/comma to add a custom one.'
    )

    class Meta:
        model = Profile
        fields = ['display_name', 'gender', 'age', 'experience', 'cv']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['skills_text'].initial = ", ".join(
                [s.name for s in self.instance.skills.all()]
            )

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
        
        # Save skills relations
        skills_str = self.cleaned_data.get('skills_text', '')
        skill_names = [s.strip() for s in skills_str.split(',') if s.strip()]
        
        skill_objects = []
        for name in skill_names:
            skill, _ = Skill.objects.get_or_create(name=name)
            skill_objects.append(skill)
        
        profile.skills.set(skill_objects)
        return profile
