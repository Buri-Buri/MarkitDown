import sys
import os
import json

# Ensure stdout and stderr exist when running headless via pythonw.exe without a console
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# Fast Child Process Handler for OS Dialogs (Runs before any heavy imports or Flask setup)
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1].startswith("--dialog"):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if sys.argv[1] == "--dialog-files":
        files = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[
                ("All Supported Files", "*.pdf;*.docx;*.xlsx;*.xls;*.pptx;*.txt;*.csv;*.json;*.xml;*.htm;*.html;*.zip;*.epub;*.msg;*.wav;*.mp3;*.jpg;*.jpeg;*.png"),
                ("PDF Documents", "*.pdf"),
                ("Word Documents", "*.docx"),
                ("Excel Sheets", "*.xlsx;*.xls"),
                ("PowerPoint Slides", "*.pptx"),
                ("Images", "*.jpg;*.jpeg;*.png"),
                ("Audio Files", "*.wav;*.mp3"),
                ("Ebooks", "*.epub"),
                ("All Files", "*.*")
            ]
        )
        print(json.dumps(list(files)))
        sys.exit(0)
    elif sys.argv[1] == "--dialog-folder":
        folder = filedialog.askdirectory(title="Select Folder")
        print(folder)
        sys.exit(0)

import time
import socket
import datetime
import traceback
import subprocess
import threading
import webbrowser
import re
from urllib.parse import urlparse
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from markitdown import MarkItDown

# Shared default converter instance to eliminate instantiation overhead
default_converter = None
def get_converter(kwargs):
    global default_converter
    if not kwargs:
        if default_converter is None:
            default_converter = MarkItDown()
        return default_converter
    return MarkItDown(**kwargs)

# ----------------------------------------------------
# Main Server Setup
# ----------------------------------------------------

# Active tabs tracking & shutdown state
active_tabs = set()
active_tabs_lock = threading.Lock()
last_ping = time.time()
has_connected = False
shutdown_timer = None

def schedule_shutdown_if_no_tabs():
    global shutdown_timer
    with active_tabs_lock:
        if len(active_tabs) == 0 and has_connected:
            if shutdown_timer is not None:
                shutdown_timer.cancel()
            # 4 second grace period to differentiate tab close from page refresh / reload
            shutdown_timer = threading.Timer(4.0, do_shutdown)
            shutdown_timer.daemon = True
            shutdown_timer.start()

def cancel_pending_shutdown():
    global shutdown_timer
    if shutdown_timer is not None:
        shutdown_timer.cancel()
        shutdown_timer = None

def do_shutdown():
    with active_tabs_lock:
        if len(active_tabs) == 0:
            print("Browser tab closed. Shutting down server...")
            os._exit(0)

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

def get_config_dir():
    """Get the folder path to save persistent user data."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_config_path(filename):
    """Get writeable config path with home folder fallback."""
    base_dir = get_config_dir()
    if os.path.exists(base_dir) and os.access(base_dir, os.W_OK):
        return os.path.join(base_dir, filename)
    else:
        fallback_dir = os.path.join(os.path.expanduser("~"), ".markitdown_studio")
        os.makedirs(fallback_dir, exist_ok=True)
        return os.path.join(fallback_dir, filename)

def get_downloads_dir():
    """Get user's default Downloads directory on Windows."""
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.exists(downloads_path):
        return downloads_path
    return os.path.expanduser("~")

def get_url_filename(url):
    """Generate a clean filename from a URL (webpage or YouTube)."""
    parsed = urlparse(url)
    host = parsed.netloc.replace("www.", "")
    host = re.sub(r'[^a-zA-Z0-9.-]', '_', host)
    
    # Check for YouTube URL pattern
    if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
        video_id = ""
        if "v=" in parsed.query:
            # Query params extraction
            params = {k: v for k, v in [p.split('=') for p in parsed.query.split('&') if '=' in p]}
            video_id = params.get("v", "")
        elif parsed.netloc == "youtu.be" or "youtu.be" in parsed.netloc:
            video_id = parsed.path.strip("/")
        if video_id:
            return f"youtube_{video_id}"
        return "youtube_video"
        
    path_path = parsed.path
    if path_path.endswith('/'):
        path_path = path_path[:-1]
    base = os.path.basename(path_path)
    base = re.sub(r'[^a-zA-Z0-9.-]', '_', base)
    
    if base:
        return f"{host}_{base}"
    return f"{host}_webpage"

