// MarkItDown Studio App Script - Browser / Flask Web Architecture

// Mimic the original pywebview API structure for seamless compatibility
const pywebview = {
    api: {
        async select_files() {
            const res = await fetch('/api/select_files', { method: 'POST' });
            return await res.json();
        },
        async select_folder() {
            const res = await fetch('/api/select_folder', { method: 'POST' });
            const path = await res.text();
            return path || null;
        },
        async get_settings() {
            const res = await fetch('/api/settings');
            return await res.json();
        },
        async save_settings(settings) {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            return await res.json();
        },
        async get_history() {
            const res = await fetch('/api/history');
            return await res.json();
        },
        async clear_history() {
            const res = await fetch('/api/clear_history', { method: 'POST' });
            return await res.json();
        },
        async convert_file(filePath) {
            const res = await fetch('/api/convert_file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: filePath })
            });
            return await res.json();
        },
        async read_text_file(filePath) {
            const res = await fetch('/api/read_text_file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: filePath })
            });
            return await res.text();
        },
        async open_path(path) {
            const res = await fetch('/api/open_path', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: path })
            });
            return await res.json();
        },
        async open_folder_containing(filePath) {
            const res = await fetch('/api/open_folder_containing', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: filePath })
            });
            return await res.json();
        }
    }
};

// App State
let conversionQueue = [];
let appSettings = {};
let appHistory = [];
let isConverting = false;

// DOM Elements
const navItems = document.querySelectorAll('.nav-item');
const tabContents = document.querySelectorAll('.tab-content');
const dropZone = document.getElementById('drop-zone');
const btnSelectFiles = document.getElementById('btn-select-files');
const btnSelectFolder = document.getElementById('btn-select-folder');
const queueCard = document.getElementById('queue-card');
const queueList = document.getElementById('queue-list');
const queueCount = document.getElementById('queue-count');
const btnClearQueue = document.getElementById('btn-clear-queue');
const btnStartConvert = document.getElementById('btn-start-convert');
const historyList = document.getElementById('history-list');
const btnClearHistory = document.getElementById('btn-clear-history');
const settingsForm = document.getElementById('settings-form');
const checkUseLlm = document.getElementById('use-llm');
const llmFields = document.getElementById('llm-fields');
const checkUseDocIntel = document.getElementById('use-docintel');
const docintelFields = document.getElementById('docintel-fields');
const settingsSaveSuccess = document.getElementById('settings-save-success');

// URL inputs
const inputUrl = document.getElementById('input-url');
const btnConvertUrl = document.getElementById('btn-convert-url');

// Configuration Indicators
const llmIndicator = document.getElementById('llm-indicator');
const docintelIndicator = document.getElementById('docintel-indicator');

// Drawer Elements
const previewDrawer = document.getElementById('preview-drawer');
const drawerOverlay = document.getElementById('drawer-overlay');
const btnPreviewClose = document.getElementById('btn-preview-close');
const btnPreviewCopy = document.getElementById('btn-preview-copy');
const btnPreviewOpen = document.getElementById('btn-preview-open');
const previewTitle = document.getElementById('preview-title');
const previewSubtitle = document.getElementById('preview-subtitle');
const previewRendered = document.getElementById('preview-rendered');
const previewRaw = document.getElementById('preview-raw');
const drawerTabs = document.querySelectorAll('.drawer-tab');
const drawerViews = document.querySelectorAll('.drawer-view-content');

// Active Preview State
let activePreviewMarkdown = "";
let activePreviewOutputPath = "";

// ----------------------------------------------------
// Initialization
// ----------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    loadHistory();
    setupEventListeners();
    
    // Start background ping loop to keep server alive
    pingServer();
    setInterval(pingServer, 3000);
});

async function pingServer() {
    try {
        await fetch('/api/ping');
    } catch (err) {
        console.warn("Ping failed (server may be offline)", err);
    }
}

