# DermaAI – AI-Based Skin Allergy Detection

## Project Overview
DermaAI is an AI-powered application that analyzes uploaded skin images and predicts one of four supported skin conditions.

## Features
-**Skin Condition Prediction:**Uses EfficientNetV2-B0 to classify supported skin conditions.
- **Grad-CAM Visualization:** Highlights image regions that influence the model's prediction.
- **Voice Input:** Allows users to describe their symptoms using voice input, where supported.
- **Tamil Support:** Helps Tamil-speaking users interact with the application, where implemented.
- **Automatic Recommendations:** Generates food, clothing, and home-care suggestions.
- **PDF Report:** Allows users to download a patient report containing selected patient details and AI analysis.

## Supported Conditions
- Contact Dermatitis
- Eczema
- Psoriasis
- Urticaria

## Technologies Used
Python, Streamlit, TensorFlow/Keras, EfficientNetV2-B0, Grad-CAM, Ollama, and ReportLab.

## How to Run
Install the required dependencies and run:

```bash
streamlit run app.py


## Disclaimer
This is an educational project, not a clinically validated diagnostic system. Predictions may be incorrect and should not replace professional medical assessment.
