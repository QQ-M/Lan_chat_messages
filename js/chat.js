let lastPollTime = Date.now();
const pollInterval = 2000; // 2秒

function copyMessage(message, button) {
    // 创建临时 textarea 元素
    const textarea = document.createElement('textarea');
    textarea.value = message;
    textarea.classList.add('hidden-textarea');
    document.body.appendChild(textarea);
    
    try {
        // 选择文本
        textarea.select();
        textarea.setSelectionRange(0, 99999); // 用于移动设备
        
        // 执行复制命令
        const successful = document.execCommand('copy');
        if (successful) {
            showCopySuccess(button);
        } else {
            throw new Error('Copy command failed');
        }
    } catch (err) {
        console.error('复制失败:', err);
        button.textContent = '复制失败';
        button.style.background = '#ffcccc';
        setTimeout(() => {
            button.textContent = '复制';
            button.style.background = '';
        }, 1000);
    } finally {
        // 清理：移除临时元素
        document.body.removeChild(textarea);
    }
}

function showCopySuccess(button) {
    button.textContent = '已复制';
    button.classList.add('copied');
    setTimeout(() => {
        button.textContent = '复制';
        button.classList.remove('copied');
    }, 1000);
}

function fallbackCopy(message, button) {
    const textarea = document.getElementById('copyTextarea');
    textarea.value = message;
    textarea.select();
    
    try {
        document.execCommand('copy');
        showCopySuccess(button);
    } catch (err) {
        console.error('复制失败:', err);
        button.textContent = '复制失败';
        button.style.background = '#ffcccc';
        setTimeout(() => {
            button.textContent = '复制';
            button.style.background = '';
        }, 1000);
    }
}


// 检查消息是否需要更新
function needsUpdate(existingMessages, newData) {
    if (existingMessages.length !== newData.length) return true;
    
    for (let i = 0; i < existingMessages.length; i++) {
        const existingMsg = existingMessages[i];
        const newMsg = newData[i];
        
        // 获取现有消息的内容
        const existingTimestamp = existingMsg.querySelector('.timestamp').textContent;
        const existingUsername = existingMsg.querySelector('.username').textContent;
        const existingText = existingMsg.querySelector('.message-text').textContent;
        
        // 比较消息内容
        if (existingTimestamp !== newMsg.timestamp ||
            existingUsername !== newMsg.username ||
            existingText !== newMsg.message) {
            return true;
        }
    }
    return false;
}

function pollMessages() {
    const now = Date.now();
    // 如果距离上次更新不到 pollInterval，跳过这次更新
    if (now - lastPollTime < pollInterval) {
        return;
    }
    lastPollTime = now;
    fetchMessages();
}

// 添加文件上传预览功能
function setupFileUpload() {
    const fileUpload = document.getElementById('file-upload');
    fileUpload.addEventListener('change', function(e) {
        if (e.target.files[0]) {
            handlePastedFile(e.target.files[0]);
        }
    });
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else return (bytes / 1048576).toFixed(2) + ' MB';
}


// 添加自动滚动函数
function scrollToBottom() {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function createMessageElement(msg) {
    let attachmentHtml = '';
    if (msg.image) {
        attachmentHtml = `<img src="${msg.image}" alt="Uploaded image" class="message-image" onload="scrollToBottom()">`;
    } else if (msg.file) {
        attachmentHtml = `<a href="${msg.file}" class="file-download" download>下载文件</a>`;
        if (msg.preview) {
            attachmentHtml += `<pre class="file-preview">${msg.preview}</pre>`;
        }
    }
    return `
        <div class="message">
            <div class="message-content">
                <div class="message-header">
                    <span class="timestamp">${msg.timestamp}</span>
                    <span class="username">${msg.username}</span>
                </div>
                <div class="message-text">${msg.message}</div>
                ${attachmentHtml}
            </div>
            <button class="copy-btn" onclick="copyMessage('${msg.message.replace(/'/g, "\\'")}', this)">复制</button>
        </div>
    `;
}

function fetchMessages() {
    fetch('/messages')
        .then(response => response.json())
        .then(data => {
            const messagesDiv = document.getElementById('messages');
            
            // 获取现有消息的数量
            const existingMessages = messagesDiv.children;
            const currentLength = existingMessages.length;
            
            // 如果消息数量或内容有变化才更新
            if (currentLength !== data.length || needsUpdate(existingMessages, data)) {
                messagesDiv.innerHTML = data.map(createMessageElement).join('');
                // 自动滚动到底部
                scrollToBottom();
            }
        });
}

function sendMessage() {
    const username = document.getElementById('username').value.trim();
    const message = document.getElementById('message').value.trim();
    const fileUpload = document.getElementById('file-upload');
    
    if (!username || (!message && !fileUpload.files[0])) {
        alert('请输入用户名和消息或选择文件！');
        return;
    }

    const formData = new FormData();
    formData.append('username', username);
    formData.append('message', message);

    if (fileUpload.files[0]) {
        formData.append('file', fileUpload.files[0]);
    }

    sendFormData(formData);
}

function sendFormData(formData) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/send', true);

    xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            updateProgressBar(percentComplete);
        }
    };

    xhr.onload = function() {
        if (xhr.status === 200) {
            document.getElementById('message').value = '';
            document.getElementById('file-upload').value = '';
            document.getElementById('file-preview').innerHTML = '';
            fetchMessages();
        }
    };

    xhr.send(formData);
}

function updateProgressBar(percent) {
    const progressBar = document.getElementById('upload-progress');
    progressBar.style.width = percent + '%';
    if (percent === 100) {
        setTimeout(() => {
            progressBar.style.width = '0%';
        }, 1000);
    }
}

// 初始化
function init() {
    document.getElementById('max-messages').textContent = 100;
    setupFileUpload();
    setupPasteListener();
    fetchMessages(); // 初始加载消息
    setInterval(pollMessages, 300);
    
    // 添加消息输入框的回车键发送功能
    document.getElementById('message').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

function setupPasteListener() {
    document.addEventListener('paste', function(event) {
        const items = (event.clipboardData || event.originalEvent.clipboardData).items;
        for (let index in items) {
            const item = items[index];
            if (item.kind === 'file') {
                const file = item.getAsFile();
                handlePastedFile(file);
            }
        }
    });
}

function handlePastedFile(file) {
    const fileUpload = document.getElementById('file-upload');
    const filePreview = document.getElementById('file-preview');
    
    // Create a new File object with a unique name
    const uniqueFileName = `pasted-file-${Date.now()}-${file.name}`;
    const newFile = new File([file], uniqueFileName, { type: file.type });
    
    // Update the file input
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(newFile);
    fileUpload.files = dataTransfer.files;
    
    // Show preview
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            filePreview.innerHTML = `<img src="${e.target.result}" alt="File preview" class="file-preview-image">`;
        };
        reader.readAsDataURL(file);
    } else {
        filePreview.innerHTML = `<div class="file-preview-info">${newFile.name} (${formatFileSize(newFile.size)})</div>`;
    }
}

// 当DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

