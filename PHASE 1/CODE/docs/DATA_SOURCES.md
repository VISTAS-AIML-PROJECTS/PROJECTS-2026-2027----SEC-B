# Data Sources

---

## 1. Amazon Berkeley Objects (ABO) Product Catalog

| Field | Value |
|---|---|
| Source | Amazon Berkeley Objects dataset |
| File | `public/wrapture_abo_products.json` |
| Records | ~42,650 dimension-valid products |
| Product types | ~524 unique types |
| Fields used | item_id, item_name, product_type, length, width, height, volume_cubic_in |
| Dimension units | inches |
| Filter applied | Only records with length > 0, width > 0, height > 0 |

This is a static file served directly from the React public directory and also read by the Flask backend. It is NOT duplicated into SQLite — it is used as a read-only reference catalog.

---

## 2. Packrift Packaging Catalog

| Field | Value |
|---|---|
| Source | Packrift packaging supplier catalog |
| File | `public/data/wrapture_packaging_catalog.json` |
| Records | ~2,209 |
| Types | Boxes, mailers, poly bags |
| Fields used | sku, title, family, product_type, length_in, width_in, height_in, material, protection_score, protection_evidence, pack_quantity, unit_price, snapshot_price, co2e_recycling_mt, canonical_product_url |

`load_capacity` is **not** present in this catalog. The backend always returns `load_capacity_verified: false`.

CO₂ values (`co2e_recycling_mt`) are present for some records and `null` for others. The backend never invents a CO₂ value — it returns `null` when unavailable.

---

## 3. Rootstrap Waste/Material Dataset

| Field | Value |
|---|---|
| Used for | Training the MobileNetV2 material classifier |
| Classes | cardboard, compost, glass, metal, paper, plastic, trash |
| Training images | 2,616 |
| Test images | 645 |

The dataset is not included in this repository. The trained model artifacts are included.

---

## 4. COCO 2017 (subset)

| Field | Value |
|---|---|
| Used for | Training the YOLO11s product detector |
| Classes used | 15 (laptop, cell_phone, keyboard, mouse, bottle, cup, backpack, handbag, book, clock, vase, chair, remote, scissors, teddy_bear) |
| Status | Training in progress |

---

## 5. SQLite Application Database

| Field | Value |
|---|---|
| File | `backend/data/wrapture.db` (created at runtime) |
| Tables | recommendations, material_classifications, chat_messages, review_analyses |
| Purpose | Store real application usage events |
| Initial state | Empty (all counts start at zero) |

This database is **not** committed to version control (`backend/data/*.db` is in `.gitignore`).
