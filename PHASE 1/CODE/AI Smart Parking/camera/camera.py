import cv2


def start_camera():

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open laptop camera.")
        return

    print("Camera started successfully.")
    print("Press Q to stop the camera.")

    while True:

        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read camera frame.")
            break

        # Display the camera frame
        cv2.imshow("AI Smart Parking - Camera", frame)

        # Press Q to exit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    start_camera()