import os
import django
import random
import argparse

from faker import Faker
from django.core.files.uploadedfile import SimpleUploadedFile
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "information_system.settings")
django.setup()

from system_app.models import CustomUser, Refugee  # Adjust the import based on your app name


fake = Faker()

def populate_users(n=5):
    """Create n fake users."""
    try:
        for _ in range(n):
            email = fake.email()
            password = "password123"  # Default password for testing
            user = CustomUser.objects.create_user(email=email, password=password)
            print(f"Created User: {user.email}")
    except Exception as e:
        print(f"Error populating users: {e}")

def populate_refugees(n=10):
    """Create n fake refugees."""
    try:
        gender_choices = ["Male", "Female", "Other"]
        refugee_status_choices = ["Asylum Seeker", "Recognized Refugee", "Stateless"]
        
        for _ in range(n):
            refugee = Refugee.objects.create(
                full_name=fake.name(),
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=60),
                gender=random.choice(gender_choices),
                nationality=fake.country(),
                language_spoken=fake.language_name(),
                refugee_status=random.choice(refugee_status_choices),
                phone_number=fake.phone_number(),
                email=fake.email(),
                location=fake.city(),
                medical_history=fake.text(max_nb_chars=200),
                vaccination_records=fake.text(max_nb_chars=100),
                chronic_illnesses=fake.word(),
                bank_account=fake.iban(),
                aid_received=fake.text(max_nb_chars=100),
                education_level=fake.sentence(nb_words=5),
                work_experience=fake.text(max_nb_chars=150),
                previous_country=fake.country(),
            )
            print(f"Created Refugee: {refugee.full_name}")
    except Exception as e:
        print(f"Error populating refugees: {e}")

def depopulate_db():
    """Delete all users and refugees from the database."""
    try:
        Refugee.objects.all().delete()
        CustomUser.objects.all().delete()
        print("Database depopulation complete! All users and refugees removed.")
    except Exception as e:
        print(f"Error depopulating database: {e}")

def main():
    parser = argparse.ArgumentParser(description="Manage database population.")
    parser.add_argument("--populate", action="store_true", help="Populate the database with sample data")
    parser.add_argument("--depopulate", action="store_true", help="Remove all sample data from the database")
    args = parser.parse_args()

    if args.populate:
        print("Starting database population...")
        populate_users()
        populate_refugees()
        print("Database population complete!")
    elif args.depopulate:
        print("Starting database depopulation...")
        depopulate_db()
    else:
        print("Please provide either --populate or --depopulate.")

if __name__ == "__main__":
    main()
