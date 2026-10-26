# Complete Step-by-Step Guide: Moving this Project to Another System

This guide explains exactly how to transfer the **NSE & BSE Full Market Coverage Terminal** to another computer (Windows, macOS, or Linux) with zero data loss and ready-to-run setup.

---

## 📋 What Needs to be Transferred

### ✅ 1. Folders and Files to COPY:
* `backend/` *(Exclude `venv/`)*
* `frontend/` *(Exclude `node_modules/`)*
* `data/` *(Make sure `data/market_master.db` is included so all 62,798 instruments are preserved!)*
* `.env` / `backend/.env` *(Keep your broker keys or AI API keys intact)*
* `setup_new_pc.bat` / `start.bat` *(or `.sh` scripts for Mac/Linux)*
* `package.json`, `requirements.txt`, etc.

### ❌ 2. Folders to SKIP / DELETE before copying:
* `backend/venv/` (Virtual environments are specific to the machine's operating system and Python path).
* `frontend/node_modules/` (Node packages should be installed fresh on the new machine via `npm install`).
* `frontend/dist/` (Build output, will be regenerated if built).

---

## 🛠️ Step 1: Destination System Prerequisites

Make sure the new computer has installed:
1. **Python 3.10+** (Download from [python.org](https://www.python.org/) — *Check "Add Python to PATH" during installation on Windows*).
2. **Node.js 18+ or 20+ (LTS)** (Download from [nodejs.org](https://nodejs.org/)).

---

## 🚀 Step 2: Running Setup on the New System

### 🪟 On Windows (Easiest Method):
1. Copy the `nse-bse-platform` folder onto your new computer (e.g., to `C:\Projects\nse-bse-platform` or `D:\Projects\nse-bse-platform`).
2. Double-click **`setup_new_pc.bat`**.
   * It will automatically create `backend/venv`, install all Python dependencies from `requirements.txt`, and run `npm install` for the frontend.
3. Once completed, simply double-click **`start.bat`**!

### 💻 Manual Command Line Setup (Windows / Mac / Linux):

#### Terminal 1: Setup & Run Python Backend
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Mac / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Backend Server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 2: Setup & Run React Frontend
```bash
cd frontend

# Install Node modules
npm install

# Start Frontend Dev Server
npm run dev
```

---

## 🌐 Step 3: Access the Application

- **Web Application Interface:** Open browser at `http://localhost:5173`
- **Backend API & Swagger Docs:** Open browser at `http://127.0.0.1:8000/docs`

---

## 🔑 Step 4: Environment Variables (`.env`)

If you had custom Kotak Neo credentials or AI API keys configured:
- Check `backend/.env`
- Ensure your keys are in place:
```env
ACTIVE_LIVE_PROVIDER=kotak_neo
KOTAK_CONSUMER_KEY=your_consumer_key
GEMINI_API_KEY=your_gemini_key_if_used
```
