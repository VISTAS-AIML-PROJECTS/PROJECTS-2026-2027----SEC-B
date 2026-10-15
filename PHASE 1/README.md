# AI-Based Skin Allergy Detection and Personalized Healthcare Recommendation System Using Deep Learning

## 📌 Project Overview
DermaAI is an AI-powered skin analysis application designed to predict selected skin conditions from uploaded images. It provides an interactive interface for entering patient details, analyzing skin images, and viewing supporting information.

## ✨ Key Features

### 🧠 AI-Based Skin Condition Prediction
- Uses an EfficientNetV2-B0 deep learning model.
- Predicts four supported classes:
  - Contact Dermatitis
  - Eczema
  - Psoriasis
  - Urticaria

### 🔍 Grad-CAM Visualization
- Uses Gradient-weighted Class Activation Mapping (Grad-CAM) to visualize image regions that influence the model's prediction.
- Helps users understand which areas of the uploaded image contributed to the prediction.
- The visualization is an AI explanation, not proof of a medical diagnosis.

### 🎙️ Voice Input for Symptoms
- Allows users to describe their symptoms using voice input, where supported.
- Helps make patient information entry more convenient.

### 🌐 Tamil Language Support
- Supports Tamil-language interaction for users, where implemented.
- Helps Tamil-speaking users interact with the application more comfortably.

### 📋 Patient Information
- Allows users to enter relevant patient details and describe symptoms.
- Displays the predicted skin condition alongside the analysis.

### 🍎 Automatic Recommendations
- Uses an Ollama-based recommendation engine to generate suggestions related to:
  - Food
  - Clothing
  - Home-care remedies
- Suggestions should be treated as general information and not as a substitute for professional medical advice.

### 📄 Downloadable PDF Patient Report
- Generates a downloadable PDF report.
- Can include patient details, the uploaded skin image, the predicted condition, and selected recommendations, depending on the report configuration.

## 🛠️ Technologies Used
- Python
- Streamlit
- TensorFlow / Keras
- EfficientNetV2-B0
- Grad-CAM
- Ollama
- ReportLab
- Pillow
- NumPy
- Scikit-learn

## 🚀 How to Run the Project

1. Install Python.
2. Install the required packages from `requirements.txt`.
3. Start Ollama and ensure the required model is available if automatic recommendations are enabled.
4. Open a terminal in the project directory.
5. Run the application:

```bash
streamlit run app.py

## ⚠️ Disclaimer
DermaAI is an educational project and is not a clinically validated diagnostic system. Its predictions may be incorrect. Consult a qualified dermatologist for medical assessment and treatment.

## 👨‍💻 Project Information
**Project Name:** DermaAI – AI-Based Skin Allergy Detection System

**Domain:** Artificial Intelligence, Deep Learning, and Healthcare Applications