# Configurations
history_file = get_config_path("history.json")
settings_file = get_config_path("settings.json")

def load_settings():
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(settings):
    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def load_history():
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

# Initialize Flask App
ui_dir = get_resource_path("ui")
app = Flask(__name__, static_folder=None)

# ----------------------------------------------------
# Subprocess Helper for Dialogs
# ----------------------------------------------------
def run_dialog_subprocess(mode):
    if not hasattr(sys, '_MEIPASS'):
        cmd = [sys.executable, os.path.abspath(__file__), mode]
    else:
        cmd = [sys.executable, mode]
        
    proc = subprocess.run(cmd, capture_output=True, text=True, creationflags=0x08000000) # CREATE_NO_WINDOW
    return proc.stdout.strip()

# ----------------------------------------------------
# Flask Routing
# ----------------------------------------------------

@app.route('/')
def index():
    return send_from_directory(ui_dir, "index.html")

@app.route('/<path:filename>')
def serve_ui(filename):
    return send_from_directory(ui_dir, filename)

@app.route('/api/tab_opened', methods=['POST'])
def tab_opened():
    global has_connected, last_ping
    tab_id = request.json.get("tab_id") if request.is_json and request.json else None
    with active_tabs_lock:
        if tab_id:
            active_tabs.add(tab_id)
        cancel_pending_shutdown()
    has_connected = True
    last_ping = time.time()
    return jsonify({"status": "ok", "active_tabs": len(active_tabs)})

@app.route('/api/tab_closed', methods=['POST'])
def tab_closed():
    try:
        data = request.get_json(silent=True) or {}
        tab_id = data.get("tab_id")
    except Exception:
        tab_id = None
    with active_tabs_lock:
        if tab_id:
            active_tabs.discard(tab_id)
    schedule_shutdown_if_no_tabs()
    return jsonify({"status": "ok"})

@app.route('/api/ping', methods=['GET', 'POST'])
def ping():
    global last_ping, has_connected
    last_ping = time.time()
    has_connected = True
    tab_id = None
    if request.is_json and request.json:
        tab_id = request.json.get("tab_id")
    with active_tabs_lock:
        if tab_id:
            active_tabs.add(tab_id)
        cancel_pending_shutdown()
    return jsonify({"status": "ok"})

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'POST':
        settings = request.json
        save_settings(settings)
        return jsonify({"success": True})
    return jsonify(load_settings())

@app.route('/api/history', methods=['GET'])
def handle_history():
    return jsonify(load_history())

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    save_history([])
    return jsonify({"success": True})

@app.route('/api/select_files', methods=['POST'])
def select_files():
    try:
        output = run_dialog_subprocess("--dialog-files")
        if output:
            paths = json.loads(output)
            files_info = []
            for path in paths:
                if os.path.exists(path):
                    files_info.append({
                        "path": path,
                        "name": os.path.basename(path),
                        "size": os.path.getsize(path),
                        "extension": os.path.splitext(path)[1].lower()
                    })
            return jsonify(files_info)
    except Exception as e:
        print(f"Error selecting files: {e}")
    return jsonify([])

@app.route('/api/select_folder', methods=['POST'])
def select_folder():
    try:
        output = run_dialog_subprocess("--dialog-folder")
        return output if output else ""
    except Exception as e:
        print(f"Error selecting folder: {e}")
        return ""

def format_friendly_error(err):
    err_str = str(err)
    if "credit_balance_exhausted" in err_str or "insufficient_quota" in err_str:
        return "OpenAI API Error: Quota exceeded (Error 429). You have no credits remaining on your OpenAI account. Please add billing credits at platform.openai.com/billing or update your API key in Settings."
    if "invalid_api_key" in err_str or "Incorrect API key provided" in err_str:
        return "OpenAI API Error: Invalid API key. Please check and re-enter your OpenAI API key in Settings."
    if "RateLimitError" in err_str:
        return "OpenAI API Error: Rate limit reached (Error 429). Please wait a moment before trying again."
    if "AuthenticationError" in err_str:
        return "OpenAI API Error: Authentication failed. Please verify your OpenAI API key in Settings."
    return err_str

