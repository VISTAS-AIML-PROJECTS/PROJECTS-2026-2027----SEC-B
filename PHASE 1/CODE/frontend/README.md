# ChronoLens - Frontend

React single-page frontend application for **ChronoLens** (Phase 0 Video Upload Interface).

---

## Technical Overview

- **Framework:** React 18 + Vite
- **HTTP Client:** Axios
- **Design System:** Custom Dark Theme (`#0B0F19` canvas, `#4F46E5` primary accent, glassmorphic cards)
- **Icons:** Lucide React

---

## Folder Structure

```
frontend/
├── public/                  # Static web assets
├── src/
│   ├── components/
│   │   └── VideoUploader.jsx# Core drag-and-drop & progress upload component
│   ├── App.jsx              # Main single-page container (Title & Upload panel)
│   ├── index.css            # Dark mode design tokens & CSS variables
│   └── main.jsx             # React DOM root entry
├── index.html               # Main HTML template & Google Fonts
├── package.json             # NPM dependencies & build scripts
├── vite.config.js           # Vite dev server & proxy settings
└── README.md                # Frontend documentation
```

---

## Frontend Setup & Execution

### 1. Install Dependencies

```bash
# Navigate to frontend folder
cd frontend

# Install packages
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

The frontend application will run on `http://localhost:5173`.

---

## Key Features

- **Single Page Application:** Minimalist, centered card layout without unnecessary routing or dashboards.
- **Drag & Drop Upload Zone:** Responsive interactive dropzone with drag-hover highlights.
- **Browse File Button:** Standard file browser trigger.
- **Real-Time Progress Bar:** Powered by Axios `onUploadProgress` listener showing live percentage.
- **Pre-Validation:** Pre-screens format (.mp4, .avi, .mov, .mkv) and 2GB size limit before sending network requests.
- **Comprehensive Error Handling:** Explicit badges and alert banners for:
  - *Unsupported file type.*
  - *Upload failed.*
  - *Network error.*
  - *Large file.*