// ----------------------------------------------------
// Navigation Tab Logic
// ----------------------------------------------------
function setupEventListeners() {
    // Sidebar Navigation
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.getAttribute('data-tab');
            
            navItems.forEach(n => n.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));
            
            item.classList.add('active');
            document.getElementById(tabId).classList.add('active');
            
            if (tabId === 'history-tab') {
                loadHistory();
            }
        });
    });

    // File Selection Buttons
    btnSelectFiles.addEventListener('click', selectFiles);
    btnSelectFolder.addEventListener('click', selectFolder);

    // URL Conversion Button
    btnConvertUrl.addEventListener('click', convertUrl);
    inputUrl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            convertUrl();
        }
    });

    // Queue Controls
    btnClearQueue.addEventListener('click', clearQueue);
    btnStartConvert.addEventListener('click', startConversion);

    // History controls
    btnClearHistory.addEventListener('click', clearHistory);

    // Settings Toggle Panels
    checkUseLlm.addEventListener('change', () => {
        if (checkUseLlm.checked) {
            llmFields.classList.remove('collapsed');
        } else {
            llmFields.classList.add('collapsed');
        }
    });

    checkUseDocIntel.addEventListener('change', () => {
        if (checkUseDocIntel.checked) {
            docintelFields.classList.remove('collapsed');
        } else {
            docintelFields.classList.add('collapsed');
        }
    });

    // Settings Form Submit
    settingsForm.addEventListener('submit', saveSettings);

    // Drag and Drop files
    setupDragAndDrop();

    // Drawer tabs
    drawerTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const viewId = tab.getAttribute('data-view');
            
            drawerTabs.forEach(t => t.classList.remove('active'));
            drawerViews.forEach(v => v.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(viewId).classList.add('active');
        });
    });

    // Drawer close events
    btnPreviewClose.addEventListener('click', closePreviewDrawer);
    drawerOverlay.addEventListener('click', closePreviewDrawer);
    
    // Drawer action events
    btnPreviewCopy.addEventListener('click', copyPreviewMarkdown);
    btnPreviewOpen.addEventListener('click', openPreviewFile);
}

// ----------------------------------------------------
// Drag & Drop Handling (Supports Web Browser File Upload)
// ----------------------------------------------------
function setupDragAndDrop() {
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('hover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('hover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleDroppedFiles(files);
    }, false);

    // Clicking the dropzone triggers file picker
    dropZone.addEventListener('click', (e) => {
        if (e.target.closest('.btn')) return;
        selectFiles();
    });
}

async function handleDroppedFiles(files) {
    if (!files || files.length === 0) return;
    
    const addedFiles = [];
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        if (file.path) {
            const name = file.name;
            const size = file.size;
            const ext = name.substring(name.lastIndexOf('.')).toLowerCase();
            
            addedFiles.push({
                path: file.path,
                name: name,
                size: size,
                extension: ext
            });
        } else {
            // Standard Web Browser Drag & Drop (Multipart upload route)
            const fileObj = {
                path: "UPLOADED:" + file.name,
                name: file.name,
                size: file.size,
                extension: file.name.substring(file.name.lastIndexOf('.')).toLowerCase(),
                status: 'converting',
                error: '',
                outputPath: '',
                outputName: '',
                markdown: ''
            };
            conversionQueue.push(fileObj);
            renderQueueTable();
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const res = await response.json();
                if (res.success) {
                    fileObj.status = 'success';
                    fileObj.outputPath = res.output_path;
                    fileObj.outputName = res.output_name;
                    fileObj.markdown = res.markdown;
                } else {
                    fileObj.status = 'error';
                    fileObj.error = res.error;
                }
            } catch (err) {
                fileObj.status = 'error';
                fileObj.error = err.message || "Upload and convert failed";
            }
            renderQueueTable();
            loadHistory();
        }
    }
    
    if (addedFiles.length > 0) {
        addFilesToQueue(addedFiles);
    }
}

// ----------------------------------------------------
// File Selection & URL Converter
// ----------------------------------------------------

async function selectFiles() {
    try {
        const files = await pywebview.api.select_files();
        if (files && files.length > 0) {
            addFilesToQueue(files);
        }
    } catch (err) {
        console.error("Error choosing files", err);
    }
}

async function selectFolder() {
    try {
        const folderPath = await pywebview.api.select_folder();
        if (folderPath) {
            alert(`Selected folder: ${folderPath}\nTo convert files inside, you can select files using the 'Browse Files' button or drop them here.`);
        }
    } catch (err) {
        console.error("Error choosing folder", err);
    }
}

