from django.db import models

# Create your models here.

class Refugee(models.Model):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    
    REFUGEE_STATUS_CHOICES = [
        ("Asylum Seeker", "Asylum Seeker"),
        ("Recognized Refugee", "Recognized Refugee"),
        ("Stateless", "Stateless"),
    ]

    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10,choices=GENDER_CHOICES)
    nationality = models.CharField(max_length=100)
    language_spoken = models.CharField(max_length=255)
    refugee_status = models.CharField(max_length=50, choices=REFUGEE_STATUS_CHOICES)
    
    # Biometric Data (Stored as File or Hash)
    fingerprint_data = models.JSONField(null=True, blank=True)
    facial_image = models.ImageField(upload_to='faces/', null=True, blank=True)
    
    # Contact Information
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    location = models.CharField(max_length=255)

    # Medical Data
    medical_history = models.TextField(null=True, blank=True)
    vaccination_records = models.TextField(null=True, blank=True)
    chronic_illnesses = models.CharField(max_length=255, null=True, blank=True)

    # Financial & Aid Data
    bank_account = models.CharField(max_length=100, null=True, blank=True)
    aid_received = models.TextField(null=True, blank=True)

    # Education & Work History
    education_level = models.CharField(max_length=255, null=True, blank=True)
    work_experience = models.TextField(null=True, blank=True)

    # Legal & Immigration
    immigration_documents = models.FileField(upload_to='documents/', null=True, blank=True)
    previous_country = models.CharField(max_length=100, null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
