# Model Documentation

---

## 1. Wrapture MobileNetV2 Material Classifier

| Field | Value |
|---|---|
| Name | Wrapture MobileNetV2 Material Classifier |
| Architecture | MobileNetV2 + GlobalAveragePooling + Dense(7, softmax) |
| Framework | TensorFlow / Keras |
| Task | Multi-class image classification (packaging/waste material) |
| Classes | 7 |
| Class names | cardboard, compost, glass, metal, paper, plastic, trash |
| Training dataset | Rootstrap waste/material dataset |
| Training samples | 2,616 |
| Test samples | 645 |
| Test accuracy | ~86.98% (measured on unseen test set) |
| Input shape | (224, 224, 3) — RGB, float32 |
| Status | **Trained** |

**Artifact locations**

- TF.js (browser): `public/models/wrapture-material/model.json` + `.bin` shards
- SavedModel (Flask backend): `model_conversion/content/wrapture_material_model/`

**Important note**

This is a **material/waste classifier**. It classifies the dominant material visible in an image (cardboard, plastic, glass, etc.). It is **not** a product detector and will not identify product types such as "laptop" or "bottle".

**Backend inference**

The Flask backend loads the SavedModel via `tf.saved_model.load()` and runs inference through the `serving_default` signature. Confidence values are real softmax probabilities from the model — not invented.

---

## 2. Wrapture YOLO11s Product Detector

| Field | Value |
|---|---|
| Name | Wrapture YOLO11s Product Detector |
| Architecture | YOLO11s (Ultralytics) |
| Framework | Ultralytics / PyTorch |
| Task | Object detection |
| Classes | 15 |
| Class names | laptop, cell_phone, keyboard, mouse, bottle, cup, backpack, handbag, book, clock, vase, chair, remote, scissors, teddy_bear |
| Training dataset | COCO 2017 (subset, annotated for 15 target classes) |
| Training samples | Not yet evaluated |
| Test samples | Not yet evaluated |
| Test accuracy | Not yet evaluated |
| Status | **Training in progress (Google Colab)** |

**Expected artifact location**

```
backend/models/yolo/best.pt       ← PyTorch weights
backend/models/yolo/classes.json  ← class name list
```

**How to install when training is complete**

1. Export `best.pt` from Colab.
2. Place at `backend/models/yolo/best.pt`.
3. Create `backend/models/yolo/classes.json` with the 15 class names.
4. Restart Flask — the model loads automatically.

**Behavior when unavailable**

The backend returns:
```json
{
  "status": "PRODUCT_DETECTOR_UNAVAILABLE",
  "error": "Product detection model not installed. Expected weights at: ..."
}
```

No fake detections are returned under any circumstances.

---

## 3. DistilBERT Sentiment Analyzer (third-party pretrained)

| Field | Value |
|---|---|
| Name | distilbert-base-uncased-finetuned-sst-2-english |
| Source | HuggingFace Hub (public pretrained model) |
| Task | Binary sentiment classification (POSITIVE / NEGATIVE) |
| Classes | 2 (POSITIVE, NEGATIVE) |
| Training | Pretrained on SST-2 by HuggingFace — not trained by Wrapture |
| Status | Downloaded on first use via `transformers` library |

Segments with confidence < 65% are classified as neutral by Wrapture's post-processing.