async function convertUrl() {
    const url = inputUrl.value.trim();
    if (!url) {
        alert("Please enter a Webpage or YouTube URL.");
        return;
    }
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
        alert("Please enter a valid URL starting with http:// or https://");
        return;
    }

    // Disable controls
    btnConvertUrl.disabled = true;
    inputUrl.disabled = true;
    btnConvertUrl.innerText = "Converting Link...";

    // Append URL conversion item to active queue list
    const fileObj = {
        path: url,
        name: url,
        size: 0,
        extension: "URL",
        status: 'converting',
        error: '',
        outputPath: '',
        outputName: '',
        markdown: ''
    };
    conversionQueue.push(fileObj);
    renderQueueTable();

    try {
        const response = await fetch('/api/convert_url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        const res = await response.json();
        if (res.success) {
            fileObj.status = 'success';
            fileObj.outputPath = res.output_path;
            fileObj.outputName = res.output_name;
            fileObj.markdown = res.markdown;
            
            // Clear URL bar
            inputUrl.value = "";
        } else {
            fileObj.status = 'error';
            fileObj.error = res.error;
        }
    } catch (err) {
        fileObj.status = 'error';
        fileObj.error = err.message || "Failed to convert URL.";
    }

    // Re-enable
    btnConvertUrl.disabled = false;
    inputUrl.disabled = false;
    btnConvertUrl.innerText = "Convert URL";

    renderQueueTable();
    loadHistory();
}

// ----------------------------------------------------
// Settings & History Synchronization
// ----------------------------------------------------

async function loadSettings() {
    try {
        appSettings = await pywebview.api.get_settings();
        applySettingsToUI();
    } catch (err) {
        console.error("Error loading settings", err);
    }
}

function applySettingsToUI() {
    checkUseLlm.checked = !!appSettings.use_llm;
    document.getElementById('api-key').value = appSettings.api_key || "";
    document.getElementById('api-base').value = appSettings.api_base || "";
    document.getElementById('llm-model').value = appSettings.llm_model || "gpt-4o";
    document.getElementById('llm-prompt').value = appSettings.llm_prompt || "Write a detailed caption for this image.";

    checkUseDocIntel.checked = !!appSettings.use_docintel;
    document.getElementById('docintel-endpoint').value = appSettings.docintel_endpoint || "";
    document.getElementById('docintel-key').value = appSettings.docintel_key || "";

    if (appSettings.use_llm) llmFields.classList.remove('collapsed');
    if (appSettings.use_docintel) docintelFields.classList.remove('collapsed');

    updateIndicators();
}

function updateIndicators() {
    if (appSettings.use_llm && appSettings.api_key) {
        llmIndicator.querySelector('.dot').className = 'dot green';
        llmIndicator.querySelector('span').innerText = `LLM describing images with ${appSettings.llm_model || 'gpt-4o'}`;
    } else {
        llmIndicator.querySelector('.dot').className = 'dot red';
        llmIndicator.querySelector('span').innerText = 'LLM image description is disabled';
    }

    if (appSettings.use_docintel && appSettings.docintel_endpoint) {
        docintelIndicator.querySelector('.dot').className = 'dot green';
        docintelIndicator.querySelector('span').innerText = 'Azure Document Intelligence enabled';
    } else {
        docintelIndicator.querySelector('.dot').className = 'dot red';
        docintelIndicator.querySelector('span').innerText = 'Azure Doc Intel is disabled';
    }
}

async function saveSettings(e) {
    e.preventDefault();
    
    appSettings = {
        use_llm: checkUseLlm.checked,
        api_key: document.getElementById('api-key').value,
        api_base: document.getElementById('api-base').value,
        llm_model: document.getElementById('llm-model').value,
        llm_prompt: document.getElementById('llm-prompt').value,
        use_docintel: checkUseDocIntel.checked,
        docintel_endpoint: document.getElementById('docintel-endpoint').value,
        docintel_key: document.getElementById('docintel-key').value
    };

    try {
        await pywebview.api.save_settings(appSettings);
        updateIndicators();
        showSaveSuccess();
    } catch (err) {
        console.error("Error saving settings", err);
    }
}

