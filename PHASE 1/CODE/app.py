import streamlit as st
import numpy as np
import tensorflow as tf
import speech_recognition as sr
import requests

from PIL import Image
from io import BytesIO
from datetime import datetime
from urllib.parse import quote
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation

from severity_engine import calculate_severity
from automatic_recommendation_engine import get_automatic_recommendations

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="DermaAI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SETTINGS
# ============================================================

MODEL_PATH = "skin_allergy_efficientnetv2b0.keras"
IMG_SIZE = (224, 224)

CLASS_NAMES = [
    "Contact_dermatitis",
    "Eczema",
    "Psoriasis",
    "Urticaria"
]


# ============================================================
# LANGUAGE
# ============================================================

if "language" not in st.session_state:
    st.session_state.language = "English"

language = st.radio(
    "🌐 Choose Your Language / உங்கள் மொழியை தேர்வு செய்யவும்",
    ["English", "தமிழ்"],
    horizontal=True
)

st.session_state.language = language

if language == "தமிழ்":
    TEXT = {
        "patient_details": "👤 நோயாளி விவரங்கள்",
        "name": "பெயர்",
        "age": "வயது",
        "gender": "பாலினம்",
        "uploaded_image": "🖼️ பதிவேற்றிய படம்",
        "ai_analysis": "🤖 AI ஆய்வு",
        "predicted_condition": "கணிக்கப்பட்ட தோல் நிலை",
        "confidence": "கணிப்பு நம்பகத்தன்மை",
        "high_confidence": "அதிக நம்பகத்தன்மை கொண்ட கணிப்பு",
        "moderate_confidence": "மிதமான நம்பகத்தன்மை கொண்ட கணிப்பு",
        "low_confidence": "குறைந்த நம்பகத்தன்மை கொண்ட கணிப்பு",
        "original_image": "அசல் படம்",
        "ai_focus": "AI கவனம் செலுத்தும் பகுதி",
        "download_report": "📄 நோயாளி அறிக்கையை பதிவிறக்கவும்"
    }
else:
    TEXT = {
        "patient_details": "👤 Patient Details",
        "name": "Name",
        "age": "Age",
        "gender": "Gender",
        "uploaded_image": "🖼️ Uploaded Image",
        "ai_analysis": "🤖 AI Analysis",
        "predicted_condition": "Predicted Condition",
        "confidence": "Prediction Confidence",
        "high_confidence": "High-confidence prediction",
        "moderate_confidence": "Moderate-confidence prediction",
        "low_confidence": "Low-confidence prediction",
        "original_image": "Original Image",
        "ai_focus": "AI Focus Area",
        "download_report": "📄 Download Patient Report"
    }


# ============================================================
# GRAD-CAM
# ============================================================

def make_gradcam_heatmap(img_array, model, pred_index=None):
    """
    Generate a Grad-CAM heatmap directly from the EfficientNetV2-B0
    feature output. This avoids disconnected nested-model graphs.
    """
    import tensorflow as tf

    base_model = model.get_layer("efficientnetv2-b0")
    gap_layer = model.get_layer("global_average_pooling2d")
    dense_layer = model.get_layer("dense")

    with tf.GradientTape() as tape:

        # EfficientNetV2-B0 final 4-D feature maps
        feature_maps = base_model(
            img_array,
            training=False
        )

        if len(feature_maps.shape) != 4:
            raise ValueError(
                f"EfficientNet feature output is not 4-D: {feature_maps.shape}"
            )

        # Original classifier head
        pooled = gap_layer(feature_maps)
        predictions = dense_layer(pooled)

        if pred_index is None:
            pred_index = tf.argmax(predictions[0])

        class_score = predictions[0, pred_index]

    # Gradients of the selected class with respect to feature maps
    grads = tape.gradient(
        class_score,
        feature_maps
    )

    if grads is None:
        raise ValueError(
            "Gradients could not be calculated for Grad-CAM."
        )

    # Global-average-pool the gradients
    pooled_grads = tf.reduce_mean(
        grads,
        axis=(1, 2)
    )

    feature_maps = feature_maps[0]
    pooled_grads = pooled_grads[0]

    # Weighted combination of feature maps
    heatmap = tf.reduce_sum(
        feature_maps * pooled_grads,
        axis=-1
    )

    # Keep positive activations only
    heatmap = tf.maximum(
        heatmap,
        0
    )

    # Normalize to 0-1
    max_value = tf.reduce_max(heatmap)

    heatmap = tf.where(
        max_value > 0,
        heatmap / max_value,
        tf.zeros_like(heatmap)
    )

    return heatmap.numpy()


