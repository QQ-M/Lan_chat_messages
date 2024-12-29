import http.server
import socketserver
import json
from urllib.parse import parse_qs
from datetime import datetime

# 存储聊天消息
messages = []

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
                    #messages {
                        height: 400px;
                        overflow-y: auto;
                        border: 1px solid #ccc;
                        margin-bottom: 10px;
                        padding: 10px;
                    }
                    .message {
                        margin-bottom: 10px;
                    }
                    .timestamp {
                        color: #666;
                        font-size: 0.8em;
                    }
                </style>
            </head>
            <body>
                <h1>局域网聊天室</h1>
                <div id="messages"></div>
                <input type="text" id="username" placeholder="你的名字" style="margin-right: 10px;">
                <input type="text" id="message" placeholder="输入消息">
                <button onclick="sendMessage()">发送</button>

                <script>
                    function fetchMessages() {
                        fetch('/messages')
                            .then(response => response.json())
                            .then(data => {
                                const messagesDiv = document.getElementById('messages');
                                messagesDiv.innerHTML = '';
                                data.forEach(msg => {
                                    messagesDiv.innerHTML += `
                                        <div class="message">
                                            <span class="timestamp">${msg.timestamp}</span>
                                            <strong>${msg.username}:</strong> ${msg.message}
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
            self.wfile.write(json.dumps(messages).encode())

    def do_POST(self):
        if self.path == '/send':
            # 接收新消息
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # 添加时间戳
            data['timestamp'] = datetime.now().strftime('%H:%M:%S')
            messages.append(data)
            
            # 只保留最近的100条消息
            if len(messages) > 100:
                messages.pop(0)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())

def run_server(port=8000):
    handler = ChatHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"服务器运行在 http://localhost:{port}/")
        httpd.serve_forever()

if __name__ == '__main__':
    run_server()
