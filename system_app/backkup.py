# authenticate using facial recognition
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
                        print("Error: 'embedding' key not found in the stored data")
                        continue  # Skip this refugee

                else:
                    print("Error: Stored embedding is not a valid list")
                    continue  # Skip this refugee

                # Convert to NumPy array
                stored_embedding = np.array(stored_embedding, dtype=np.float32).flatten()

                '''
                # Debugging outputs
                print(f"Final stored embedding shape: {stored_embedding.shape}")
                print(f"First 5 values of stored embedding: {stored_embedding[:5]}")  # Preview
                '''

                # Compute similarity
                similarity_score = 1 - cosine(embedding, stored_embedding)
                threshold = 0.5

                print(f"Similarity Score: {similarity_score}")

                if similarity_score >= threshold:
                    return JsonResponse({
                        "success": True,
                        "name": refugee.full_name,
                        "nationality": refugee.nationality,
                        "status": refugee.refugee_status,
                        "dob": refugee.date_of_birth
                    })

            except Exception as e:
                print(f"Error processing {refugee.full_name}: {e}")
                continue  # Skip and proceed to next refugee

            return JsonResponse({"success": False, "error": "No matching refugee found"})


    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})