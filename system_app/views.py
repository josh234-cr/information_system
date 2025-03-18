import os
import json
import base64
import secrets
from .models import Refugee, WebAuthnCredential
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import RefugeeSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, get_user_model
from .forms import RefugeeRegistrationForm, CustomUserCreationForm, CustomAuthenticationForm
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity, AttestationObject, AuthenticatorData
from fido2.client import CollectedClientData
from fido2.cose import ES256
from fido2.utils import websafe_decode, websafe_encode
from base64 import urlsafe_b64decode, urlsafe_b64encode

# capture face

import cv2
import os
import json
import uuid
from django.http import JsonResponse, HttpResponseRedirect
from deepface import DeepFace
from system_app.models import Refugee

def capture_face(request):
    full_name = request.GET.get("username")

    if not full_name:
        return JsonResponse({"error": "Missing refugee username."}, status=400)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return JsonResponse({"error": "Could not access webcam."}, status=400)

    while True:
        ret, frame = cap.read()
        if not ret:
            return JsonResponse({"error": "Failed to capture image."}, status=400)

        # Show the live webcam feed
        cv2.imshow("Scanning Face - Press Space to Capture", frame)

        # Press "Space" to capture, "ESC" to exit
        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # Space key
            break
        elif key == 27:  # ESC key
            cap.release()
            cv2.destroyAllWindows()
            return JsonResponse({"error": "Face capture cancelled."}, status=400)

    cap.release()
    cv2.destroyAllWindows()

    # ✅ Save the captured image
    img_filename = f"{full_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.jpg"
    img_path = os.path.join("media/faces", img_filename)
    os.makedirs("media/faces", exist_ok=True)
    cv2.imwrite(img_path, frame)

    try:
        # ✅ Detect face before processing
        detected_faces = DeepFace.extract_faces(img_path, detector_backend="opencv")

        if not detected_faces:
            return JsonResponse({"error": "No face detected. Try again in better lighting."}, status=400)

        # ✅ Generate embedding vector
        embeddings = DeepFace.represent(img_path, model_name="Facenet", enforce_detection=False)

        if not embeddings:
            return JsonResponse({"error": "No embedding generated."}, status=400)

        embedding_vector = embeddings[0]["embedding"]

        # ✅ Save embedding to refugee profile
        try:
            refugee = Refugee.objects.get(full_name=full_name)
            refugee.facial_embedding = json.dumps(embedding_vector)  
            refugee.save()
        except Refugee.DoesNotExist:
            return JsonResponse({"error": "Refugee not found in the database."}, status=404)

        return HttpResponseRedirect("/dashboard/")

    except ValueError as e:
        print("Debug Error")
        return JsonResponse({"error": str(e)}, status=400)

# authenticate using facial recognition

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Refugee
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
from deepface import DeepFace
import json
from scipy.spatial.distance import cosine

@csrf_exempt
def authenticate_refugee(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"})

    try:
        data = json.loads(request.body)
        image_data = data.get("image")

        if not image_data:
            return JsonResponse({"success": False, "error": "No image provided"})

        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(",")[1])
        image = Image.open(BytesIO(image_bytes))
        image = np.array(image)

        # Convert to OpenCV format
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Extract face embedding directly
        embedding_result = DeepFace.represent(image, model_name="Facenet", enforce_detection=False)
        if not embedding_result:
            return JsonResponse({"success": False, "error": "No face detected"})

        embedding = np.array(embedding_result[0]["embedding"]).flatten()  # Flatten embedding

        # Compare extracted embedding with stored embeddings
        refugees = Refugee.objects.exclude(facial_embedding=None) 

        print("Debugging about to start")

        print(f"Total refugees with embeddings: {refugees.count()}")


        for refugee in refugees:

            print("Debugging in the for loop started")
            # Convert stored embedding from JSON
            try:
                stored_embedding = json.loads(refugee.facial_embedding)  # Convert from JSON string

                # Ensure stored_embedding is a list containing at least one dictionary
                if isinstance(stored_embedding, list) and len(stored_embedding) > 0:
                    first_entry = stored_embedding[0]  # Extract the first dictionary

                    if isinstance(first_entry, dict) and "embedding" in first_entry:
                        stored_embedding = first_entry["embedding"]  # Extract the actual embedding list
                    else:
                        print("❌ Error: 'embedding' key not found in the stored data")
                        continue  # Skip this refugee

                else:
                    print("❌ Error: Stored embedding is not a valid list")
                    continue  # Skip this refugee

                # Convert to NumPy array
                stored_embedding = np.array(stored_embedding, dtype=np.float32).flatten()

                # Debugging outputs
                print(f"✅ Final stored embedding shape: {stored_embedding.shape}")
                print(f"✅ First 5 values of stored embedding: {stored_embedding[:5]}")  # Preview

                # Compute similarity
                similarity_score = 1 - cosine(embedding, stored_embedding)
                threshold = 0.6

                if similarity_score >= threshold:
                    return JsonResponse({
                        "success": True,
                        "name": refugee.name,
                        "nationality": refugee.nationality,
                        "age": refugee.age,
                        "institution": refugee.registered_institution.name
                    })

            except Exception as e:
                print(f"❌ Error processing {refugee.full_name}: {e}")
                continue  # Skip and proceed to next refugee

            return JsonResponse({"success": False, "error": "No matching refugee found"})


    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})



##
##
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
