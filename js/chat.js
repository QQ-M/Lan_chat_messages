let lastPollTime = Date.now();
const pollInterval = 2000; // 2秒

function copyMessage(message, button) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(message)
            .then(() => showCopySuccess(button))
            .catch(() => fallbackCopy(message, button));
    } else {
        fallbackCopy(message, button);
    }
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

function showCopySuccess(button) {
    button.textContent = '已复制';
    button.classList.add('copied');
    setTimeout(() => {
        button.textContent = '复制';
        button.classList.remove('copied');
    }, 1000);
}

function createMessageElement(msg) {
    let imageHtml = '';
    if (msg.image) {
        imageHtml = `<img src="${msg.image}" alt="Uploaded image" class="message-image">`;
    }
    return `
        <div class="message">
            <div class="message-content">
                <div class="message-header">
                    <span class="timestamp">${msg.timestamp}</span>
                    <span class="username">${msg.username}</span>
                </div>
                <div class="message-text">${msg.message}</div>
                ${imageHtml}
            </div>
            <button class="copy-btn" onclick="copyMessage('${msg.message.replace(/'/g, "\\'")}', this)">复制</button>
        </div>
    `;
}

function sendMessage() {
    const username = document.getElementById('username').value.trim();
    const message = document.getElementById('message').value.trim();
    const imageUpload = document.getElementById('image-upload');
    
    if (!username || (!message && !imageUpload.files[0])) {
        alert('请输入用户名和消息或选择图片！');
        return;
    }

    const messageInput = document.getElementById('message');
    messageInput.disabled = true;

    const formData = new FormData();
    formData.append('username', username);
    formData.append('message', message);

    if (imageUpload.files[0]) {
        formData.append('image', imageUpload.files[0]);
        sendFormData(formData);
    } else {
        sendFormData(formData);
    }
}

function sendFormData(formData) {
    fetch('/send', {
        method: 'POST',
        body: formData
    }).then(() => {
        document.getElementById('message').value = '';
        document.getElementById('message').disabled = false;
        document.getElementById('message').focus();
        document.getElementById('image-upload').value = '';
        document.getElementById('image-preview').style.display = 'none';
        fetchMessages();
    }).catch(() => {
        document.getElementById('message').disabled = false;
    });
}

function fetchMessages() {
    fetch('/messages')
        .then(response => response.json())
        .then(data => {
            const messagesDiv = document.getElementById('messages');
            const wasAtBottom = messagesDiv.scrollHeight - messagesDiv.scrollTop <= messagesDiv.clientHeight + 10;
            
            // 获取现有消息的数量
            const existingMessages = messagesDiv.children;
            const currentLength = existingMessages.length;
            
            // 如果消息数量或内容有变化才更新
            if (currentLength !== data.length || needsUpdate(existingMessages, data)) {
                // 记住当前滚动位置
                const oldScrollHeight = messagesDiv.scrollHeight;
                const oldScrollTop = messagesDiv.scrollTop;
                
                // 更新消息
                messagesDiv.innerHTML = data.map(createMessageElement).join('');
                
                // 恢复滚动位置
                if (wasAtBottom) {
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                } else {
                    const newScrollHeight = messagesDiv.scrollHeight;
                    const scrollDiff = newScrollHeight - oldScrollHeight;
                    messagesDiv.scrollTop = oldScrollTop + scrollDiff;
                }
            }
        });
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

// 添加图片预览功能
function setupImageUpload() {
    document.getElementById('image-upload').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const preview = document.getElementById('image-preview');
                preview.src = e.target.result;
                preview.style.display = 'inline-block';
            };
            reader.readAsDataURL(file);
        }
    });
}

// 添加粘贴图片功能
function setupPasteListener() {
    document.addEventListener('paste', function(event) {
        const items = (event.clipboardData || event.originalEvent.clipboardData).items;
        for (let index in items) {
            const item = items[index];
            if (item.kind === 'file') {
                const blob = item.getAsFile();
                const reader = new FileReader();
                reader.onload = function(event) {
                    const imagePreview = document.getElementById('image-preview');
                    imagePreview.src = event.target.result;
                    imagePreview.style.display = 'inline-block';
                    
                    // 创建一个新的 File 对象并将其添加到 image-upload 输入
                    const imageFile = new File([blob], "pasted-image.png", { type: "image/png" });
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(imageFile);
                    document.getElementById('image-upload').files = dataTransfer.files;
                };
                reader.readAsDataURL(blob);
            }
        }
    });
}

// 初始化
function init() {
    document.getElementById('max-messages').textContent = 100; // 假设CONFIG.MAX_MESSAGES为100
    setupImageUpload();
    setupPasteListener();
    fetchMessages();
    setInterval(pollMessages, 300); // 使用更短的检查间隔，但实际更新遵循 pollInterval
}

// 当DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

