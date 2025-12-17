# Real-time Yoga Pose Detection using Flask, OpenCV, and MediaPipe

This project utilizes Flask, OpenCV, and MediaPipe to power a real-time yoga pose detection application. By using a webcam feed, it dynamically classifies yoga poses using MediaPipe, while Flask enables easy web deployment. OpenCV manages video streaming and image processing, creating an interactive platform for yoga enthusiasts to practice effectively.

# Installation

1. Clone the repository.

2. Install the required dependencies:

   ```bash
   pip install Flask opencv-python mediapipe
   ```

3. Run the Flask application:

   ```bash
   python app.py
   ```

4. Open your web browser and navigate to `http://localhost:5000` to access the application.

# Usage

1. Ensure your webcam is connected and working properly.

2. Open the application in your web browser.

3. Follow the on-screen instructions to position yourself within the webcam frame.

4. The application will dynamically classify your yoga poses in real-time using MediaPipe.

5. Use this feedback to adjust and improve your yoga poses.