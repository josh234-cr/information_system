from django.test import TestCase
from .models import CustomUser, WebAuthnCredential, Passkey, Refugee


class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="test@example.com", password="password123")

    def test_create_user(self):
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("password123"))

    def test_create_superuser(self):
        superuser = CustomUser.objects.create_superuser(email="admin@example.com", password="admin123")
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

class WebAuthnCredentialModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="test@example.com", password="password123")
        self.credential = WebAuthnCredential.objects.create(
            user=self.user,
            credential_id="credential_id_123",
            public_key="public_key_123",
            sign_count=1,
            transports="usb"
        )

    def test_webauthn_credential_creation(self):
        self.assertEqual(self.credential.user.email, "test@example.com")
        self.assertEqual(self.credential.credential_id, "credential_id_123")
        self.assertEqual(self.credential.public_key, "public_key_123")
        self.assertEqual(self.credential.sign_count, 1)
        self.assertEqual(self.credential.transports, "usb")

class PasskeyModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="test@example.com", password="password123")
        self.passkey = Passkey.objects.create(user=self.user, passkey="passkey_123")

    def test_passkey_creation(self):
        self.assertEqual(self.passkey.user.email, "test@example.com")
        self.assertEqual(self.passkey.passkey, "passkey_123")

class RefugeeModelTest(TestCase):
    def setUp(self):
        self.refugee = Refugee.objects.create(
            full_name="John Doe",
            date_of_birth="1990-01-01",
            gender="Male",
            nationality="Country",
            language_spoken="English",
            refugee_status="Asylum Seeker",
            location="Location",
        )

    def test_refugee_creation(self):
        self.assertEqual(self.refugee.full_name, "John Doe")
        self.assertEqual(self.refugee.date_of_birth, "1990-01-01")
        self.assertEqual(self.refugee.gender, "Male")
        self.assertEqual(self.refugee.nationality, "Country")
        self.assertEqual(self.refugee.language_spoken, "English")
        self.assertEqual(self.refugee.refugee_status, "Asylum Seeker")
        self.assertEqual(self.refugee.location, "Location")