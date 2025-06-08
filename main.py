#########################################################################
# Python x AI Agent
# Flask, Linebot, deployment - 網站伺服器串聯LINE服務
#
# [作業]
# LINE AI Bot 自主網搜聊天機器人
#
# 問題：請依照本週課程所述，撰寫程式並於串聯LINE頻道後測試。
#       測試完成後遷移寄存佈署至伺服器 (PythonAnywhere)
#
# 輸出：
#       1)使用者加入好友後於 LINE 所發文字訊息，機器人會連結
#         Google Gemini，由 AI 生成回覆內容後再轉發回去給發送者。
#       2)回應使用者的內容須有聊天脈絡，具備一定的對話記憶。
#       3)每次聊天時擁有的對話記憶維持在2個回合(即問與答共4段內容)。
#       4)加入機器人為好友的眾多使用者之個別聊天內容必須保密。
#       5)聊天機器人應24小時服務用戶。
#
#       增加 Line Bot 一輸入提示內容自主網路搜尋，以排除 AI 幻覺，
#       並提供即時訊息。
#
# 提示：結合 LLM 結構式 (JSON) 輸出功能
##########################################################################

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
from googlesearch import search as GoogleSearchFunction

# 設定 .env 檔案的絕對路徑
env_path = Path(__file__).resolve().parent / '.env'

# 確保 .env 檔案存在
if not env_path.exists():
    raise FileNotFoundError(f"找不到 .env 檔案：{env_path}")

# 載入環境變數
if not load_dotenv(env_path):
    raise RuntimeError(f"無法載入 .env 檔案：{env_path}")

# 驗證 API 金鑰
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY 未設定")

# 初始化 Gemini API
genai.configure(api_key=api_key)

# 初始化模型（使用 Gemini 2.0 Flash）
model = genai.GenerativeModel('gemini-2.0-flash')

# 測試模型連線
try:
    response = model.generate_content(
        "測試訊息",
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 2048,
        }
    )
    print("Gemini API 連線成功！")
except Exception as e:
    print(f"Gemini API 連線失敗：{e}")
    raise

# 初始化 Flask 應用程式
app = Flask(__name__)

# 初始化 LINE Bot API
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 用於儲存每個使用者的聊天歷史
user_histories = {}

# 用來詢問是否需要搜尋才能回覆問題的樣板
# 要求 AI 以 JSON 格式回覆 Y/N 以及建議的搜尋關鍵字
template_google = '''
你是一個回答問題的專家。
請判斷以下的使用者問題是否需要網路搜尋來提供準確或最新的資訊。
如果需要，請在 `keyword` 中提供一個相關的搜尋關鍵字。
如果不需要，請將 `search` 設定為 'N'，並將 `keyword` 留空。

範例:
使用者問題: 台北101多高?
JSON 回覆: {"search": "N", "keyword": ""}

使用者問題: 今天的台北天氣如何?
JSON 回覆: {"search": "Y", "keyword": "台北天氣"}

使用者問題: 2024奧運在哪舉辦?
JSON 回覆: {"search": "Y", "keyword": "2024 奧運舉辦地點"}

使用者問題: 最近有什麼電影好看?
JSON 回覆: {"search": "Y", "keyword": "最新電影推薦"}

現在，請根據以下的使用者問題提供 JSON 回覆:
使用者問題: {msg}
JSON 回覆:
'''

def get_reply_g(message, sys_msg=None, stream=False, json_format=False, history=None):
    """
    Ask Gemini AI to generate a response to the given message.
    Args:
        message (str): The message to generate a response to.
        sys_msg (str): The system message to pass to the model.
        stream (bool): Whether to stream the response.
        json_format (bool): Whether to format the response as JSON.
        history (list): A list of previous messages in the conversation.
    Yields:
        The generated response text.
    """
    if history is None:
        history = []

    # 如果有系統訊息，則作為對話的開頭
    if sys_msg:
        full_history = [{"role": "user", "parts": [sys_msg]}, {"role": "model", "parts": ["好的。"]}] + history
    else:
        full_history = history

    # 將當前訊息加入歷史記錄
    full_history.append({"role": "user", "parts": [message]})

    chat_session = model.start_chat(history=full_history)

    try:
        response = chat_session.send_message(message, stream=stream)
        if stream:
            for chunk in response:
                yield chunk.text
        else:
            yield response.text
    except Exception as e:
        print(f"Error in get_reply_g: {e}")
        yield "對不起，AI 處理訊息時發生錯誤。"

def check_google(msg, verbose=False):
    """
    Check if AI thinks it needs to search the internet to answer a question.
    """
    try:
        prompt = template_google.format(msg=msg)
        response = model.generate_content(prompt)
        
        if verbose:
            print(f"Raw AI response: {response.text}")
        
        try:
            # 嘗試解析 JSON 回應
            json_res = json.loads(response.text)
            if isinstance(json_res, dict) and 'search' in json_res and 'keyword' in json_res:
                return json_res
            else:
                if verbose:
                    print(f"Invalid JSON format: {json_res}")
                return {"search": "N", "keyword": ""}
        except json.JSONDecodeError as e:
            if verbose:
                print(f"JSON decode error: {e}")
            return {"search": "N", "keyword": ""}
    except Exception as e:
        if verbose:
            print(f"Unexpected error in check_google: {e}")
        return {"search": "N", "keyword": ""}

