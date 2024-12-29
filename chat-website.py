import http.server
import socketserver
import json
from urllib.parse import parse_qs
from datetime import datetime
import os

# 配置
CONFIG = {
    'MAX_MESSAGES': 100,  # 最大消息数量
    'STORAGE_FILE': 'chat_messages.txt',  # 存储文件名
    'PORT': 8000  # 服务器端口
}

class MessageManager:
    def __init__(self):
        self.messages = []
        self.load_messages()

    def load_messages(self):
        """从文件加载消息"""
        try:
            if os.path.exists(CONFIG['STORAGE_FILE']):
                with open(CONFIG['STORAGE_FILE'], 'r', encoding='utf-8') as f:
                    self.messages = json.loads(f.read())
        except Exception as e:
            print(f"加载消息出错: {e}")
            self.messages = []

    def save_messages(self):
        """保存消息到文件"""
        try:
            with open(CONFIG['STORAGE_FILE'], 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存消息出错: {e}")

    def add_message(self, message):
        """添加新消息"""
        self.messages.append(message)
        if len(self.messages) > CONFIG['MAX_MESSAGES']:
            self.messages.pop(0)
        self.save_messages()

    def get_messages(self):
        """获取所有消息"""
        return self.messages

message_manager = MessageManager()

class ChatHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <title>局域网聊天室</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --primary-color: #4a90e2;
            --secondary-color: #f5f5f5;
            --border-color: #e0e0e0;
            --success-color: #4caf50;
            --text-primary: #333;
            --text-secondary: #666;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background: #f9f9f9;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }

        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
            padding: 24px;
        }

        h1 {
            color: var(--primary-color);
            text-align: center;
            margin-bottom: 20px;
            font-size: 28px;
        }

        .system-info {
            color: var(--text-secondary);
            text-align: center;
            margin-bottom: 20px;
            font-size: 14px;
            padding: 8px;
            background: var(--secondary-color);
            border-radius: 6px;
        }

        #messages {
            height: 500px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 20px;
            padding: 16px;
            background: white;
        }

        .message {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 16px;
            animation: fadeIn 0.3s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message-content {
            flex-grow: 1;
            background: var(--secondary-color);
            padding: 12px;
            border-radius: 8px;
            position: relative;
        }

        .message-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }

        .timestamp {
            color: var(--text-secondary);
            font-size: 12px;
        }

        .username {
            font-weight: 600;
            color: var(--primary-color);
        }

        .message-text {
            word-break: break-word;
        }

        .copy-btn {
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 6px 12px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s ease;
            color: var(--text-secondary);
        }

        .copy-btn:hover {
            background: var(--secondary-color);
            transform: translateY(-1px);
        }

        .copy-btn.copied {
            background: var(--success-color);
            color: white;
            border-color: var(--success-color);
        }

        .input-area {
            display: flex;
            gap: 12px;
        }

        input {
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.2s ease;
        }

        input:focus {
            outline: none;
            border-color: var(--primary-color);
        }

        #username {
            width: 150px;
        }

        #message {
            flex-grow: 1;
        }

        button {
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px 24px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        button:hover {
            background: #357abd;
            transform: translateY(-1px);
        }

        .hidden-textarea {
            position: fixed;
            top: -9999px;
            left: -9999px;
            opacity: 0;
        }

        /* 响应式设计 */
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }

            .container {
                padding: 16px;
            }

            .input-area {
                flex-direction: column;
            }

            #username {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>局域网聊天室</h1>
        <div class="system-info">最多显示最近 """ + str(CONFIG['MAX_MESSAGES']) + """ 条消息</div>
        <div id="messages"></div>
        <div class="input-area">
            <input type="text" id="username" placeholder="你的名字" autocomplete="off">
            <input type="text" id="message" placeholder="输入消息" autocomplete="off">
            <button onclick="sendMessage()">发送</button>
        </div>
    </div>
    <textarea id="copyTextarea" class="hidden-textarea"></textarea>

    <script>
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
            return `
                <div class="message">
                    <div class="message-content">
                        <div class="message-header">
                            <span class="timestamp">${msg.timestamp}</span>
                            <span class="username">${msg.username}</span>
                        </div>
                        <div class="message-text">${msg.message}</div>
                    </div>
                    <button class="copy-btn" onclick="copyMessage('${msg.message.replace(/'/g, "\\'")}', this)">复制</button>
                </div>
            `;
        }

        function sendMessage() {
            const username = document.getElementById('username').value.trim();
            const message = document.getElementById('message').value.trim();
            
            if (!username || !message) {
                alert('请输入用户名和消息！');
                return;
            }

            const messageInput = document.getElementById('message');
            messageInput.disabled = true;

            fetch('/send', {
                method: 'POST',
                body: JSON.stringify({ username, message })
            }).then(() => {
                messageInput.value = '';
                messageInput.disabled = false;
                messageInput.focus();
                fetchMessages();
            }).catch(() => {
                messageInput.disabled = false;
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

        // 创建消息元素的函数保持不变
        function createMessageElement(msg) {
            return `
                <div class="message">
                    <div class="message-content">
                        <div class="message-header">
                            <span class="timestamp">${msg.timestamp}</span>
                            <span class="username">${msg.username}</span>
                        </div>
                        <div class="message-text">${msg.message}</div>
                    </div>
                    <button class="copy-btn" onclick="copyMessage('${msg.message.replace(/'/g, "\\'")}', this)">复制</button>
                </div>
            `;
        }

        // 修改轮询间隔为更长时间
        const pollInterval = 2000; // 2秒
        let lastPollTime = Date.now();
        
        function pollMessages() {
            const now = Date.now();
            // 如果距离上次更新不到 pollInterval，跳过这次更新
            if (now - lastPollTime < pollInterval) {
                return;
            }
            lastPollTime = now;
            fetchMessages();
        }

        // 初始化
        fetchMessages();
        setInterval(pollMessages, 300); // 使用更短的检查间隔，但实际更新遵循 pollInterval

    </script>
</body>
</html>
            """
            self.wfile.write(html.encode())

        elif self.path == '/messages':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(message_manager.get_messages()).encode())

    def do_POST(self):
        if self.path == '/send':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            data['timestamp'] = datetime.now().strftime('%H:%M:%S')
            message_manager.add_message(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())

def run_server(port=None):
    if port is not None:
        CONFIG['PORT'] = port
    
    handler = ChatHandler
    with socketserver.TCPServer(("", CONFIG['PORT']), handler) as httpd:
        print(f"服务器运行在 http://localhost:{CONFIG['PORT']}/")
        print(f"消息将保存在: {os.path.abspath(CONFIG['STORAGE_FILE'])}")
        print(f"最多保存最近 {CONFIG['MAX_MESSAGES']} 条消息")
        httpd.serve_forever()

if __name__ == '__main__':
    run_server()