import json
import base64
import secrets
from .models import Refugee
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import RefugeeSerializer
from .forms import RefugeeRegistrationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from webauthn.helpers.structs import PublicKeyCredentialRpEntity
from webauthn.helpers.exceptions import InvalidRegistrationResponse

RP_ID = "127.0.0.1"  # Change to your domain when deploying

# Store challenges temporarily (ideally, use session storage)
CHALLENGES = {}


#@login_required
def institution_dashboard(request):
    return render(request, 'dashboard/institution_dashboard.html')


def register_refugee(request):
    if request.method == "POST":
        form = RefugeeRegistrationForm(request.POST)
        if form.is_valid():
            refugee = form.save(commit=False)

            # Retrieve and validate fingerprint data
            fingerprint_data = request.POST.get("fingerprint_data")
            if fingerprint_data:
                fingerprint_data = json.loads(fingerprint_data)
                
                # Validate challenge before storing fingerprint data
                session_key = request.session.session_key
                stored_challenge = CHALLENGES.pop(session_key, None)
                
                if not stored_challenge or stored_challenge != fingerprint_data["challenge"]:
                    return JsonResponse({"error": "Invalid fingerprint challenge!"}, status=400)

                refugee.fingerprint_data = fingerprint_data  # Store fingerprint data in JSON format

            refugee.save()
            return redirect("registration_success")  # Redirect to success page

    else:
        form = RefugeeRegistrationForm()

    return render(request, "refugees/register.html", {"form": form})


def generate_fingerprint_challenge(request):
    """Generate a WebAuthn challenge for fingerprint registration"""
    challenge = secrets.token_urlsafe(32)  # Generate a unique challenge
    request.session["fingerprint_challenge"] = challenge  # Store challenge in session

    return JsonResponse({"challenge": base64.b64encode(challenge.encode()).decode()})

def registration_success(request):
    return render(request, "refugees/success.html")