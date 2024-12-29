<?php
// Configuration
define('MAX_MESSAGES', 100);
define('STORAGE_FILE', 'chat_messages.txt');

class MessageManager {
    private $messages = [];

    public function __construct() {
        $this->loadMessages();
    }

    private function loadMessages() {
        try {
            if (file_exists(STORAGE_FILE)) {
                $content = file_get_contents(STORAGE_FILE);
                $this->messages = json_decode($content, true) ?? [];
            }
        } catch (Exception $e) {
            error_log("Error loading messages: " . $e->getMessage());
            $this->messages = [];
        }
    }

    private function saveMessages() {
        try {
            file_put_contents(STORAGE_FILE, json_encode($this->messages, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
        } catch (Exception $e) {
            error_log("Error saving messages: " . $e->getMessage());
        }
    }

    public function addMessage($message) {
        $this->messages[] = $message;
        if (count($this->messages) > MAX_MESSAGES) {
            array_shift($this->messages);
        }
        $this->saveMessages();
    }

    public function getMessages() {
        return $this->messages;
    }
}

// Handle API requests
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_GET['action']) && $_GET['action'] === 'send') {
    header('Content-Type: application/json');
    
    $data = json_decode(file_get_contents('php://input'), true);
    if (!empty($data['username']) && !empty($data['message'])) {
        $messageManager = new MessageManager();
        $data['timestamp'] = date('H:i:s');
        $messageManager->addMessage($data);
        echo json_encode(['status' => 'success']);
    } else {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Missing username or message']);
    }
    exit;
}

// Handle message retrieval
if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['action']) && $_GET['action'] === 'messages') {
    header('Content-Type: application/json');
    $messageManager = new MessageManager();
    echo json_encode($messageManager->getMessages());
    exit;
}

// Main HTML page
?>
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
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }
        .message-content {
            flex-grow: 1;
        }
        .timestamp {
            color: #666;
            font-size: 0.8em;
        }
        .system-info {
            color: #888;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .copy-btn {
            background: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 2px 8px;
            cursor: pointer;
            font-size: 0.8em;
        }
        .copy-btn:hover {
            background: #e0e0e0;
        }
        .copy-btn.copied {
            background: #90EE90;
            border-color: #008000;
        }
    </style>
</head>
<body>
    <h1>局域网聊天室</h1>
    <div class="system-info">最多显示最近 <?php echo MAX_MESSAGES; ?> 条消息</div>
    <div id="messages"></div>
    <input type="text" id="username" placeholder="你的名字" style="margin-right: 10px;">
    <input type="text" id="message" placeholder="输入消息">
    <button onclick="sendMessage()">发送</button>

    <script>
        function copyMessage(message, button) {
            navigator.clipboard.writeText(message).then(() => {
                button.textContent = '已复制';
                button.classList.add('copied');
                
                setTimeout(() => {
                    button.textContent = '复制';
                    button.classList.remove('copied');
                }, 1000);
            });
        }

        function fetchMessages() {
            fetch('?action=messages')
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

            fetch('?action=send', {
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

        setInterval(fetchMessages, 1000);
        
        document.getElementById('message').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        fetchMessages();
    </script>
</body>
</html>