@app.route('/api/convert_file', methods=['POST'])
def convert_file():
    data = request.json or {}
    file_path = data.get("file_path")
    custom_prompt = data.get("prompt")
    force_llm = data.get("force_llm")
    
    settings = load_settings()
    output_dir = get_downloads_dir()
    
    try:
        kwargs = {}
        # Configure LLM Client
        if (settings.get("use_llm") or force_llm) and settings.get("api_key"):
            from openai import OpenAI
            client = OpenAI(
                api_key=settings.get("api_key"),
                base_url=settings.get("api_base") or None
            )
            kwargs["llm_client"] = client
            kwargs["llm_model"] = settings.get("llm_model") or "gpt-4o"
            if custom_prompt:
                kwargs["llm_prompt"] = custom_prompt
            elif settings.get("llm_prompt"):
                kwargs["llm_prompt"] = settings.get("llm_prompt")

        # Configure Azure Document Intelligence
        if settings.get("use_docintel") and settings.get("docintel_endpoint"):
            kwargs["docintel_endpoint"] = settings.get("docintel_endpoint")
            if settings.get("docintel_key"):
                kwargs["docintel_credential"] = settings.get("docintel_key")

        # Run conversion
        md_converter = get_converter(kwargs)
        result = md_converter.convert(file_path)
        markdown_content = result.text_content

        os.makedirs(output_dir, exist_ok=True)
        file_base = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(output_dir, f"{file_base}.md")

        # Unique naming
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{file_base}_{counter}.md")
            counter += 1

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Update History
        history = load_history()
        entry = {
            "source_path": file_path,
            "source_name": os.path.basename(file_path),
            "output_path": output_path,
            "output_name": os.path.basename(output_path),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success"
        }
        history.insert(0, entry)
        save_history(history)

        return jsonify({
            "success": True,
            "markdown": markdown_content,
            "output_path": output_path,
            "output_name": os.path.basename(output_path)
        })
    except Exception as e:
        error_msg = format_friendly_error(e)
        print(traceback.format_exc())
        
        history = load_history()
        entry = {
            "source_path": file_path,
            "source_name": os.path.basename(file_path),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "error",
            "error": error_msg
        }
        history.insert(0, entry)
        save_history(history)
        
        return jsonify({
            "success": False,
            "error": error_msg
        })

