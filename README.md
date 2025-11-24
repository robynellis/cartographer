# Cartographer  
An automated pipeline for converting **YouTube playlists → Beat Saber maps**, fully processed and prepared for ChroMapper.

Cartographer handles:

- playlist extraction  
- high-quality M4A audio downloading  
- automated Beat Sage map generation (via Playwright)  
- map cleanup, metadata normalization, and folder renaming  
- preparing maps for final editing in ChroMapper  

This project is designed to be fully automated, configurable, and CI/CD friendly.

---

## 📦 Project Overview

```
Playlist URL
   ↓
download_songs.py
   ↓
Audio files (.m4a)
   ↓
generate_maps.py (Beat Sage automation)
   ↓
Map ZIPs
   ↓
manipulate_files.py
   ↓
Clean Map Folders (ready for ChroMapper)
```

Each step is fully controllable through `run_pipeline.py` or can be executed manually.

---

# 🔧 Setup

All steps assume you're inside the project root.

### 1. Create the virtual environment

```bash
python3 -m venv .venv
```

### 2. Activate the environment

**macOS / Linux**
```bash
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browser runtime (Chromium)

```bash
python -m playwright install chromium
```

### 5. Configure the project

Copy the example config:

```bash
cp vars.example.json vars.json
```

Open `vars.json` and update:

- `base_dir`:  
  ```
  "/home/user/beatsaber"
  ```
- `paths.songs` and `paths.maps`  
- playlist URL or pass via CLI  
- Beat Sage parameters (artist, model, difficulty)  
- post-processing author name  

---

# 🚀 Automated Pipeline (Recommended)

Cartographer includes a master runner that executes the full workflow.

### Run everything:

```bash
python3 run_pipeline.py
```

### Run without prompts (CI mode):

```bash
python3 run_pipeline.py --yes
```

### Skip stages:

```bash
python3 run_pipeline.py --skip-download
python3 run_pipeline.py --skip-generate
python3 run_pipeline.py --skip-clean
```

### Use a custom config file:

```bash
python3 run_pipeline.py --config env/vars-party.json
```

---

# 🛠 Manual Usage (Per-stage Execution)

If you want full control:

### 1. Download audio files from a playlist

```bash
python3 download_songs.py
```

Override playlist at runtime:

```bash
python3 download_songs.py --playlist "https://youtube.com/playlist?list=..."
```

### 2. Generate Beat Saber maps (Beat Sage automation)

Default (headless):

```bash
python3 generate_maps.py
```

To see the browser UI, set `"headless": false` in `vars.json`.

### 3. Clean and normalize maps

```bash
python3 manipulate_files.py
```

This step:

- removes “Beat Sage_” prefixes  
- removes model version suffixes  
- strips `.m4a` from folder names  
- updates author metadata  
- deletes Beat Sage `_customData`  
- renames difficulty files if needed  

### 4. Move cleaned maps into your ChroMapper working directory

Once maps are processed, move them from:

```
/home/user/beatsaber/maps
```

to your Beat Saber **CustomWIP** directory.

Open them in **ChroMapper** to:

- add lighting  
- customize environment  
- polish patterns  
- finalize map details  

---

# ⚙️ Configuration Reference (`vars.json`)

```json
{
  "base_dir": "/home/user/beatsaber",

  "paths": {
    "songs": "songs",
    "maps": "maps"
  },

  "download": {
    "audio_format": "140",
    "playlist_url": "",
    "progress_bar": true
  },

  "beatsage": {
    "url": "https://beatsage.com",
    "headless": true,
    "artist_name": "Thievery Corporation",
    "difficulty_label": "Expert+",
    "model_value": "v2-flow"
  },

  "postprocess": {
    "author_name": "AtomicbabyVR"
  }
}
```

---

# 📁 Directory Layout

```
cartographer/
│
├── download_songs.py
├── generate_maps.py
├── manipulate_files.py
├── run_pipeline.py
├── config.py
│
├── requirements.txt
├── vars.json
├── vars.example.json
│
├── songs/   ← downloaded .m4a files
└── maps/    ← processed map folders
```

---

# 🧭 Roadmap

### Phase 3 (planned)

- CI/CD integration  
- Artifact publishing  
- Configuration profiles  
- ChroMapper automation  
- Optional Dockerization  
- Web UI for playlist → maps  

---

# 🤝 Contributing

Pull requests are welcome.

To contribute:

- follow existing code style  
- keep config in `vars.json`  
- avoid hardcoded paths  
- ensure scripts are runnable through venv + `run_pipeline.py`  