function showSaveSuccess() {
    settingsSaveSuccess.classList.add('show');
    setTimeout(() => {
        settingsSaveSuccess.classList.remove('show');
    }, 3000);
}

async function loadHistory() {
    try {
        appHistory = await pywebview.api.get_history();
        renderHistoryTable();
    } catch (err) {
        console.error("Error loading history", err);
    }
}

async function clearHistory() {
    if (confirm("Are you sure you want to clear your conversion history?")) {
        try {
            await pywebview.api.clear_history();
            loadHistory();
        } catch (err) {
            console.error("Error clearing history", err);
        }
    }
}

function renderHistoryTable() {
    if (appHistory.length === 0) {
        historyList.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">No history recorded yet. Converted files will appear here.</td>
            </tr>
        `;
        return;
    }

    historyList.innerHTML = "";
    appHistory.forEach((entry, idx) => {
        const row = document.createElement('tr');
        
        const badgeClass = entry.status === 'success' ? 'badge-success' : 'badge-error';
        const badgeText = entry.status === 'success' ? 'Success' : 'Error';
        
        row.innerHTML = `
            <td class="table-source-cell" title="${entry.source_path}">${entry.source_name}</td>
            <td title="${entry.output_path || ''}">${entry.output_name || 'N/A'}</td>
            <td>${entry.timestamp}</td>
            <td><span class="badge ${badgeClass}">${badgeText}</span></td>
            <td>
                <div class="drawer-actions">
                    ${entry.status === 'success' ? `
                        <button class="btn btn-secondary btn-sm btn-view-md" data-idx="${idx}">View Preview</button>
                        <button class="btn btn-icon btn-sm btn-open-folder" data-path="${entry.output_path}" title="Open Folder">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                        </button>
                    ` : `
                        <span class="text-muted" title="${entry.error || ''}">Hover to view error</span>
                    `}
                </div>
            </td>
        `;
        
        historyList.appendChild(row);
    });

    document.querySelectorAll('.btn-view-md').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = parseInt(e.target.getAttribute('data-idx'));
            const entry = appHistory[idx];
            openPreviewFromFile(entry.output_path, entry.output_name);
        });
    });

    document.querySelectorAll('.btn-open-folder').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const path = e.target.closest('.btn-open-folder').getAttribute('data-path');
            pywebview.api.open_folder_containing(path);
        });
    });
}

// ----------------------------------------------------
// Conversion Queue Mechanics
// ----------------------------------------------------

function addFilesToQueue(files) {
    files.forEach(file => {
        if (!conversionQueue.some(q => q.path === file.path)) {
            conversionQueue.push({
                ...file,
                status: 'pending',
                error: '',
                outputPath: '',
                outputName: '',
                markdown: ''
            });
        }
    });

    renderQueueTable();
}

function renderQueueTable() {
    if (conversionQueue.length === 0) {
        queueCard.style.display = 'none';
        return;
    }

    queueCard.style.display = 'flex';
    queueCount.innerText = conversionQueue.length;
    queueList.innerHTML = "";

    conversionQueue.forEach((file, idx) => {
        const row = document.createElement('tr');
        
        let badgeHTML = "";
        if (file.status === 'pending') {
            badgeHTML = `<span class="badge badge-pending">Queued</span>`;
        } else if (file.status === 'converting') {
            badgeHTML = `<span class="badge badge-converting">Converting...</span>`;
        } else if (file.status === 'success') {
            badgeHTML = `<span class="badge badge-success">Success</span>`;
        } else if (file.status === 'error') {
            badgeHTML = `<span class="badge badge-error" title="${file.error}">Error</span>`;
        }

        const formattedSize = formatBytes(file.size);
        
        row.innerHTML = `
            <td class="table-source-cell" title="${file.path}"><strong>${file.name}</strong></td>
            <td>${file.extension.toUpperCase().replace('.', '')}</td>
            <td>${formattedSize}</td>
            <td>${file.outputName || '<span class="text-muted">Auto-naming...</span>'}</td>
            <td>${badgeHTML}</td>
            <td>
                ${file.status === 'success' ? `
                    <button class="btn btn-secondary btn-sm btn-queue-view" data-idx="${idx}">Preview</button>
                ` : `
                    <button class="btn btn-icon btn-sm btn-remove-queue" data-idx="${idx}" title="Remove file" ${isConverting ? 'disabled' : ''}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                `}
            </td>
        `;
        
        queueList.appendChild(row);
    });

    document.querySelectorAll('.btn-remove-queue').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = parseInt(e.target.closest('.btn-remove-queue').getAttribute('data-idx'));
            conversionQueue.splice(idx, 1);
            renderQueueTable();
        });
    });

    document.querySelectorAll('.btn-queue-view').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = parseInt(e.target.getAttribute('data-idx'));
            const file = conversionQueue[idx];
            showPreviewDrawer(file.outputName, file.outputPath, file.markdown);
        });
    });
}

function clearQueue() {
    if (isConverting) return;
    conversionQueue = [];
    renderQueueTable();
}

async function startConversion() {
    if (isConverting || conversionQueue.length === 0) return;
    
    isConverting = true;
    btnStartConvert.disabled = true;
    btnClearQueue.disabled = true;
    btnSelectFiles.disabled = true;
    btnSelectFolder.disabled = true;

    for (let i = 0; i < conversionQueue.length; i++) {
        const file = conversionQueue[i];
        if (file.status === 'success' || file.path.startsWith("UPLOADED:") || file.extension === "URL") continue;

        file.status = 'converting';
        renderQueueTable();

        try {
            const res = await pywebview.api.convert_file(file.path);
            if (res.success) {
                file.status = 'success';
                file.outputPath = res.output_path;
                file.outputName = res.output_name;
                file.markdown = res.markdown;
            } else {
                file.status = 'error';
                file.error = res.error;
            }
        } catch (err) {
            file.status = 'error';
            file.error = err.message || "Unknown execution error";
        }
        
        renderQueueTable();
    }

    isConverting = false;
    btnStartConvert.disabled = false;
    btnClearQueue.disabled = false;
    btnSelectFiles.disabled = false;
    btnSelectFolder.disabled = false;
    
    loadHistory();
}

// ----------------------------------------------------
// Preview Drawer
// ----------------------------------------------------

async function openPreviewFromFile(filePath, fileName) {
    try {
        const markdown = await pywebview.api.read_text_file(filePath);
        showPreviewDrawer(fileName, filePath, markdown);
    } catch (err) {
        showPreviewDrawer(fileName, filePath, `Error reading file: ${err.message}`);
    }
}

function showPreviewDrawer(title, outputPath, markdown) {
    activePreviewMarkdown = markdown;
    activePreviewOutputPath = outputPath;

    previewTitle.innerText = title;
    previewSubtitle.innerText = outputPath;
    previewSubtitle.setAttribute('title', outputPath);
    
    previewRaw.value = markdown;
    
    if (window.marked) {
        previewRendered.innerHTML = marked.parse(markdown);
    } else {
        previewRendered.innerHTML = `<pre style="white-space: pre-wrap;">${markdown}</pre>`;
    }

    drawerTabs.forEach(t => t.classList.remove('active'));
    drawerViews.forEach(v => v.classList.remove('active'));
    
    drawerTabs[0].classList.add('active');
    document.getElementById('rendered-view').classList.add('active');

    previewDrawer.classList.add('open');
    drawerOverlay.classList.add('active');
}

function closePreviewDrawer() {
    previewDrawer.classList.remove('open');
    drawerOverlay.classList.remove('active');
}

function copyPreviewMarkdown() {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(activePreviewMarkdown).then(() => {
            alert("Markdown copied to clipboard!");
        }).catch(err => {
            console.error("Clipboard copy failed", err);
        });
    } else {
        previewRaw.select();
        document.execCommand('copy');
        alert("Markdown copied to clipboard!");
    }
}

// Opens the converted file locally
function openPreviewFile() {
    if (activePreviewOutputPath) {
        pywebview.api.open_path(activePreviewOutputPath);
    }
}

// ----------------------------------------------------
// Utility Functions
// ----------------------------------------------------

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