def create_gradcam_image(original_image, heatmap):
    """
    Create the colored Grad-CAM overlay.

    COLORMAP_JET gives the requested:
    blue -> green -> yellow -> red visualization.
    """
    import cv2
    import numpy as np
    from PIL import Image

    if isinstance(original_image, Image.Image):
        original = np.array(
            original_image.convert("RGB")
        )
    else:
        original = np.array(original_image)

    original = np.uint8(
        np.clip(original, 0, 255)
    )

    # Convert heatmap to 0-255
    heatmap_uint8 = np.uint8(
        np.clip(heatmap, 0, 1) * 255
    )

    # Resize heatmap to original image dimensions
    heatmap_uint8 = cv2.resize(
        heatmap_uint8,
        (
            original.shape[1],
            original.shape[0]
        ),
        interpolation=cv2.INTER_LINEAR
    )

    # Blue -> Green -> Yellow -> Red
    colored_heatmap = cv2.applyColorMap(
        heatmap_uint8,
        cv2.COLORMAP_JET
    )

    # OpenCV BGR -> RGB
    colored_heatmap = cv2.cvtColor(
        colored_heatmap,
        cv2.COLOR_BGR2RGB
    )

    # Overlay heatmap on original image
    overlay = cv2.addWeighted(
        original,
        0.55,
        colored_heatmap,
        0.45,
        0
    )

    return Image.fromarray(
        np.uint8(overlay)
    )


# ============================================================
# PDF REPORT
# ============================================================

