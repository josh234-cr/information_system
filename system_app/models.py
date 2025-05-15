#models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None  
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class WebAuthnCredential(models.Model):
    """Stores WebAuthn passkeys for biometric authentication via Windows Hello."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    credential_id = models.CharField(max_length=255, unique=True)
    public_key = models.TextField()
    sign_count = models.IntegerField(default=0)
    transports = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Credential for {self.user.email}"


class Passkey(models.Model):
    """Passkey authentication for users."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    passkey = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Passkey for {self.user.email}"


class Refugee(models.Model):
    GENDER_CHOICES = [("Male", "Male"), ("Female", "Female"), ("Other", "Other")]
    REFUGEE_STATUS_CHOICES = [
        ("Asylum Seeker", "Asylum Seeker"),
        ("Recognized Refugee", "Recognized Refugee"),
        ("Stateless", "Stateless"),
    ]

    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    nationality = models.CharField(max_length=100)
    language_spoken = models.CharField(max_length=255)
    refugee_status = models.CharField(max_length=50, choices=REFUGEE_STATUS_CHOICES)

    # Biometric Data
    fingerprint_data = models.JSONField(null=True, blank=True)
    facial_embedding = models.JSONField(null=True, blank=True)  # Stores facial vector data
    facial_embedding_ipfs = models.CharField(max_length=255, null=True, blank=True)
    fingerprint_data_ipfs = models.CharField(max_length=255, null=True, blank=True)

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
