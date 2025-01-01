import http.server
import socketserver
import json
from urllib.parse import parse_qs, quote
import cgi
from datetime import datetime
import os
import base64
import uuid
import mimetypes
from socketserver import ThreadingMixIn
import chardet
import re

# 配置
CONFIG = {
    'MAX_MESSAGES': 100,  # 最大消息数量
    'STORAGE_FILE': 'chat_messages.txt',  # 存储文件名
    'PORT': 8000,  # 服务器端口
    'IMAGE_FOLDER': 'images',  # 图片存储文件夹
    'FILES_FOLDER': 'files' # 文件存储文件夹
}

# 确保图片存储文件夹存在
os.makedirs(CONFIG['IMAGE_FOLDER'], exist_ok=True)
os.makedirs(CONFIG['FILES_FOLDER'], exist_ok=True)

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

def sanitize_filename(filename):
    """Sanitize filename to be URL-safe"""
    # Remove any non-URL-safe characters
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    # Ensure the filename is not empty
    if not safe_filename:
        safe_filename = str(uuid.uuid4())
    return safe_filename

def detect_encoding(file_path):
    """Detect the encoding of a file"""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def read_file_preview(file_path, num_lines=10):
    """Read the first num_lines of a file with proper encoding"""
    encoding = detect_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            preview = ''.join(f.readlines()[:num_lines])
        return preview
    except UnicodeDecodeError:
        return "无法预览文件内容。可能是二进制文件或使用了不支持的编码。"

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

        elif self.path.startswith(('/images/', '/files/')):
            try:
                file_path = os.path.join(os.getcwd(), self.path[1:])
                with open(file_path, 'rb') as f:
                    self.send_response(200)
                    content_type, _ = mimetypes.guess_type(file_path)
                    self.send_header('Content-type', content_type if content_type else 'application/octet-stream')
                    self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, 'File not found')
        else:
            self.send_error(404, 'Not Found')

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
                
                if 'file' in form:
                    file_item = form['file']
                    if file_item.filename:
                        original_filename = os.path.basename(file_item.filename)
                        safe_filename = sanitize_filename(original_filename)
                        file_path = os.path.join(CONFIG['FILES_FOLDER'], safe_filename)
                        
                        # If a file with the same name exists, add a UUID to make it unique
                        if os.path.exists(file_path):
                            name, ext = os.path.splitext(safe_filename)
                            safe_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
                            file_path = os.path.join(CONFIG['FILES_FOLDER'], safe_filename)
                        
                        with open(file_path, 'wb') as f:
                            f.write(file_item.file.read())
                        
                        if safe_filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                            data['image'] = f"/files/{quote(safe_filename)}"
                        else:
                            data['file'] = f"/files/{quote(safe_filename)}"
                            data['original_filename'] = original_filename
                            if safe_filename.lower().endswith('.txt'):
                                preview = read_file_preview(file_path)
                                data['preview'] = preview

                message_manager.add_message(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode())
            else:
                self.send_error(400, 'Bad Request: Expected multipart/form-data')

class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""

def run_server(port=None):
    if port is not None:
        CONFIG['PORT'] = port
    
    handler = ChatHandler
    with ThreadedHTTPServer(("", CONFIG['PORT']), handler) as httpd:
        print(f"服务器运行在 http://localhost:{CONFIG['PORT']}/")
        print(f"消息将保存在: {os.path.abspath(CONFIG['STORAGE_FILE'])}")
        print(f"图片将保存在: {os.path.abspath(CONFIG['IMAGE_FOLDER'])}")
        print(f"文件将保存在: {os.path.abspath(CONFIG['FILES_FOLDER'])}")
        print(f"最多保存最近 {CONFIG['MAX_MESSAGES']} 条消息")
        httpd.serve_forever()

if __name__ == '__main__':
    run_server()

