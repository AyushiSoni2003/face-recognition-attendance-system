import face_recognition
import cv2
import os
import datetime
from PIL import Image
import numpy as np

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
                if face_img.size == 0:
                    print("Face image is empty. Skipping save.")
                    continue

                # Convert to RGB (OpenCV loads in BGR)
                face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)

                # Save using PIL for guaranteed format
                pil_image = Image.fromarray(face_img_rgb)
                os.makedirs("captured_images", exist_ok=True)
                name = student_name.replace(" ", "_")
                filename = os.path.join("captured_images", f"{name}_{student_id}.jpg")
                pil_image.save(filename, format="JPEG")
                print(f"✅ Saved face image: {filename}")
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

            try:
                # Load with Pillow and convert to RGB for safety
                pil_img = Image.open(path).convert("RGB")
                image = np.array(pil_img)

                # Now encode the face
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_encodings.append(encodings[0])
                    known_names.append(student_name)
                    known_ids.append(student_id)
            except Exception as e:
                print(f"❌ Failed to process {filename}: {e}")
                # need to close camera here , in case of exception
                continue

     
    # Step 2: Open webcam and capture one frame
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        return {
            "Attendance": "Absent",
            "Student Name": "Unknown",
            "Student Id": "Unknown",
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": "Could not open webcam"
        }

    print("Camera is on. Detecting face...")
    result = {
        "Attendance": "Absent",
        "Student Name": "Unknown",
        "Student Id": "Unknown",
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    while True:
        ret, frame = video_capture.read()
        if not ret or frame is None:
            print("Error: Frame not read from webcam.")
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Check for valid frame shape before converting
        if small_frame is None or small_frame.ndim != 3 or small_frame.shape[2] != 3:
            print("Error: Frame is not a valid RGB image.")
            break

        # Convert the frame from BGR to RGB
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Safety check for dtype
        if rgb_small_frame.dtype != 'uint8':
            print("Error: Frame is not uint8 type.")
            break

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
                    "Attendance": "Present",
                    "Student Name": known_names[matched_idx],
                    "Student Id": known_ids[matched_idx],
                    "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                result["Attendance"] = "Absent"

            video_capture.release()
            cv2.destroyAllWindows()
            return result

        # Show webcam feed (optional)
        SHOW_FEED = False
        if SHOW_FEED:
            cv2.imshow('Recognition - Press Q to quit', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    video_capture.release()
    cv2.destroyAllWindows()
    return result