def google_res(user_msg: str, num_results: int=5, verbose: bool=False):
    """
    returns the up-to-date results of Google-internet-search
    """
    if verbose:
        print(f"Searching Google for: {user_msg}")
    
    results = []
    try:
        # 使用 googlesearch-python 的 search 函數
        for url in GoogleSearchFunction(user_msg, num_results=num_results):
            results.append({"snippet": url})
    except Exception as e:
        if verbose:
            print(f"Error during Google search: {e}")
        return ""

    if not results:
        if verbose:
            print("No search results found.")
        return ""

    search_result_text = ""
    for i, res in enumerate(results):
        # 由於我們只想要摘要，可以提取 snippet
        if 'snippet' in res:
            search_result_text += f"Snippet {i+1}: {res['snippet']}\n"
        elif 'description' in res: # 有些搜尋結果可能用 description
            search_result_text += f"Description {i+1}: {res['description']}\n"
        
        # 限制返回的結果長度，避免超出模型上下文限制
        if len(search_result_text) > 1500: # 大約 1500 字元
            search_result_text += "... (truncated)"
            break
            
    if verbose:
        print(f"Google search results:\n{search_result_text}")
        
    return search_result_text

def chat_g(user_msg, sys_msg=None, stream=False, verbose=False, user_id=None):
    """
    Interact with Gemini AI.
    Args:
        user_msg (str): The user's message to the AI.
        sys_msg (str): The AI's prompt to the user.
        stream (bool): Whether to stream AI's response.
        verbose (bool): Whether to print debug information.
        user_id (str): Unique ID for the user to maintain chat history.
    Yields:
        str: The AI's response to the user's message.
    """
    # 取得或初始化使用者的聊天歷史
    if user_id not in user_histories:
        user_histories[user_id] = []

    history = user_histories[user_id]

    # 限制對話記憶在最近的2個回合 (4段內容：2個使用者訊息 + 2個模型回覆)
    # 每個回合包含一個使用者訊息和一個模型回覆，所以是 (user, model), (user, model)
    while len(history) > 4: 
        history.pop(0) # 移除最舊的對話回合中的使用者訊息
        history.pop(0) # 移除最舊的對話回合中的模型回覆

    # 步驟 1: 檢查是否需要網路搜尋
    check_res = check_google(user_msg, verbose=verbose)
    search_needed = check_res.get('search')
    search_keyword = check_res.get('keyword')

    ai_response_content = ""

    if search_needed == 'Y' and search_keyword:
        if verbose:
            print(f"AI suggests searching for: {search_keyword}")
        
        # 步驟 2: 執行網路搜尋
        search_results = google_res(search_keyword, num_results=3, verbose=verbose) # 取得前3條結果

        if search_results:
            # 步驟 3: 將搜尋結果納入提示中，讓 AI 總結
            # 建立一個新的提示，包含原始問題和搜尋結果
            prompt_with_search = (
                f"使用者問題: {user_msg}\n"
                f"以下是網路搜尋結果，請根據這些資訊來回答問題：\n"
                f"{search_results}\n"
                f"請綜合這些資訊並簡潔地回答使用者問題。"
            )
            if verbose:
                print(f"Sending prompt with search results to AI:\n{prompt_with_search}")
            
            # 使用包含搜尋結果的提示進行對話
            response_generator = get_reply_g(prompt_with_search, sys_msg=sys_msg, stream=stream, history=history)
        else:
            # 如果沒有搜尋結果，直接用原始問題問 AI
            if verbose:
                print("No search results, proceeding with direct AI response.")
            response_generator = get_reply_g(user_msg, sys_msg=sys_msg, stream=stream, history=history)
    else:
        # 不需要網路搜尋，直接用原始問題問 AI
        if verbose:
            print("AI determines no search is needed, proceeding with direct AI response.")
        response_generator = get_reply_g(user_msg, sys_msg=sys_msg, stream=stream, history=history)

    # 收集 AI 的回覆內容
    for chunk in response_generator:
        ai_response_content += chunk
        yield chunk # 如果是串流模式，逐塊回傳

    # 將使用者訊息和 AI 回覆加入歷史記錄
    user_histories[user_id].append({"role": "user", "parts": [user_msg]})
    user_histories[user_id].append({"role": "model", "parts": [ai_response_content]})


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # print("InvalidSignatureError: Check your LINE_CHANNEL_SECRET.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text
    
    # 預設的系統訊息，您可以根據需要修改
    sys_msg = "你是一位樂於助人且富有創意的 AI 助理，專精於提供即時且準確的資訊，並能夠從網路搜尋結果中整合資訊進行回答。"

    # 調用 chat_g 函式以獲得 AI 回覆，並傳遞 user_id 以維護歷史記錄
    ai_response = ""
    for chunk in chat_g(user_message, sys_msg=sys_msg, verbose=True, user_id=user_id):
        ai_response += chunk

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_response))

# 不再使用 flask-ngrok，而是假設 ngrok 已經在外部啟動
# run_with_ngrok(app) # 移除這行

def main():
    # 這裡的 main 函式是為了保持結構完整性
    # 實際的 Flask 應用程式啟動會透過 app.run()
    pass

if __name__ == '__main__':
    # 讓 Flask 應用程式在啟動時運行
    app.run(host='0.0.0.0', port=5000)
    # 如果您手動啟動 ngrok，請確保 ngrok http 5000 在另一個終端機中運行