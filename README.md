# AI Face & Skin Problem Analyzer (Streamlit App)

An AI-powered computer vision web application built with Python, OpenCV, and Streamlit that analyzes facial skin conditions (acne, dark circles, skin redness, texture) and recommends targeted skincare products with prices in Indian Rupees (₹).

---

## 🚀 Features

- **Accurate Computer Vision AI**: CIELAB chromaticity & blob detection algorithm. Smooth, clean skin images will accurately predict high health scores (90-100%) without false positives.
- **Dual Input Modes**:
  - 📷 **Live Webcam Camera**: Real-time snapshot analysis.
  - 📁 **Upload Photo Image**: Upload any image file from your device.
- **Full-Screen Camera UI**: live camera fills the screen, with **Face Scan** and **Choose Photo** buttons below it, recommendations on the right, and a **×** close button (stops the camera and clears results; tap **Start camera** to reopen).
- **Recommendation Panel (right side)**:
  - Displays Facial Health Score & identified skin conditions.
  - Recommends tailored products with prices in **Indian Rupees (₹)** and direct purchase search links.
- **Diagnostic Test Overrides**: Test dropdown mode for easy verification.

---

## 💻 Local Setup & Execution

1. Clone or navigate to the project directory:
   ```bash
   git clone https://github.com/meharnisha3107/AI-smart-mirror.git
   cd AI-smart-mirror
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

The application will automatically launch in your browser at `http://localhost:8501`.

---

## ☁️ Deploying to Streamlit Cloud

To host this website online for free on Streamlit Cloud:

1. Push this folder to a public GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your GitHub account and click **New app**.
4. Select your repository, set **Main file path** to `app.py`, and click **Deploy**!


---

## 📁 Project structure

```
app.py                         # Streamlit entry point (runs the analysis)
skin_ai_model.py               # OpenCV skin analysis (unchanged)
products_db.py                 # Product catalog (unchanged)
components/skin_scanner/       # Full-screen camera + recommendations UI (HTML/JS)
```

> The browser camera needs **HTTPS or localhost** (Streamlit Cloud and `localhost` both work).