def create_patient_report(
    patient_details,
    predicted_condition,
    confidence,
    uploaded_image_bytes,
    language="English"
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]

    story = []

    if language == "தமிழ்":
        report_title = "நோயாளியின் தோல் ஒவ்வாமை பகுப்பாய்வு அறிக்கை"
        patient_details_title = "நோயாளியின் விவரங்கள்"
        name_label = "பெயர்"
        age_label = "வயது"
        gender_label = "பாலினம்"
        contact_label = "தொடர்பு எண்"
        previous_allergy_label = "முந்தைய தோல் ஒவ்வாமை"
        symptoms_label = "தற்போதைய அறிகுறிகள்"
        ai_analysis_title = "AI பகுப்பாய்வு"
        condition_label = "கணிக்கப்பட்ட நிலை"
        confidence_label = "கணிப்பு நம்பகத்தன்மை"
    else:
        report_title = "PATIENT SKIN ALLERGY ANALYSIS REPORT"
        patient_details_title = "Patient Details"
        name_label = "Name"
        age_label = "Age"
        gender_label = "Gender"
        contact_label = "Contact Number"
        previous_allergy_label = "Previous Skin Allergy"
        symptoms_label = "Current Symptoms"
        ai_analysis_title = "AI Analysis"
        condition_label = "Predicted Condition"
        confidence_label = "Prediction Confidence"

    story.append(
        Paragraph(
            report_title,
            title_style
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            patient_details_title,
            heading_style
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"<b>{name_label}:</b> "
            f"{patient_details.get('name', '')}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>{age_label}:</b> "
            f"{patient_details.get('age', '')}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>{gender_label}:</b> "
            f"{patient_details.get('gender', '')}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>{contact_label}:</b> "
            f"{patient_details.get('phone', '')}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>{previous_allergy_label}:</b> "
            f"{patient_details.get('previous_allergy', '')}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>{symptoms_label}:</b> "
            f"{patient_details.get('symptoms', '')}",
            normal_style
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            ai_analysis_title,
            heading_style
        )
    )

    story.append(Spacer(1, 10))

    try:
        image_data = BytesIO(uploaded_image_bytes)

        report_image = ReportLabImage(
            image_data,
            width=3.5 * inch,
            height=3.5 * inch
        )

        story.append(report_image)
        story.append(Spacer(1, 15))

    except Exception:
        pass

    story.append(
        Paragraph(
            f"<b>{condition_label}:</b> "
            f"{predicted_condition}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>{confidence_label}:</b> "
            f"{confidence:.2f}%",
            normal_style
        )
    )

    prediction_time = datetime.now().strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )

    story.append(
        Paragraph(
            f"<b>Date &amp; Time of Prediction:</b> "
            f"{prediction_time}",
            normal_style
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "This report is generated by the AI-based skin "
            "allergy analysis system and is intended for "
            "informational purposes.",
            normal_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f7f9fc;
    }

    .hero-title {
        font-size: 42px;
        font-weight: 800;
        color: #16324F;
        margin-bottom: 5px;
    }

    .hero-subtitle {
        font-size: 17px;
        color: #667085;
        margin-bottom: 25px;
    }

    .prediction-card {
        background: linear-gradient(
            135deg,
            #e9f8f3,
            #f4fbff
        );
        border-radius: 20px;
        padding: 25px;
        border: 1px solid #d5eee5;
        margin-top: 15px;
    }

    .prediction-label {
        color: #667085;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
    }

    .prediction-name {
        color: #16324F !important;
        font-size: 30px;
        font-weight: 800;
        margin-top: 5px;
    }

    .care-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #e4e7ec;
    }

    .care-title {
        font-size: 18px;
        font-weight: 700;
        color: #1d2939;
    }

    .precaution {
        background: #fff8e6;
        border-radius: 10px;
        padding: 10px;
        color: #7a5b00;
        font-size: 14px;
        margin-top: 12px;
    }

    .info-card {
        background: white;
        padding: 18px;
        border-radius: 15px;
        border: 1px solid #e4e7ec;
        text-align: center;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOAD MODEL
# ============================================================

@st.cache_resource
def load_model():
    return tf.keras.models.load_model(MODEL_PATH)


try:
    model = load_model()
except Exception as e:
    st.error(
        f"Could not load the model: {e}"
    )
    st.stop()


# ============================================================
# PATIENT DETAILS
# ============================================================

st.markdown("---")

st.header(TEXT["patient_details"])

st.write(
    "Enter the patient's details before starting the AI analysis."
    if language == "English"
    else "AI பகுப்பாய்வை தொடங்குவதற்கு முன் நோயாளியின் விவரங்களை உள்ளிடவும்."
)

col1, col2 = st.columns(2)

with col1:

    patient_name = st.text_input(
        TEXT["name"],
        placeholder=(
            "Enter patient name"
            if language == "English"
            else "நோயாளியின் பெயரை உள்ளிடவும்"
        )
    )

    patient_age = st.number_input(
        TEXT["age"],
        min_value=1,
        max_value=120,
        value=18,
        step=1
    )

    patient_gender = st.selectbox(
        TEXT["gender"],
        (
            [
                "Select",
                "Male",
                "Female",
                "Other",
                "Prefer not to say"
            ]
            if language == "English"
            else [
                "தேர்வு செய்யவும்",
                "ஆண்",
                "பெண்",
                "மற்றவை",
                "குறிப்பிட விரும்பவில்லை"
            ]
        )
    )

with col2:

    patient_phone = st.text_input(
        "Contact Number"
        if language == "English"
        else "தொடர்பு எண்",
        placeholder=(
            "Enter contact number"
            if language == "English"
            else "தொடர்பு எண்ணை உள்ளிடவும்"
        )
    )

    previous_allergy = st.selectbox(
        "Previous Skin Allergy"
        if language == "English"
        else "முந்தைய தோல் ஒவ்வாமை",
        (
            ["Select", "Yes", "No", "Not sure"]
            if language == "English"
            else [
                "தேர்வு செய்யவும்",
                "ஆம்",
                "இல்லை",
                "தெரியவில்லை"
            ]
        )
         )

patient_symptoms = st.text_area(
    "Current Symptoms"
    if language == "English"
    else "தற்போதைய அறிகுறிகள்",
    placeholder=(
        "Describe current symptoms, such as itching, redness, swelling, etc."
        if language == "English"
        else "அரிப்பு, சிவத்தல், வீக்கம் போன்ற தற்போதைய அறிகுறிகளை விவரிக்கவும்."
    )
)


# ============================================================
# SEVERITY INPUT
# ============================================================

st.subheader(
    "🩹 Symptom Severity Assessment"
    if language == "English"
    else "🩹 அறிகுறிகளின் தீவிரத்தன்மை மதிப்பீடு"
)

itching_level = st.select_slider(
    "Itching intensity"
    if language == "English"
    else "அரிப்பு தீவிரம்",
    options=["None", "Mild", "Moderate", "Severe"],
    value="Mild"
)

redness_level = st.select_slider(
    "Redness / skin irritation"
    if language == "English"
    else "சிவத்தல் / தோல் எரிச்சல்",
    options=["None", "Mild", "Moderate", "Severe"],
    value="Mild"
)

swelling_level = st.select_slider(
    "Swelling"
    if language == "English"
    else "வீக்கம்",
    options=["None", "Mild", "Moderate", "Severe"],
    value="None"
)

affected_area = st.select_slider(
    "Approximate affected skin area"
    if language == "English"
    else "பாதிக்கப்பட்ட தோல் பகுதியின் தோராயமான அளவு",
    options=["Small", "Moderate", "Large", "Very Large"],
    value="Small"
)

pain_level = st.select_slider(
    "Pain / discomfort"
    if language == "English"
    else "வலி / அசௌகரியம்",
    options=["None", "Mild", "Moderate", "Severe"],
    value="None"
)

skin_damage = st.selectbox(
    "Open skin / blistering / oozing"
    if language == "English"
    else "திறந்த தோல் / கொப்புளம் / திரவம் வெளியேறுதல்",
    ["None", "Mild", "Present"]
)


# ============================================================
# SAVE PATIENT DETAILS
# ============================================================

if st.button("💾 Save Patient Details"):

    if not patient_name.strip():

        st.warning(
            "Please enter the patient's name."
            if language == "English"
            else "நோயாளியின் பெயரை உள்ளிடவும்."
        )

    elif patient_gender in ["Select", "தேர்வு செய்யவும்"]:

        st.warning(
            "Please select the patient's gender."
            if language == "English"
            else "நோயாளியின் பாலினத்தைத் தேர்வு செய்யவும்."
        )

    elif previous_allergy in ["Select", "தேர்வு செய்யவும்"]:

        st.warning(
            "Please select whether the patient had a previous skin allergy."
            if language == "English"
            else "முந்தைய தோல் ஒவ்வாமை பற்றிய தகவலைத் தேர்வு செய்யவும்."
        )

    else:

        st.session_state["patient_details"] = {
            "name": patient_name.strip(),
            "age": patient_age,
            "gender": patient_gender,
            "phone": patient_phone.strip(),
            "previous_allergy": previous_allergy,
            "symptoms": patient_symptoms.strip()
        }

        st.success(
            "✅ Patient details saved successfully!"
            if language == "English"
            else "✅ நோயாளியின் விவரங்கள் வெற்றிகரமாக சேமிக்கப்பட்டன!"
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🩺 AI BASED SKIN ALLERGY DETECTION"
    )

    st.write(
        "Contact Dermatitis, Eczema, Psoriasis and Urticaria"
    )

    st.divider()

    st.markdown("### Supported Conditions")

    st.markdown(
        """
        🟢 Contact Dermatitis  
        🔵 Eczema  
        🟣 Psoriasis  
        🟠 Urticaria
        """
    )

    st.divider()

    st.markdown("### How it works")

    st.markdown(
        """
        **1.** Upload a skin image  
        **2.** AI analyzes the image  
        **3.** Condition is predicted  
        **4.** Supportive-care information is retrieved
        """
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="hero-title">🩺 AI BASED SKIN ALLERGY DETECTION</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="hero-subtitle">'
    'AI-powered skin condition detection with personalized supportive-care information'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# TOP INFORMATION CARDS
# NOTE: MODEL ACCURACY IS INTENTIONALLY NOT DISPLAYED.
# ============================================================

info1, info2 = st.columns(2)

with info1:

    st.markdown(
        '<div class="info-card">'
        '<h3>🤖 AI Model</h3>'
        '<p>EfficientNetV2-B0</p>'
        '</div>',
        unsafe_allow_html=True
    )

with info2:

    st.markdown(
        '<div class="info-card">'
        '<h3>🔬 Conditions</h3>'
        '<p>4 Skin Conditions</p>'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# IMAGE UPLOAD
# ============================================================

st.write("")

st.markdown(
    "### 📤 Upload Skin Image"
    if language == "English"
    else "### 📤 தோல் படத்தை பதிவேற்றவும்"
)

uploaded_file = st.file_uploader(
    "Choose a JPG, JPEG or PNG image"
    if language == "English"
    else "JPG, JPEG அல்லது PNG படத்தைத் தேர்ந்தெடுக்கவும்",
    type=["jpg", "jpeg", "png"],
    help=(
        "Upload a clear image of the affected skin area."
        if language == "English"
        else "பாதிக்கப்பட்ட தோல் பகுதியின் தெளிவான படத்தை பதிவேற்றவும்."
    )
)


# ============================================================
# IMAGE + MODEL PREDICTION
# ============================================================

uploaded_image_bytes = None

if uploaded_file is not None:

    try:

        # Read the upload ONCE and keep our own bytes.
        uploaded_image_bytes = uploaded_file.getvalue()

        if not uploaded_image_bytes:
            st.error(
                "The uploaded image is empty. Please choose another image."
            )
            st.stop()

        image = Image.open(
            BytesIO(uploaded_image_bytes)
        ).convert("RGB")

    except Exception as e:

        st.error(
            f"Could not open the uploaded image: {e}"
            if language == "English"
            else f"பதிவேற்றிய படத்தைத் திறக்க முடியவில்லை: {e}"
        )
        st.stop()

    left, right = st.columns([1.1, 1])

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    with left:

        st.markdown(
            f"#### {TEXT['uploaded_image']}"
        )

        st.image(
            image,
            use_container_width=True
        )

    # --------------------------------------------------------
    # PREPARE IMAGE ARRAY
    # --------------------------------------------------------

    image_resized = image.resize(IMG_SIZE)

    image_array = np.asarray(
        image_resized,
        dtype=np.float32
    )

    image_array = np.expand_dims(
        image_array,
        axis=0
    )

    # --------------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------------

    try:

        predictions = model.predict(
            image_array,
            verbose=0
        )

        predicted_index = int(
            np.argmax(predictions[0])
        )

        confidence = float(
            predictions[0][predicted_index]
        )

        predicted_class = CLASS_NAMES[
            predicted_index
        ]
        

    except Exception as e:

        st.error(
            f"Model prediction failed: {e}"
            if language == "English"
            else f"AI கணிப்பு தோல்வியடைந்தது: {e}"
        )

        predicted_class = None
        confidence = 0.0

    # --------------------------------------------------------
    # AI RESULT
    # --------------------------------------------------------

    if predicted_class is not None:

        with right:

            st.markdown(
                f"#### {TEXT['ai_analysis']}"
            )

            st.markdown(
                f"""
                <div class="prediction-card">
                    <div class="prediction-label">
                        {TEXT['predicted_condition']}
                    </div>
                    <div class="prediction-name">
                        {predicted_class.replace('_', ' ')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write("")

            st.metric(
                TEXT["confidence"],
                f"{confidence * 100:.2f}%"
            )

            st.progress(
                min(confidence, 1.0)
            )

            if confidence >= 0.85:

                st.success(
                    TEXT["high_confidence"]
                )

            elif confidence >= 0.60:

                st.warning(
                    TEXT["moderate_confidence"]
                )

            else:

                st.error(
                    TEXT["low_confidence"]
                )

    # ========================================================
    # SEVERITY ASSESSMENT
    # ========================================================

    try:

        severity, severity_score = calculate_severity(
            itching_level,
            redness_level,
            swelling_level,
            affected_area,
            pain_level,
            skin_damage
        )

    except Exception as e:

        severity = None
        severity_score = None

        st.warning(
            f"Severity assessment could not be completed: {e}"
            if language == "English"
            else f"தீவிரத்தன்மை மதிப்பீட்டை முடிக்க முடியவில்லை: {e}"
        )

    # ========================================================
    # GRAD-CAM
    # ========================================================

    if predicted_class is not None:

        gradcam_image = None

        try:

            heatmap = make_gradcam_heatmap(
                image_array,
                model,
                pred_index=predicted_index
            )

            gradcam_image = create_gradcam_image(
                image,
                heatmap
            )

        except Exception as e:

            gradcam_image = None

            st.warning(
                f"Grad-CAM could not be generated: {e}"
                if language == "English"
                else f"Grad-CAM உருவாக்க முடியவில்லை: {e}"
            )

        st.divider()

        st.markdown(
            "### 🖐️ AI Focus Area — Grad-CAM"
            if language == "English"
            else "### 🖐️ AI கவனம் செலுத்தும் பகுதி — Grad-CAM"
        )

        if gradcam_image is not None:

            gradcam_col1, gradcam_col2 = st.columns(2)

            with gradcam_col1:

                st.caption(
                    TEXT["original_image"]
                )

                st.image(
                    image,
                    use_container_width=True
                )

            with gradcam_col2:

                st.caption(
                    TEXT["ai_focus"]
                )

                st.image(
                    gradcam_image,
                    use_container_width=True
                )

        else:

            st.warning(
                "AI Focus Area could not be generated."
                if language == "English"
                else "AI கவனம் செலுத்தும் பகுதியை உருவாக்க முடியவில்லை."
            )


    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    if predicted_class is not None:

        st.write("")
        st.divider()

        st.markdown(
            "### 🌿 Personalized Recommendations"
            if language == "English"
            else "### 🌿 தனிப்பயனாக்கப்பட்ட பரிந்துரைகள்"
        )

        st.caption(
            "Recommendations are generated according to the AI-predicted condition."
            if language == "English"
            else "AI கணித்த நிலைக்கு ஏற்ப பரிந்துரைகள் உருவாக்கப்படுகின்றன."
        )

        with st.spinner(
            "Generating condition-specific recommendations..."
            if language == "English"
            else "நிலைக்கு ஏற்ப பரிந்துரைகள் உருவாக்கப்படுகின்றன..."
        ):

            try:

                automatic_data = get_automatic_recommendations(
                    predicted_class
                )

                if not isinstance(automatic_data, dict):
                    automatic_data = {}

            except Exception as e:

                st.warning(
                    f"Recommendation generation failed: {e}"
                    if language == "English"
                    else f"பரிந்துரைகள் உருவாக்குவதில் பிழை: {e}"
                )

                automatic_data = {}

        food_recommendations = automatic_data.get(
            "food",
            []
        )

        clothing_recommendations = automatic_data.get(
            "clothing",
            []
        )

        home_remedies = automatic_data.get(
            "home_remedy",
            []
        )

        food_tab, clothing_tab, care_tab = st.tabs(
            [
                "🍎 Food",
                "👕 Clothing",
                "🌿 Supportive Care"
            ]
        )

        # ----------------------------------------------------
        # FOOD
        # ----------------------------------------------------

        with food_tab:

            if food_recommendations:

                for i, recommendation in enumerate(
                    food_recommendations,
                    start=1
                ):

                    if isinstance(
                        recommendation,
                        dict
                    ):
                        text = recommendation.get(
                            "recommendation",
                            recommendation.get(
                                "text",
                                str(recommendation)
                            )
                        )
                    else:
                        text = str(
                            recommendation
                        )

                    st.markdown(
                        f"""
                        <div class="care-card">
                            <div class="care-title">
                                🍎 Food Recommendation {i}
                            </div>
                            <p>{text}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:

                st.info(
                    "No food recommendations were generated."
                    if language == "English"
                    else "உணவு பரிந்துரைகள் எதுவும் உருவாக்கப்படவில்லை."
                )

        # ----------------------------------------------------
        # CLOTHING
        # ----------------------------------------------------

        with clothing_tab:

            if clothing_recommendations:

                for i, recommendation in enumerate(
                    clothing_recommendations,
                    start=1
                ):

                    if isinstance(
                        recommendation,
                        dict
                    ):
                        text = recommendation.get(
                            "recommendation",
                            recommendation.get(
                                "text",
                                str(recommendation)
                            )
                        )
                    else:
                        text = str(
                            recommendation
                        )

                    st.markdown(
                        f"""
                        <div class="care-card">
                            <div class="care-title">
                                👕 Clothing Recommendation {i}
                            </div>
                            <p>{text}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:

                st.info(
                    "No clothing recommendations were generated."
                    if language == "English"
                    else "ஆடை பரிந்துரைகள் எதுவும் உருவாக்கப்படவில்லை."
                )

        # ----------------------------------------------------
        # SUPPORTIVE CARE
        # ----------------------------------------------------

        with care_tab:

            if home_remedies:

                for i, recommendation in enumerate(
                    home_remedies,
                    start=1
                ):

                    if isinstance(
                        recommendation,
                        dict
                    ):

                        title = recommendation.get(
                            "care_option",
                            recommendation.get(
                                "title",
                                f"Supportive Care {i}"
                            )
                        )

                        text = recommendation.get(
                            "recommendation",
                            recommendation.get(
                                "text",
                                recommendation.get(
                                    "description",
                                    ""
                                )
                            )
                        )

                        precaution = recommendation.get(
                            "precautions",
                            ""
                        )

                    else:

                        title = f"Supportive Care {i}"
                        text = str(
                            recommendation
                        )
                        precaution = ""

                    precaution_html = ""

                    if precaution:

                        precaution_html = (
                            f"""
                            <div class="precaution">
                                ⚠️ <b>Precaution:</b>
                                {precaution}
                            </div>
                            """
                        )

                    st.markdown(
                        f"""
                        <div class="care-card">
                            <div class="care-title">
                                🌿 {title}
                            </div>
                            <p>{text}</p>
                            {precaution_html}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:

                st.info(
                    "No supportive-care recommendations were generated."
                    if language == "English"
                    else "ஆதரவு பராமரிப்பு பரிந்துரைகள் எதுவும் உருவாக்கப்படவில்லை."
                )


# ============================================================
# VOICE SYMPTOM INPUT
# ============================================================

st.divider()

st.markdown(
    "### 🎤 Tell Us Your Symptoms"
    if language == "English"
    else "### 🎤 உங்கள் அறிகுறிகளைச் சொல்லுங்கள்"
)

st.write(
    "Allow microphone access and speak naturally in English, Tamil, or Tamil-English."
    if language == "English"
    else "மைக்ரோஃபோன் அனுமதியை வழங்கி, தமிழ், ஆங்கிலம் அல்லது தமிழ்-ஆங்கிலத்தில் இயல்பாகப் பேசுங்கள்."
)

if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

if st.button(
    "🎙️ Start Recording"
    if language == "English"
    else "🎙️ பதிவைத் தொடங்கவும்"
):

    recognizer = sr.Recognizer()

    try:

        with sr.Microphone() as source:

            st.info(
                "🎤 Listening... Please speak now."
                if language == "English"
                else "🎤 கேட்கிறது... இப்போது பேசுங்கள்."
            )

            recognizer.adjust_for_ambient_noise(
                source,
                duration=1
            )

            audio = recognizer.listen(
                source,
                timeout=10,
                phrase_time_limit=30
            )

        st.info(
            "🔄 Converting your voice to text..."
            if language == "English"
            else "🔄 உங்கள் குரலை எழுத்தாக மாற்றுகிறது..."
        )

        try:

            text = recognizer.recognize_google(
                audio,
                language="ta-IN"
            )

            st.session_state.voice_text = text

        except sr.UnknownValueError:

            text = recognizer.recognize_google(
                audio,
                language="en-IN"
            )

            st.session_state.voice_text = text

        st.success(
            "✅ Voice captured successfully!"
            if language == "English"
            else "✅ குரல் வெற்றிகரமாக பதிவு செய்யப்பட்டது!"
        )

    except sr.WaitTimeoutError:

        st.warning(
            "No speech detected. Please try again."
            if language == "English"
            else "பேச்சு எதுவும் கண்டறியப்படவில்லை. மீண்டும் முயற்சிக்கவும்."
        )

    except sr.UnknownValueError:

        st.warning(
            "Sorry, I could not understand the speech."
            if language == "English"
            else "மன்னிக்கவும், உங்கள் பேச்சைப் புரிந்துகொள்ள முடியவில்லை."
        )

    except sr.RequestError as e:

        st.error(
            f"Speech recognition service error: {e}"
            if language == "English"
            else f"குரல் அறிதல் சேவை பிழை: {e}"
        )

    except Exception as e:

        st.error(
            f"Microphone error: {e}"
            if language == "English"
            else f"மைக்ரோஃபோன் பிழை: {e}"
        )


if st.session_state.voice_text:

    st.markdown(
        "#### 📝 Recognized Symptoms"
        if language == "English"
        else "#### 📝 கண்டறியப்பட்ட அறிகுறிகள்"
    )

    st.text_area(
        "Your spoken symptoms"
        if language == "English"
        else "நீங்கள் பேசிய அறிகுறிகள்",
        value=st.session_state.voice_text,
        height=100
    )


# ============================================================
# NEARBY DERMATOLOGISTS
# ============================================================

st.markdown("---")

st.markdown(
    "## 🩺 Find Nearby Dermatologists"
    if language == "English"
    else "## 🩺 அருகிலுள்ள தோல் மருத்துவர்களைக் கண்டறியவும்"
)

st.write(
    "Use your current location to find dermatologists and skin clinics within 20 km."
    if language == "English"
    else "உங்கள் தற்போதைய இருப்பிடத்தைப் பயன்படுத்தி 20 கி.மீ.க்குள் உள்ள தோல் மருத்துவர்கள் மற்றும் தோல் மருத்துவமனைகளைக் கண்டறியவும்."
)

location = streamlit_geolocation()

# IMPORTANT:
# Always initialize clinics before any condition uses it.
clinics = []

find_doctors = st.button(
    "📍 Find Nearby Dermatologists"
    if language == "English"
    else "📍 அருகிலுள்ள தோல் மருத்துவரைக் கண்டறியவும்"
)


def search_photon(
    search_text,
    lat,
    lon
):

    url = "https://photon.komoot.io/api/"

    params = {
        "q": search_text,
        "lat": lat,
        "lon": lon,
        "limit": 20
    }

    headers = {
        "User-Agent":
            "DermaAI-Educational-Project/1.0"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        return response.json().get(
            "features",
            []
        )

    except Exception:

        return []


if find_doctors:

    if (
        not location
        or location.get("latitude") is None
        or location.get("longitude") is None
    ):

        st.warning(
            "📍 Please allow location access in your browser first."
            if language == "English"
            else "📍 முதலில் உங்கள் உலாவியில் இருப்பிட அனுமதியை வழங்கவும்."
        )

    else:

        try:

            latitude = float(
                location["latitude"]
            )

            longitude = float(
                location["longitude"]
            )

            st.success(
                "📍 Your location was detected!"
                if language == "English"
                else "📍 உங்கள் இருப்பிடம் கண்டறியப்பட்டது!"
            )

            search_terms = [
                "dermatologist",
                "dermatology clinic",
                "skin clinic",
                "skin hospital",
                "derma clinic"
            ]

            all_results = []

            with st.spinner(
                "🔎 Finding dermatologists near you..."
                if language == "English"
                else "🔎 உங்களுக்கு அருகிலுள்ள தோல் மருத்துவர்களைத் தேடுகிறது..."
            ):

                for search_term in search_terms:

                    results = search_photon(
                        search_term,
                        latitude,
                        longitude
                    )

                    all_results.extend(
                        results
                    )

            # ------------------------------------------------
            # PROCESS CLINICS
            # ------------------------------------------------

            for result in all_results:

                properties = result.get(
                    "properties",
                    {}
                )

                geometry = result.get(
                    "geometry",
                    {}
                )

                coordinates = geometry.get(
                    "coordinates",
                    []
                )

                if len(coordinates) < 2:
                    continue

                try:

                    place_longitude = float(
                        coordinates[0]
                    )

                    place_latitude = float(
                        coordinates[1]
                    )

                except Exception:

                    continue

                try:

                    distance = geodesic(
                        (
                            latitude,
                            longitude
                        ),
                        (
                            place_latitude,
                            place_longitude
                        )
                    ).km

                except Exception:

                    continue

                if distance > 20:
                    continue

                name = (
                    properties.get("name")
                    or "Dermatology Clinic"
                )

                address_parts = []

                for key in [
                    "housenumber",
                    "street",
                    "district",
                    "city",
                    "postcode"
                ]:

                    value = properties.get(
                        key
                    )

                    if value:
                        address_parts.append(
                            str(value)
                        )

                address = ", ".join(
                    address_parts
                )

                phone = (
                    properties.get("phone")
                    or properties.get(
                        "contact:phone"
                    )
                )

                website = (
                    properties.get("website")
                    or properties.get(
                        "contact:website"
                    )
                )

                clinics.append(
                    {
                        "name": name,
                        "distance": distance,
                        "address": address,
                        "phone": phone,
                        "website": website,
                        "latitude": place_latitude,
                        "longitude": place_longitude
                    }
                )

            # ------------------------------------------------
            # REMOVE DUPLICATES
            # ------------------------------------------------

            unique_clinics = {}

            for clinic in clinics:

                key = (
                    clinic["name"]
                    .strip()
                    .lower(),
                    round(
                        clinic["latitude"],
                        4
                    ),
                    round(
                        clinic["longitude"],
                        4
                    )
                )

                unique_clinics[key] = clinic

            clinics = list(
                unique_clinics.values()
            )

            # ------------------------------------------------
            # SORT
            # ------------------------------------------------

            clinics.sort(
                key=lambda x:
                x["distance"]
            )

        except Exception as e:

            st.error(
                f"Location/clinic search failed: {e}"
                if language == "English"
                else f"இருப்பிடம்/மருத்துவமனை தேடல் தோல்வியடைந்தது: {e}"
            )

# ------------------------------------------------------------
# DISPLAY CLINICS ONLY AFTER BUTTON
# ------------------------------------------------------------

if (
    find_doctors
    and location
    and location.get("latitude") is not None
    and location.get("longitude") is not None
):

    if not clinics:

        st.warning(
            "No dermatologist or skin clinic was found within 20 km."
            if language == "English"
            else "20 கி.மீ. சுற்றளவில் தோல் மருத்துவர் அல்லது தோல் மருத்துவமனை எதுவும் கிடைக்கவில்லை."
        )

        st.info(
            "Your location was detected, but the free place database may not contain clinics in this area."
            if language == "English"
            else "உங்கள் இருப்பிடம் கண்டறியப்பட்டது. ஆனால் இலவச இடத் தரவுத்தளத்தில் இந்தப் பகுதியில் உள்ள மருத்துவமனைகள் இருக்காமல் இருக்கலாம்."
        )

    else:

        st.subheader(
            "🩺 Dermatologists Near You"
            if language == "English"
            else "🩺 உங்களுக்கு அருகிலுள்ள தோல் மருத்துவர்கள்"
        )

        st.caption(
            "Sorted from nearest to farthest • Maximum distance: 20 km"
            if language == "English"
            else "அருகிலிருந்து தொலைவு வரை வரிசைப்படுத்தப்பட்டுள்ளது • அதிகபட்ச தூரம்: 20 கி.மீ."
        )

        for index, clinic in enumerate(
            clinics[:10],
            start=1
        ):

            st.markdown("---")

            st.markdown(
                f"### {index}. 🩺 {clinic['name']}"
            )

            if clinic["distance"] < 1:

                distance_text = (
                    f"{clinic['distance'] * 1000:.0f} meters"
                    if language == "English"
                    else f"{clinic['distance'] * 1000:.0f} மீட்டர்"
                )

            else:

                distance_text = (
                    f"{clinic['distance']:.2f} km"
                    if language == "English"
                    else f"{clinic['distance']:.2f} கி.மீ."
                )

            st.write(
                f"📏 **{distance_text} away**"
                if language == "English"
                else f"📏 **{distance_text} தொலைவில்**"
            )

            if clinic["address"]:

                st.write(
                    f"📍 {clinic['address']}"
                )

            else:

                st.write(
                    "📍 Address not available"
                    if language == "English"
                    else "📍 முகவரி கிடைக்கவில்லை"
                )

            maps_url = (
                "https://www.google.com/maps/dir/"
                "?api=1"
                f"&destination="
                f"{clinic['latitude']},"
                f"{clinic['longitude']}"
            )

            search_name = quote(
                f"{clinic['name']} "
                f"{clinic['address']}"
            )

            contact_url = (
                "https://www.google.com/search?q="
                f"{search_name}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.link_button(
                    "📍 Directions"
                    if language == "English"
                    else "📍 வழிகாட்டுதல்",
                    maps_url
                )

            with col2:

                if clinic["phone"]:

                    st.link_button(
                        "📞 Call"
                        if language == "English"
                        else "📞 அழைக்க",
                        "tel:" +
                        str(
                            clinic["phone"]
                        )
                    )

                else:

                    st.link_button(
                        "🔎 Contact"
                        if language == "English"
                        else "🔎 தொடர்பு",
                        contact_url
                    )

            with col3:

                if clinic["website"]:

                    st.link_button(
                        "🌐 Website"
                        if language == "English"
                        else "🌐 இணையதளம்",
                        clinic["website"]
                    )

                else:

                    st.link_button(
                        "🌐 Clinic Info"
                        if language == "English"
                        else "🌐 மருத்துவமனை தகவல்",
                        contact_url
                    )


# ============================================================
# DOWNLOAD PATIENT REPORT
# ============================================================

st.markdown("---")

st.header(
    "📄 Patient Report"
    if language == "English"
    else "📄 நோயாளர் அறிக்கை"
)

if "patient_details" not in st.session_state:

    st.info(
        "Please save patient details first."
        if language == "English"
        else "முதலில் நோயாளியின் விவரங்களைச் சேமிக்கவும்."
    )

elif uploaded_file is None or predicted_class is None:

    st.info(
        "Please upload an image and complete the AI analysis first."
        if language == "English"
        else "படத்தைப் பதிவேற்றி AI பகுப்பாய்வை முதலில் முடிக்கவும்."
    )

elif uploaded_image_bytes is None:

    st.info(
        "Please upload the image again to generate the report."
        if language == "English"
        else "அறிக்கையை உருவாக்க படத்தை மீண்டும் பதிவேற்றவும்."
    )

else:

    report_file = create_patient_report(
        st.session_state["patient_details"],
        predicted_class,
        confidence * 100,
        uploaded_image_bytes,
        language=language
    )

    st.download_button(
        label=TEXT["download_report"],
        data=report_file,
        file_name="Patient_Skin_Allergy_Report.pdf",
        mime="application/pdf",
        key="download_patient_report"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "DermaAI — AI-based skin condition analysis for informational purposes."
    if language == "English"
    else "DermaAI — தகவல் நோக்கங்களுக்கான AI அடிப்படையிலான தோல் நிலை பகுப்பாய்வு."
)