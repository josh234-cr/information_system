
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
        print("Face detected ... now processing")
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB
        frame_resized = cv2.resize(frame_rgb, (160, 160))  # Resize to 160x160

        detected_faces = DeepFace.extract_faces(frame_resized, detector_backend="opencv")
        print("Face extracted ... now embedding")

        if not detected_faces:
            return JsonResponse({"error": "No face detected. Try again in better lighting."}, status=400)

        embeddings = DeepFace.represent(frame_resized, model_name="Facenet", enforce_detection=False)
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
            refugee.embedding_cid = embedding_cid
            refugee.save()
        except Refugee.DoesNotExist:
            return JsonResponse({"error": "Refugee not found in the database."}, status=404)

        with open("ipfs_records.txt", "a") as file:
            file.write(f"Image CID: {image_cid}\nEmbedding CID: {embedding_cid}\n\n")

        return HttpResponseRedirect("/dashboard/")

    except ValueError as e:
        logger.error("Face processing error: %s", str(e))
        return JsonResponse({"error": "Face recognition failed."}, status=400)



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
                        return JsonResponse({
                            "success": True,
                            "message": "Authentication successful via IPFS"
                        })

        return JsonResponse({"success": False, "error": "No matching refugee found in IPFS."})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
