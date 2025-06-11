import cv2 
import os

# Load Haar Cascade classifiers
face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml')

def detect_from_webcam(student_id):
    # Start video capture (0 = default camera)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Cannot open webcam")
        return "Webcam error"

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) > 0:
            # Take the first face detected
            (x, y, w, h) = faces[0]
            # After detecting a face
            face_img = frame[y:y+h, x:x+w] # crop the face

            filename = os.path.join("captured_images", f"student_{student_id}.jpg")
            cv2.imwrite(filename, face_img)
            print(f"Saved face image: {filename}")

            cap.release()
            cv2.destroyAllWindows()
            return "Face detected and saved"

        # Show the frame
        cv2.imshow("Detecting Face - Press 'q' to quit", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    
    # Release resourcesq
    cap.release()
    cv2.destroyAllWindows()
    return "No face detected"

