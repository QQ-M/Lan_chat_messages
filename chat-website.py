import http.server
import socketserver
import json
from urllib.parse import parse_qs
import cgi
from datetime import datetime
import os
import base64
import uuid

# 配置
CONFIG = {
    'MAX_MESSAGES': 100,  # 最大消息数量
    'STORAGE_FILE': 'chat_messages.txt',  # 存储文件名
    'PORT': 8000,  # 服务器端口
    'IMAGE_FOLDER': 'images'  # 图片存储文件夹
}

# 确保图片存储文件夹存在
os.makedirs(CONFIG['IMAGE_FOLDER'], exist_ok=True)

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
            
            with open('index.html', 'r', encoding='utf-8') as f:
                html = f.read()
            self.wfile.write(html.encode())

        elif self.path == '/messages':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(message_manager.get_messages()).encode())

        elif self.path.startswith(('/css/', '/js/')):
            try:
                file_path = os.path.join(os.getcwd(), self.path[1:])
                with open(file_path, 'rb') as f:
                    self.send_response(200)
                    if self.path.endswith('.css'):
                        self.send_header('Content-type', 'text/css')
                    elif self.path.endswith('.js'):
                        self.send_header('Content-type', 'application/javascript')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, 'File not found')

        elif self.path.startswith('/images/'):
            try:
                image_path = os.path.join(os.getcwd(), self.path[1:])
                with open(image_path, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'image/png')  # 根据需要调整内容类型
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, 'File not found')

    def do_POST(self):
        if self.path == '/send':
            content_type, pdict = cgi.parse_header(self.headers['Content-Type'])
            if content_type == 'multipart/form-data':
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST',
                             'CONTENT_TYPE': self.headers['Content-Type']}
                )
                
                username = form.getvalue('username')
                message = form.getvalue('message')
                image = form.getvalue('image')
                
                data = {
                    'username': username,
                    'message': message,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                
                if image:
                    # 检查image是否是文件对象
                    if hasattr(image, 'file'):
                        image_data = image.file.read()
                    # 检查image是否是base64编码的字符串
                    elif isinstance(image, str) and image.startswith('data:image'):
                        image_data = base64.b64decode(image.split(',')[1])
                    else:
                        image_data = image

                    image_filename = f"{uuid.uuid4()}.png"
                    image_path = os.path.join(CONFIG['IMAGE_FOLDER'], image_filename)
                    
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    
                    data['image'] = f"/images/{image_filename}"
                
                message_manager.add_message(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode())
            else:
                self.send_error(400, 'Bad Request: Expected multipart/form-data')

def run_server(port=None):
    if port is not None:
        CONFIG['PORT'] = port
    
    handler = ChatHandler
    with socketserver.TCPServer(("", CONFIG['PORT']), handler) as httpd:
        print(f"服务器运行在 http://localhost:{CONFIG['PORT']}/")
        print(f"消息将保存在: {os.path.abspath(CONFIG['STORAGE_FILE'])}")
        print(f"图片将保存在: {os.path.abspath(CONFIG['IMAGE_FOLDER'])}")
        print(f"最多保存最近 {CONFIG['MAX_MESSAGES']} 条消息")
        httpd.serve_forever()

if __name__ == '__main__':
    run_server()

