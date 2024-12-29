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

# 创建消息管理器实例
message_manager = MessageManager()

class ChatHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # 返回主页
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>局域网聊天室</title>
                <meta charset="utf-8">
                <style>
                    /* ... 之前的样式保持不变 ... */
                    
                    /* 添加隐藏文本框的样式 */
                    .hidden-textarea {
                        position: fixed;
                        top: -9999px;
                        left: -9999px;
                        opacity: 0;
                    }
                </style>
            </head>
            <body>
                <h1>局域网聊天室</h1>
                <div class="system-info">最多显示最近 """ + str(CONFIG['MAX_MESSAGES']) + """ 条消息</div>
                <div id="messages"></div>
                <input type="text" id="username" placeholder="你的名字" style="margin-right: 10px;">
                <input type="text" id="message" placeholder="输入消息">
                <button onclick="sendMessage()">发送</button>
                
                <!-- 添加用于复制的隐藏文本框 -->
                <textarea id="copyTextarea" class="hidden-textarea"></textarea>

                <script>
                    function copyMessage(message, button) {
                        // 首先尝试使用 Clipboard API
                        if (navigator.clipboard && window.isSecureContext) {
                            navigator.clipboard.writeText(message)
                                .then(() => showCopySuccess(button))
                                .catch(() => fallbackCopy(message, button));
                        } else {
                            // 如果 Clipboard API 不可用，使用后备方案
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
                                button.style.background = '#f0f0f0';
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

                    function fetchMessages() {
                        fetch('/messages')
                            .then(response => response.json())
                            .then(data => {
                                const messagesDiv = document.getElementById('messages');
                                messagesDiv.innerHTML = '';
                                data.forEach(msg => {
                                    messagesDiv.innerHTML += `
                                        <div class="message">
                                            <div class="message-content">
                                                <span class="timestamp">${msg.timestamp}</span>
                                                <strong>${msg.username}:</strong> ${msg.message}
                                            </div>
                                            <button class="copy-btn" onclick="copyMessage('${msg.message.replace(/'/g, "\\'")}', this)">复制</button>
                                        </div>
                                    `;
                                });
                                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                            });
                    }

                    function sendMessage() {
                        const username = document.getElementById('username').value;
                        const message = document.getElementById('message').value;
                        
                        if (!username || !message) {
                            alert('请输入用户名和消息！');
                            return;
                        }

                        fetch('/send', {
                            method: 'POST',
                            body: JSON.stringify({
                                username: username,
                                message: message
                            })
                        }).then(() => {
                            document.getElementById('message').value = '';
                            fetchMessages();
                        });
                    }

                    // 每秒更新消息
                    setInterval(fetchMessages, 1000);
                    
                    // 回车发送消息
                    document.getElementById('message').addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            sendMessage();
                        }
                    });

                    // 页面加载时获取消息
                    fetchMessages();
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

        elif self.path == '/messages':
            # 返回消息列表
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(message_manager.get_messages()).encode())

    def do_POST(self):
        if self.path == '/send':
            # 接收新消息
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # 添加时间戳
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