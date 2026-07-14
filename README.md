# MarkItDown Studio

MarkItDown Studio is a modern, premium Windows desktop utility built on top of Microsoft's `markitdown` engine. It provides a visual dashboard to convert standard documents, images, audio files, and web links into clean, LLM-friendly Markdown (.md) files.

All conversions are automatically saved to your system's default **Downloads** directory.

## System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit).
- **Web Browser**: Google Chrome, Microsoft Edge, Mozilla Firefox, or any modern web browser.
- **Internet Connection**: Required for converting Webpage / YouTube URLs and utilizing OpenAI image descriptions. Offline local file conversions (PDF, Word, Excel, Epubs, etc.) do not require internet access.
- **Optional Dependencies**:
  - **FFmpeg**: Required only if you wish to translate audio files (e.g. speech-to-text transcriptions) to Markdown. FFmpeg must be installed and added to your system `PATH`.

---

## Features

- **Multi-Format Conversion**: Supports PDF, Word (.docx), Excel (.xlsx, .xls), PowerPoint (.pptx), Epubs, Outlook messages (.msg), HTML, text formats (.txt, .csv, .json, .xml), and Zip archives.
- **URL & YouTube Conversion**: Paste any webpage URL or YouTube video link to instantly convert it to Markdown (web page scraping or video transcript download).
- **Drag & Drop Upload**: Drag multiple files directly into the browser to queue them for conversion.
- **Live Preview & Editor**: Compare rendered Markdown preview and raw Markdown source code in a side-by-side drawer, featuring quick copy-to-clipboard options.
- **Conversion Logs**: An interactive history log tracking successful conversions and detailed error hovers.
- **Multimodal LLM Support**: Configure OpenAI API credentials in the settings to automatically generate detailed captions/descriptions for images and visual assets.
- **Azure AI Support**: Configure Azure AI Document Intelligence credentials to extract tables, structures, and text from scanned/complex PDF layouts.

---

## How to Run

### Option 1: Standalone Executable (Recommended)
No Python installation is required.
1. Navigate to the executable directory:
   `D:\OneDrive - MSFT\Quantonova\md\markitdown_studio\dist\`
2. Double-click **`MarkItDownStudio.exe`**.
3. A browser tab will open automatically at a local port containing the interface.
4. **Auto-Shutdown**: When you close the browser tab, the background executable will automatically shut down within 10 seconds.

### Option 2: Run in Python (Development Mode)
Requires Python 3.10+ and dependencies.
1. Ensure the required Python packages are installed:
   ```bash
   pip install markitdown flask openai pyinstaller
   ```
2. Double-click **`run_app.bat`** (or execute `python app.py` in your terminal inside the `markitdown_studio` directory).

---

## Configuration Settings

Inside the **Settings** tab in the sidebar:
- **LLM Settings**: Toggle "Enable LLM Descriptions" and provide your OpenAI API Key, Model name (default `gpt-4o`), and a custom extraction prompt. This enables describing visual layouts in images.
- **Azure AI Document Intelligence**: Toggle and enter your Azure AI endpoint and access key to parse complex layouts and tables.

---

## How to Rebuild the Executable

If you modify the source files and wish to compile a new `.exe`:
1. Double-click **`build_exe.bat`** inside the `markitdown_studio` directory.
2. The script will automatically locate `magika`'s ML model folders and compile the application.
3. The new standalone executable will be saved in `markitdown_studio/dist/MarkItDownStudio.exe`.

---

## Credits & Acknowledgments

MarkItDown Studio is built on top of and fully powered by **Microsoft's `markitdown` engine**. We would like to express our gratitude to the creators and maintainers of the official repository:
- **Official Repository**: [microsoft/markitdown](https://github.com/microsoft/markitdown)

This utility wraps Microsoft's engine in a modern, visual desktop application to make it accessible to non-technical users and to streamline batch LLM-friendly markdown conversions.

