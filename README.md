# MarkItDown Studio

**MarkItDown Studio** is a modern, responsive Windows desktop application built on top of Microsoft's [`markitdown`](https://github.com/microsoft/markitdown) engine. It provides a visual dashboard to convert standard documents, images, audio files, and web links into clean, LLM-ready Markdown (`.md`) files.

All conversions are automatically saved to your system's default **Downloads** directory, ready for immediate use in your LLM context windows, RAG pipelines, or documentation repositories.

---

## Key Features

### 1. Three Dedicated Conversion Workflows
The dashboard is organized into three purpose-built conversion sections:

*   **📄 Documents & Files**:
    *   **Supported Formats**: PDF, Word (`.docx`), Excel (`.xlsx`, `.xls`), PowerPoint (`.pptx`), EPubs, Audio (`.mp3`, `.wav`), Outlook messages (`.msg`), HTML, text formats (`.txt`, `.csv`, `.json`, `.xml`), and Zip archives.
    *   **Flexible Input**: Drag & drop files directly onto the dropzone or click **Browse Files** / **Browse Folder** for instant batch queuing.
*   **🖼️ Images to Markdown (Dedicated AI Vision)**:
    *   **Supported Formats**: PNG, JPG, JPEG, WEBP, GIF.
    *   **Custom Prompting**: Type a custom extraction or analysis prompt directly in the card (e.g., *"Extract all chart data into markdown tables"* or *"Describe layout and visual design elements"*).
    *   **Live Status Indicator**: Visual badge displays whether OpenAI Vision is currently active or needs an API key configured.
    *   **Automatic Fallback**: If no API key is configured, extracts file metadata gracefully.
*   **🌐 Webpage & YouTube URLs**:
    *   **Web Scraping**: Converts any public article or webpage URL to clean Markdown.
    *   **YouTube Transcription**: Automatically fetches and structures transcripts from YouTube video links.
    *   **Service Indicators**: Displays real-time status of Azure AI and OpenAI Vision integrations.

### 2. High-Performance, Instant UI
*   **Zero-Latency Native Pickers**: Uses native HTML5 dialogs for instantaneous file and folder selection without freezing or delays.
*   **Multi-Threaded Concurrency**: Built on a multi-threaded Flask backend for snappy conversions and concurrent request handling.
*   **Live Side-by-Side Preview Drawer**: Compare rendered HTML markdown preview and raw Markdown source code with one-click clipboard copying.
*   **Real-Time Conversion Logs**: Track conversion history, timestamps, file sizes, and view detailed error tooltips.

## System Requirements

*   **Operating System**: Windows 10 or Windows 11 (64-bit).
*   **Python**: Python 3.10+ installed and added to `PATH`.
*   **Web Browser**: Google Chrome, Microsoft Edge, Mozilla Firefox, or any modern Chromium-based browser.
*   **Internet Connection**: Required for converting Webpage / YouTube URLs, and for OpenAI Vision / Azure AI integrations. Standard local document conversions (PDF, Word, Excel, EPubs, etc.) work completely offline.
*   **Optional Dependency (FFmpeg)**: Required only if converting audio files (e.g., `.wav`, `.mp3` speech-to-text transcription). FFmpeg must be installed and added to your system `PATH`.

---

## How to Run

### Option 1: One-Click Launch (Recommended)
Simply double-click **`run_app.bat`** in the project root directory:
1. It checks your Python environment and installs any missing packages from `requirements.txt` automatically.
2. It launches the application headless in the background via `pythonw.exe`.
3. It opens MarkItDown Studio in your default browser at `http://127.0.0.1:5000`.
4. The terminal window closes automatically.

### Option 2: Manual Terminal Launch
You can also run the application directly from PowerShell or Command Prompt:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the local server
python app.py
```
Then navigate to `http://127.0.0.1:5000` in your web browser.

---

## Configuration & Settings

Click the **Settings** tab in the left sidebar to configure optional AI integrations:

### 1. OpenAI Multimodal LLM (Vision)
*   **Enable LLM Descriptions**: Toggle on to generate detailed visual descriptions and table extractions from images.
*   **API Key**: Enter your OpenAI API key (`sk-...`).
*   **Model**: Choose or enter an OpenAI vision-capable model (default: `gpt-4o`, `gpt-4o-mini`).
*   **Default Prompt**: Customize the default system prompt used to analyze images across the app.

### 2. Azure AI Document Intelligence
*   **Enable Azure AI**: Toggle on for high-fidelity OCR, document layout analysis, and complex table structure extraction from scanned PDFs.
*   **Endpoint URL**: Your Azure Document Intelligence service endpoint.
*   **API Key**: Your Azure cognitive services access key.

---

## Project Structure

```
markitdown_studio/
├── app.py                  # Multi-threaded Flask backend with tab lifecycle & MarkItDown engine
├── run_app.bat             # Headless one-click Windows launcher (auto-closing terminal)
├── requirements.txt        # Python package dependencies
├── test_app_logic.py       # Automated unit test suite
├── README.md               # User manual and technical documentation
└── ui/
    ├── index.html          # Visual conversion dashboard (3 dedicated conversion cards)
    ├── style.css           # Modern dark-mode styling with AI Vision purple accents
    └── script.js           # Client-side state, Web Worker heartbeat, and preview drawer
```

---

## Credits & Acknowledgments

MarkItDown Studio is built on top of and fully powered by **Microsoft's `markitdown` engine**. We would like to express our gratitude to the creators and maintainers of the official repository:
*   **Official Repository**: [microsoft/markitdown](https://github.com/microsoft/markitdown)

This utility wraps Microsoft's engine in a modern, visual desktop application to streamline batch Markdown conversion for LLM context windows, RAG pipelines, and agentic workflows.
