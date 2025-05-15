import os
import json
import base64
import secrets
import cv2
import uuid
from fido2.cose import ES256
import numpy as np
from PIL import Image
from io import BytesIO
from django.contrib import messages
from fido2.server import Fido2Server
from fido2.client import CollectedClientData
from .models import Refugee, WebAuthnCredential
from rest_framework import status
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import RefugeeSerializer
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, get_user_model
from fido2.utils import websafe_decode, websafe_encode
from base64 import urlsafe_b64decode, urlsafe_b64encode
from django.http import JsonResponse, HttpResponseRedirect
from deepface import DeepFace
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Refugee
from deepface import DeepFace
from scipy.spatial.distance import cosine
from .forms import RefugeeRegistrationForm, CustomUserCreationForm, CustomAuthenticationForm
from fido2.webauthn import PublicKeyCredentialRpEntity, AttestationObject, AuthenticatorData
from fido2.webauthn import PublicKeyCredentialRpEntity, AttestationObject, AuthenticatorData
from django.shortcuts import render
from django.db import connections
from django.shortcuts import render
from django.db import connections
import os
import json
import uuid
import cv2
import ipfshttpclient
import numpy as np
import logging
from django.http import JsonResponse, HttpResponseRedirect
from deepface import DeepFace
from .models import Refugee
from django_ratelimit.decorators import ratelimit
import logging
import requests
from deepface import DeepFace
from scipy.spatial.distance import cosine
import json
import numpy as np
import base64
import cv2
from PIL import Image
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json

# connect to the MySQL database
def appointments(request):
    with connections['default'].cursor() as sqlite_cursor, connections['health_db'].cursor() as mysql_cursor:
        # Get names from the refugee system (SQLite)
        sqlite_cursor.execute("SELECT full_name FROM system_app_refugee")
        refugee_names = {row[0] for row in sqlite_cursor.fetchall()}  # Store names in a set for quick lookup

        # Get appointments from MySQL
        mysql_cursor.execute("SELECT doctor_name, patient_name, appointment_date, appointment_time, created_at FROM Appointments")
        all_appointments = mysql_cursor.fetchall()

        # Filter appointments where patient_name exists in refugee_names
        matching_appointments = [appointment for appointment in all_appointments if appointment[1] in refugee_names]

    return render(request, 'appointments.html', {'records': matching_appointments})


def health_records(request):
    with connections['default'].cursor() as sqlite_cursor, connections['health_db'].cursor() as mysql_cursor:
        # Get names from the refugee system (SQLite)
        sqlite_cursor.execute("SELECT full_name FROM system_app_refugee")
        refugee_names = {row[0] for row in sqlite_cursor.fetchall()}  # Store names in a set for quick lookup

        # Get health records from MySQL
        mysql_cursor.execute("SELECT patient_name, diagnosis, treatment, created_at FROM health_records")
        all_health_records = mysql_cursor.fetchall()

        # Filter records where patient_name exists in refugee_names
        matching_records = [record for record in all_health_records if record[0] in refugee_names]

    return render(request, 'health_records.html', {'records': matching_records})



# capture face using webcam

logger = logging.getLogger(__name__)

