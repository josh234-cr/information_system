import os
import django
from django.utils.timezone import now
from faker import Faker

# Manually configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "information_system.settings")  # Replace with your actual project name
django.setup()

from system_app.models import Refugee  # Adjust the import based on your app name

fake = Faker()

def create_fake_refugees():
    refugees = [
        {
            "full_name": "Alice Johnson",
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=60),
            "gender": "Female",
            "nationality": "Kenyan",
            "language_spoken": "English, Swahili",
            "refugee_status": "Recognized Refugee",
            "phone_number": fake.phone_number(),
            "email": fake.email(),
            "location": fake.city(),
            "medical_history": "No known conditions",
            "vaccination_records": "Fully vaccinated",
            "chronic_illnesses": "None",
            "bank_account": fake.iban(),
            "aid_received": "Food, Shelter Assistance",
            "education_level": "High School",
            "work_experience": "Retail Assistant",
            "previous_country": "Uganda",
            "timestamp": now(),
        },
        {
            "full_name": "Bob Smith",
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=60),
            "gender": "Male",
            "nationality": "Sudanese",
            "language_spoken": "Arabic, English",
            "refugee_status": "Asylum Seeker",
            "phone_number": fake.phone_number(),
            "email": fake.email(),
            "location": fake.city(),
            "medical_history": "Asthma",
            "vaccination_records": "Partially vaccinated",
            "chronic_illnesses": "Asthma",
            "bank_account": fake.iban(),
            "aid_received": "Medical Assistance",
            "education_level": "University",
            "work_experience": "Teacher",
            "previous_country": "Ethiopia",
            "timestamp": now(),
        },
        {
            "full_name": "Charlie Brown",
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=60),
            "gender": "Male",
            "nationality": "Somali",
            "language_spoken": "Somali, English",
            "refugee_status": "Recognized Refugee",
            "phone_number": fake.phone_number(),
            "email": fake.email(),
            "location": fake.city(),
            "medical_history": "Diabetes",
            "vaccination_records": "Fully vaccinated",
            "chronic_illnesses": "Diabetes",
            "bank_account": fake.iban(),
            "aid_received": "Financial Aid",
            "education_level": "High School",
            "work_experience": "Construction Worker",
            "previous_country": "Eritrea",
            "timestamp": now(),
        },
        {
            "full_name": "David White",
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=60),
            "gender": "Male",
            "nationality": "Rwandan",
            "language_spoken": "Kinyarwanda, French",
            "refugee_status": "Stateless",
            "phone_number": fake.phone_number(),
            "email": fake.email(),
            "location": fake.city(),
            "medical_history": "Hypertension",
            "vaccination_records": "Fully vaccinated",
            "chronic_illnesses": "Hypertension",
            "bank_account": fake.iban(),
            "aid_received": "Legal Aid",
            "education_level": "College",
            "work_experience": "Accountant",
            "previous_country": "Burundi",
            "timestamp": now(),
        },
        {
            "full_name": "Emma Green",
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=60),
            "gender": "Female",
            "nationality": "Ethiopian",
            "language_spoken": "Amharic, English",
            "refugee_status": "Recognized Refugee",
            "phone_number": fake.phone_number(),
            "email": fake.email(),
            "location": fake.city(),
            "medical_history": "None",
            "vaccination_records": "Fully vaccinated",
            "chronic_illnesses": "None",
            "bank_account": fake.iban(),
            "aid_received": "Housing Assistance",
            "education_level": "University",
            "work_experience": "Nurse",
            "previous_country": "South Sudan",
            "timestamp": now(),
        }
    ]
    
    for data in refugees:
        Refugee.objects.create(**data)
    print("Inserted 5 refugee records into SQLite.")

create_fake_refugees()
