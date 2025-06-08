# LINE Bot 自主網搜聊天機器人

這是一個結合 LINE Messaging API 和 Google Gemini AI 的聊天機器人，具備網路搜尋功能。

## 功能特點

- 使用 Google Gemini 2.0 Flash 模型進行對話生成
- 自動判斷是否需要網路搜尋來回答問題
- 保持最近 2 個回合的對話記憶
- 支援多用戶並保持對話隱私
- 24/7 持續服務

## 環境要求

- Python 3.8+
- Flask
- LINE Messaging API SDK
- Google Generative AI SDK
- 其他相依套件請見 requirements.txt

## 本地安裝與測試

1. 安裝必要套件：
```bash
pip install -r requirements.txt
```

2. 設定環境變數（創建 .env 檔案）：
```plaintext
GOOGLE_API_KEY=your_google_api_key
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
```

3. 本地測試：
```bash
python main.py
```

## GitHub 儲存庫設定

1. 建立 GitHub 儲存庫：
   - 登入 [GitHub](https://github.com/)
   - 點擊右上角 "+" > "New repository"
   - 儲存庫名稱：`linebot_search`
   - 描述：LINE Bot 自主網搜聊天機器人
   - 選擇 Public 或 Private
   - 不要初始化 README
   - 點擊 "Create repository"

2. 初始化本地儲存庫：
```bash
cd e:\myPython\linebot_search
git init
```

3. 設定 .gitignore 檔案：
```bash
echo .env >> .gitignore
echo __pycache__/ >> .gitignore
echo venv/ >> .gitignore
```

4. 提交程式碼：
```bash
git add .
git commit -m "初始提交：LINE Bot 自主網搜聊天機器人"
```

5. 連接並推送到 GitHub：
```bash
git remote add origin https://github.com/您的使用者名稱/linebot_search.git
git branch -M main
git push -u origin main
```

## PythonAnywhere 部署步驟

1. 註冊/登入 [PythonAnywhere](https://www.pythonanywhere.com/)

2. 開啟 Bash console，克隆專案：
```bash
git clone https://github.com/您的使用者名稱/linebot_search.git
cd linebot_search
```

3. 在 PythonAnywhere 建立虛擬環境（使用 Python 3.9 或更高版本）：
```bash
# 檢查可用的 Python 版本
ls /usr/bin/python*

# 建立虛擬環境（使用 Python 3.9 或更高版本）
mkvirtualenv --python=/usr/bin/python3.9 linebot_env

# 如果上述命令失敗，可以嘗試：
python3.9 -m venv linebot_env
source linebot_env/bin/activate

# 升級 pip
pip install --upgrade pip

# 安裝套件（如果遇到錯誤，可以一個一個安裝）
pip install flask
pip install line-bot-sdk
pip install python-dotenv
pip install google-generativeai
pip install googlesearch-python
pip install aiohttp
```

4. 如果仍然無法安裝 google-generativeai，可以嘗試：
```bash
# 指定較早的穩定版本
pip install google-generativeai==0.3.1

# 或者從 GitHub 安裝最新版本
pip install git+https://github.com/google/generative-ai-python.git
```

5. 設定 Web 應用：
   - 前往 Web 頁面
   - 點擊 Add a new web app
   - 選擇 Manual configuration
   - 選擇 Python 3.8

6. 設定虛擬環境路徑：
   - 在 Virtualenv 區域輸入：
   ```
   /home/<your-username>/.virtualenvs/linebot_env
   ```

7. 修改 WSGI 設定檔：
```python
import os
import sys

# 加入專案路徑
path = '/home/<your-username>/linebot_search'
if path not in sys.path:
    sys.path.append(path)

# 設定環境變數
os.environ['GOOGLE_API_KEY'] = 'your_key_here'
os.environ['LINE_CHANNEL_SECRET'] = 'your_secret_here'
os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'your_token_here'

# 匯入 Flask 應用
from main import app as application
```

8. 更新 LINE Bot Webhook URL：
   - 前往 LINE Developers Console
   - 更新 Webhook URL 為：
   ```
   https://<your-username>.pythonanywhere.com/callback
   ```

9. 重新載入 Web 應用

## 注意事項

- 確保環境變數正確設定
- PythonAnywhere 免費帳戶有 CPU 時間限制
- 定期檢查 LOG 檔案排除問題
- 建議啟用 HTTPS 以確保安全性

## 問題排解

如遇到問題，請檢查：
1. 環境變數是否正確設定
2. 相依套件是否完整安裝
3. Webhook URL 是否正確設定
4. PythonAnywhere 的錯誤日誌

## 授權

MIT License