@ratelimit(key='ip', rate='5/m')  # Prevent spam
def capture_face(request):
    full_name = request.GET.get("username")

    if not full_name:
        return JsonResponse({"error": "Missing refugee username."}, status=400)
    
    if len(full_name) > 100 or not full_name.replace(" ", "").isalnum():
        return JsonResponse({"error": "Invalid username format."}, status=400)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return JsonResponse({"error": "Could not access webcam."}, status=400)

    while True:
        ret, frame = cap.read()
        if not ret:
            return JsonResponse({"error": "Failed to capture image."}, status=400)

        cv2.imshow("Scanning Face - Press Space to Capture", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # Space key
            break
        elif key == 27:  # ESC key
            cap.release()
            cv2.destroyAllWindows()
            return JsonResponse({"error": "Face capture cancelled."}, status=400)

    cap.release()
    cv2.destroyAllWindows()

    try:
        print("Face detection about to start")

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB
        frame_resized = cv2.resize(frame_rgb, (160, 160))  # Resize to 160x160
        print("Face detected ... now processing")

        max_retries = 3  # Set a retry limit
        retry_count = 0

        while retry_count < max_retries:
            detected_faces = DeepFace.extract_faces(frame_resized, detector_backend="opencv", enforce_detection=False)
            
            if detected_faces:  # If face is detected, break loop and proceed
                break
            
            print(f"No face detected. Retrying... ({retry_count + 1}/{max_retries})")
            retry_count += 1

        if not detected_faces:
            return JsonResponse({"success": False, "error": "No face detected try again after sometime."})

        print("Face extracted ... now embedding")
        embeddings = DeepFace.represent(frame_resized, model_name="Facenet", enforce_detection=False)
        print("Face embedding complete ... now processing")

        if not embeddings:
            return JsonResponse({"error": "No embedding generated."}, status=400)

        embedding_vector = np.array(embeddings[0]["embedding"], dtype=np.float32).tolist()  # Force float32
        embedding_json = json.dumps({"vector": embedding_vector})

        _, img_encoded = cv2.imencode(".jpg", frame)
        img_bytes = img_encoded.tobytes()

        try:
            client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001")
            image_cid = client.add_bytes(img_bytes)
            embedding_cid = client.add_bytes(embedding_json.encode("utf-8"))
        except Exception as e:
            logger.error("IPFS Error: %s", str(e))
            return JsonResponse({"error": "Failed to upload to IPFS."}, status=500)

        try:
            refugee = Refugee.objects.get(full_name=full_name)
            refugee.face_image_cid = image_cid
            refugee.facial_embedding_ipfs = embedding_cid
            refugee.save()
        except Refugee.DoesNotExist:
            return JsonResponse({"error": "Refugee not found in the database."}, status=404)

        with open("ipfs_records.txt", "a") as file:
            file.write(f"Image CID: {image_cid}\nEmbedding CID: {embedding_cid}\n\n")

        return HttpResponseRedirect("/dashboard/")

    except ValueError as e:
        logger.error("Face processing error: %s", str(e))
        return JsonResponse({"error": "Face recognition failed."}, status=400)


# connect to local IPFS and fetch facial embedding
# Ensure you have the IPFS daemon running locally
# and the IPFS HTTP API is accessible at the specified address.

LOCAL_IPFS_GATEWAY = "http://127.0.0.1:8080/ipfs/"

def fetch_embedding_from_ipfs(cid):
    """Retrieve the facial embedding from IPFS using the CID."""
    url = f"{LOCAL_IPFS_GATEWAY}{cid}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()  # Parse JSON response

        if isinstance(data, dict) and "vector" in data:
            vector = data["vector"]
            if isinstance(vector, list):
                return np.array(vector, dtype=np.float32)  # Convert to float32
            else:
                print(f"Error: 'vector' is not a list, received: {type(vector)}")
                return None
        else:
            print(f"Error: Response does not contain 'vector' key, received: {data}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching from IPFS: {e}")
        return None

@csrf_exempt
def authenticate_refugee(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"})

    try:
        data = json.loads(request.body)
        image_data = data.get("image")
        if not image_data:
            return JsonResponse({"success": False, "error": "No image provided"})

        image_bytes = base64.b64decode(image_data.split(",")[1])
        image = Image.open(BytesIO(image_bytes))
        image = np.array(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # Convert to BGR for consistency
        image = cv2.resize(image, (160, 160))  # Resize to 160x160

        embedding_result = DeepFace.represent(image, model_name="Facenet", enforce_detection=False)
        if not embedding_result:
            return JsonResponse({"success": False, "error": "No face detected"})
        embedding = np.array(embedding_result[0]["embedding"], dtype=np.float32)  # Ensure float32

        try:
            with open("ipfs_records.txt", "r") as file:
                records = file.readlines()
        except FileNotFoundError:
            return JsonResponse({"success": False, "error": "IPFS records file not found."})

        for record in records:
            if "Embedding CID:" in record:
                embedding_cid = record.split("Embedding CID: ")[1].strip()
                stored_embedding = fetch_embedding_from_ipfs(embedding_cid)

                if stored_embedding is not None:
                    similarity_score = 1 - cosine(embedding, stored_embedding)
                    threshold = 0.5
                    
                    print(f"Similarity Score: {similarity_score}")
                    print("Stored Embedding:", np.round(stored_embedding[:5], 5))
                    print("Newly Extracted Embedding:", np.round(embedding[:5], 5))

                    if similarity_score >= threshold:
                        try:
                            # Fetch refugee whose embedding CID matches
                            refugee = Refugee.objects.get(facial_embedding_ipfs=embedding_cid)

                            print("Debug: Received embedding_cid ->", embedding_cid)  # Add debug print
                            
                            print("Debug: Found refugee ->", refugee.full_name, refugee.nationality)  # Debugging

                            return JsonResponse({
                                "success": True,
                                "message": "Authentication successful via IPFS",
                                "refugee": {
                                    "name": refugee.full_name,
                                    "nationality": refugee.nationality,
                                    "status": refugee.refugee_status,
                                    "dob": refugee.date_of_birth.strftime("%Y-%m-%d") if refugee.date_of_birth else "N/A",
                                }
                            })
                        except Refugee.DoesNotExist:
                            return JsonResponse({
                                "success": False,
                                "error": "Refugee record not found in the database, but matched via IPFS."
                            })
                        except Refugee.MultipleObjectsReturned:
                            return JsonResponse({
                                "success": False,
                                "error": "Multiple refugees found with the same IPFS CID. Data inconsistency detected."
                            })
                else:
                    return JsonResponse({"success": False, "error": "No matching refugee found in IPFS."})


    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})



CustomUser = get_user_model()
RP_ID = "localhost"
CHALLENGES = {}

rp = PublicKeyCredentialRpEntity(id=RP_ID, name="Refugee System")
server = Fido2Server(rp)

def auth_view(request):
    login_form = CustomAuthenticationForm()
    signup_form = CustomUserCreationForm()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            login_form = CustomAuthenticationForm(data=request.POST)
            if login_form.is_valid():
                email = login_form.cleaned_data["username"]
                password = login_form.cleaned_data["password"]
                try:
                    user = CustomUser.objects.get(email=email)
                    user = authenticate(request, email=email, password=password)
                    if user is not None:
                        login(request, user)
                        return redirect('institution_dashboard')  
                    else:
                        login_form.add_error(None, "Invalid email or password.")
                except CustomUser.DoesNotExist:
                    login_form.add_error("username", "User with this email does not exist")
        elif action == 'signup':
            signup_form = CustomUserCreationForm(request.POST)
            if signup_form.is_valid():
                new_user = signup_form.save()
                return redirect('institution_dashboard')
    return render(request, 'auth.html', {'login_form': login_form, 'signup_form': signup_form})

def institution_dashboard(request):
    refugees = Refugee.objects.all()
    return render(request, 'dashboard/institution_dashboard.html', {"refugees": refugees})

def register_refugee(request):
    if request.method == "POST":
        form = RefugeeRegistrationForm(request.POST)
        if form.is_valid():
            refugee = form.save(commit=False)

            # Do not save fingerprint data in the database (scanning is for demo purposes ony)
            '''
            # Fingerprint data
            fingerprint_data = request.POST.get("fingerprint_data")
            if fingerprint_data:
                fingerprint_data = json.loads(fingerprint_data)
                session_key = request.session.session_key
                stored_challenge = CHALLENGES.pop(session_key, None)
                if not stored_challenge or stored_challenge != fingerprint_data["challenge"]:
                    return JsonResponse({"error": "Invalid fingerprint challenge!"}, status=400)
                refugee.fingerprint_data = fingerprint_data'
                
                '''
            
            refugee.save()
            
            # Redirect to the facial capture page with full name as a parameter
            full_name = f"{refugee.full_name}"  # Adjust according to model fields
            return redirect(f"/capture/?username={full_name}")
    
    else:
        form = RefugeeRegistrationForm()
    
    return render(request, "refugees/register.html", {"form": form})

def registration_success(request):
    return render(request, "refugees/success.html")

@api_view(['POST'])
def begin_registration(request):
    print("begin_registration called")
    print(f"Request data: {request.data}")

    try:
        full_name = request.data.get("username")
        if not full_name:
            return JsonResponse({"error": "Full name is required"}, status=400)
        print(f"Received full name: {full_name}")
        
        registration_data, state = server.register_begin(
            {
                "id": secrets.token_bytes(16),
                "name": full_name,
                "displayName": full_name
            },
            user_verification="required",
        )
        print("Received Registration data")

        CHALLENGES[full_name] = state

        registration_data = {
            "publicKey": {
                "challenge": base64.b64encode(registration_data["publicKey"]["challenge"]).decode(),
                "rp": registration_data["publicKey"]["rp"],
                "user": {
                    "id": base64.b64encode(registration_data["publicKey"]["user"]["id"]).decode(),
                    "name": registration_data["publicKey"]["user"]["name"],
                    "displayName": registration_data["publicKey"]["user"]["displayName"]
                },
                "pubKeyCredParams": registration_data["publicKey"]["pubKeyCredParams"],
                "authenticatorSelection": registration_data["publicKey"].get("authenticatorSelection"),
                "timeout": registration_data["publicKey"].get("timeout"),
                "attestation": registration_data["publicKey"].get("attestation", "direct"),
                "excludeCredentials": registration_data["publicKey"].get("excludeCredentials", []),
                "extensions": registration_data["publicKey"].get("extensions")
            }
        }

        return JsonResponse(registration_data, safe=False)
    except Exception as e:
        print(f"Error in begin_registration: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['POST'])
def complete_registration(request):
    print("complete_registration called")
    try:
        full_name = request.data.get("full_name")
        if not full_name:
            return JsonResponse({"error": "Full name is required"}, status=400)
        print(f"Received full name: {full_name}")
        
        credential = request.data.get("credential")
        if not credential:
            return JsonResponse({"error": "Missing credential data"}, status=400)
        print("Received credentials")

        state = CHALLENGES.pop(full_name, None)
        if not state:
            return JsonResponse({"error": "Invalid challenge"}, status=400)
        
        def add_padding(base64_string):
            missing_padding = len(base64_string) % 4
            if missing_padding:
                return base64_string + "=" * (4 - missing_padding)
            return base64_string

        try:
            raw_client_data = credential["response"]["clientDataJSON"]
            padded = add_padding(raw_client_data)
            client_data = CollectedClientData(urlsafe_b64decode(padded))
            
            raw_attestation_object = credential["response"]["attestationObject"]
            padded = add_padding(raw_attestation_object)
            attestation_object = AttestationObject(urlsafe_b64decode(padded))
        except Exception as decode_error:
            print(f"Base64 decode error: {decode_error}")
            return JsonResponse({"error": "Invalid base64 encoding in credential data"}, status=400)
        
        print("Decoded credentials successfully")
        
        state.setdefault("rp_id", "localhost")
        auth_data = server.register_complete(state, client_data, attestation_object)
        print("Auth data object created successfully")

        credential_data = auth_data.credential_data
        if credential_data is None:
            return JsonResponse({"error": "Missing credential data"}, status=400)

        credential_id = credential_data.credential_id
        public_key_cose = credential_data.public_key
        
        if isinstance(public_key_cose, ES256):
            if public_key_cose.get(3) == -7:
                public_key_x = public_key_cose.get(-2)
                public_key_y = public_key_cose.get(-3)
                if not public_key_x or not public_key_y:
                    return JsonResponse({"error": "Invalid EC key, missing x or y values"}, status=400)
                public_key_bytes = public_key_x + public_key_y
            else:
                return JsonResponse({"error": "Unsupported key type"}, status=400)
        else:
            return JsonResponse({"error": "Invalid COSE public key format"}, status=400)
        
        public_key_base64 = base64.b64encode(public_key_bytes).decode()
        credential_id_base64 = base64.b64encode(credential_id).decode()
        
        WebAuthnCredential.objects.create(
            full_name=full_name,
            credential_id=credential_id_base64,
            public_key=public_key_base64,
            sign_count=auth_data.counter,
            transports=",".join(getattr(auth_data, "transports", [])),
        )

        return JsonResponse({"success": True, "message": "Passkey created successfully!"})
    except Exception as e:
        print(f"Error in complete_registration: {e}")
        return JsonResponse({"error": str(e)}, status=500)