@app.route('/api/convert_url', methods=['POST'])
def convert_url():
    data = request.json
    url = data.get("url")
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"success": False, "error": "Invalid URL provided."})
        
    settings = load_settings()
    output_dir = get_downloads_dir()
    
    try:
        kwargs = {}
        # Configure LLM Client
        if settings.get("use_llm") and settings.get("api_key"):
            from openai import OpenAI
            client = OpenAI(
                api_key=settings.get("api_key"),
                base_url=settings.get("api_base") or None
            )
            kwargs["llm_client"] = client
            kwargs["llm_model"] = settings.get("llm_model") or "gpt-4o"
            if settings.get("llm_prompt"):
                kwargs["llm_prompt"] = settings.get("llm_prompt")

        # Configure Azure Document Intelligence
        if settings.get("use_docintel") and settings.get("docintel_endpoint"):
            kwargs["docintel_endpoint"] = settings.get("docintel_endpoint")
            if settings.get("docintel_key"):
                kwargs["docintel_credential"] = settings.get("docintel_key")

        # Run URL conversion
        md_converter = get_converter(kwargs)
        result = md_converter.convert(url)
        markdown_content = result.text_content

        os.makedirs(output_dir, exist_ok=True)
        file_base = get_url_filename(url)
        output_path = os.path.join(output_dir, f"{file_base}.md")

        # Unique naming
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{file_base}_{counter}.md")
            counter += 1

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Update History
        history = load_history()
        entry = {
            "source_path": url,
            "source_name": url,
            "output_path": output_path,
            "output_name": os.path.basename(output_path),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success"
        }
        history.insert(0, entry)
        save_history(history)

        return jsonify({
            "success": True,
            "markdown": markdown_content,
            "output_path": output_path,
            "output_name": os.path.basename(output_path)
        })
    except Exception as e:
        error_msg = format_friendly_error(e)
        print(traceback.format_exc())
        
        history = load_history()
        entry = {
            "source_path": url,
            "source_name": url,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "error",
            "error": error_msg
        }
        history.insert(0, entry)
        save_history(history)
        
        return jsonify({
            "success": False,
            "error": error_msg
        })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})
    
    file = request.files['file']
    custom_prompt = request.form.get("prompt")
    force_llm = request.form.get("force_llm") == "true"
    
    if file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"})
        
    try:
        # Create temp folder next to app
        temp_dir = get_config_path("temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        output_dir = get_downloads_dir()
            
        settings = load_settings()
        kwargs = {}
        if (settings.get("use_llm") or force_llm) and settings.get("api_key"):
            from openai import OpenAI
            client = OpenAI(api_key=settings.get("api_key"), base_url=settings.get("api_base") or None)
            kwargs["llm_client"] = client
            kwargs["llm_model"] = settings.get("llm_model") or "gpt-4o"
            if custom_prompt:
                kwargs["llm_prompt"] = custom_prompt
            elif settings.get("llm_prompt"):
                kwargs["llm_prompt"] = settings.get("llm_prompt")

        if settings.get("use_docintel") and settings.get("docintel_endpoint"):
            kwargs["docintel_endpoint"] = settings.get("docintel_endpoint")
            if settings.get("docintel_key"):
                kwargs["docintel_credential"] = settings.get("docintel_key")

        # Run conversion
        md_converter = get_converter(kwargs)
        result = md_converter.convert(temp_path)
        markdown_content = result.text_content
        
        file_base = os.path.splitext(file.filename)[0]
        output_path = os.path.join(output_dir, f"{file_base}.md")
        
        # Unique naming
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{file_base}_{counter}.md")
            counter += 1
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        # Remove temp file
        try:
            os.remove(temp_path)
        except Exception:
            pass

        # Update History
        history = load_history()
        entry = {
            "source_path": f"Uploaded: {file.filename}",
            "source_name": file.filename,
            "output_path": output_path,
            "output_name": os.path.basename(output_path),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success"
        }
        history.insert(0, entry)
        save_history(history)

        return jsonify({
            "success": True,
            "markdown": markdown_content,
            "output_path": output_path,
            "output_name": os.path.basename(output_path)
        })
    except Exception as e:
        error_msg = format_friendly_error(e)
        print(traceback.format_exc())
        
        history = load_history()
        entry = {
            "source_path": f"Uploaded: {file.filename if 'file' in locals() and file else 'Unknown'}",
            "source_name": file.filename if 'file' in locals() and file else "Unknown",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "error",
            "error": error_msg
        }
        history.insert(0, entry)
        save_history(history)
        
        return jsonify({"success": False, "error": error_msg})

@app.route('/api/read_text_file', methods=['POST'])
def read_text_file():
    file_path = request.json.get("file_path")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    return "Error: File does not exist."

@app.route('/api/open_path', methods=['POST'])
def open_path():
    path = request.json.get("path")
    if os.path.exists(path):
        try:
            os.startfile(path)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False, "error": "File or folder does not exist."})

@app.route('/api/open_folder_containing', methods=['POST'])
def open_folder_containing():
    file_path = request.json.get("file_path")
    folder = os.path.dirname(file_path)
    if os.path.exists(folder):
        try:
            os.startfile(folder)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False, "error": "Folder does not exist."})

# ----------------------------------------------------
# Background Watchdog & Launch Logic
# ----------------------------------------------------

def shutdown_watchdog():
    """Watchdog for initial connection and hard disconnect fallback."""
    global last_ping, has_connected
    # Allow up to 60 seconds on initial startup for browser to launch
    startup_deadline = time.time() + 60
    while not has_connected:
        time.sleep(1)
        if time.time() > startup_deadline:
            print("No client connected within startup window. Shutting down server...")
            os._exit(0)

    # Main monitoring loop:
    # Runs continuously as long as the browser tab is open.
    # Inactivity does NOT shut down the server.
    # Shutdown only occurs if:
    # 1. The tab is explicitly closed (via tab_closed callback and grace timer)
    # 2. Or a 10-minute complete silence fallback triggers (if browser hard-crashed)
    while True:
        time.sleep(10)
        # Safety fallback if browser was force killed or crashed
        if time.time() - last_ping > 600:
            print("No active connection detected for 10 minutes. Shutting down server...")
            os._exit(0)

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def main():
    port = find_free_port()
    url = f"http://127.0.0.1:{port}/"
    
    threading.Thread(target=shutdown_watchdog, daemon=True).start()
    threading.Thread(target=lambda: (time.sleep(1.0), webbrowser.open(url)), daemon=True).start()
    
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False, threaded=True)

if __name__ == "__main__":
    main()
