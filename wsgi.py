import os
import sys
import logging
from datetime import datetime

# 設定日誌
log_path = '/home/eqpeter/linebot_search/app.log'
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 記錄啟動時間
logging.info(f"應用程式啟動於 {datetime.now()}")

try:
    # 設定專案根目錄
    project_root = '/home/eqpeter/linebot_search'

    # 將專案根目錄加入系統路徑
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logging.info(f"已加入專案路徑: {project_root}")

    # 載入環境變數
    from dotenv import load_dotenv
    env_path = os.path.join(project_root, '.env')

    if os.path.exists(env_path):
        load_dotenv(env_path)
        logging.info("成功載入 .env 檔案")
    else:
        logging.warning(f"找不到 .env 檔案: {env_path}")

    # 驗證必要的環境變數
    required_vars = ['GOOGLE_API_KEY', 'LINE_CHANNEL_SECRET', 'LINE_CHANNEL_ACCESS_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logging.error(f"缺少必要的環境變數: {', '.join(missing_vars)}")
        raise ValueError(f"缺少環境變數: {', '.join(missing_vars)}")

    # 設定 Google API 相關配置
    os.environ['PYTHONPATH'] = project_root

    # 匯入 Flask 應用程式
    from main import app as application
    logging.info("成功載入 Flask 應用程式")

except Exception as e:
    logging.error(f"應用程式載入失敗: {str(e)}")
    raise