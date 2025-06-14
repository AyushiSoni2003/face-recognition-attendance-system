import face_recognition
import cv2
import os
import datetime


# Load Haar Cascade classifiers
face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml')

def detect_from_webcam(student_id , student_name):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Cannot open webcam")
        return "Webcam error"

    face_saved = False  # To make sure we only save once

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            if not face_saved:
                face_img = frame[y:y+h, x:x+w]
                face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                os.makedirs("captured_images", exist_ok=True)
                name = student_name.replace(" ", "_")
                filename = os.path.join("captured_images", f"{name}_{student_id}.jpg")
                cv2.imwrite(filename, cv2.cvtColor(face_img_rgb, cv2.COLOR_RGB2BGR))  # Save back in BGR for consistency
                print(f"Saved face image: {filename}")
                face_saved = True

        # Show the frame with rectangles (if any)
        cv2.imshow("Detecting Face - Press 'q' to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    return "Face detected and saved" if face_saved else "No face detected"



def mark_attendance():
    # Step 1: Load and encode all known faces
    known_encodings = []
    known_names = []
    known_ids = []

    image_dir = "captured_images"

    for filename in os.listdir(image_dir):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            path = os.path.join(image_dir, filename)
            name_id = os.path.splitext(filename)[0]  # removes the file extension
            
            parts = name_id.rsplit("_", 1)
            if len(parts) == 2:
                student_name = parts[0].replace("_", " ").title()
                student_id = parts[1]
            else:
                student_name = name_id.replace("_", " ").title()
                student_id = "Unknown"

            image = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(student_name)
                known_ids.append(student_id)

    # Step 2: Open webcam and capture one frame
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        return {
            "attendance": "A",
            "student_name": "Unknown",
            "student_id": "Unknown",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": "Could not open webcam"
        }

    print("Camera is on. Detecting face...")
    result = {
        "attendance": "A",
        "student_name": "Unknown",
        "student_id": "Unknown",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Step 3: Detect and encode face(s) in the webcam frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            # Step 4: Compare captured face with known encodings
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            if True in matches:
                matched_idx = matches.index(True)
                name = known_names[matched_idx]
                result = {
                    "attendance": "P",
                    "student_name": known_names[matched_idx],
                    "student_id": known_ids[matched_idx],
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                result["attendance"] = "A"

            video_capture.release()
            cv2.destroyAllWindows()
            return result

        # Show webcam feed (optional)
        cv2.imshow('Recognition - Press Q to quit', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return result
