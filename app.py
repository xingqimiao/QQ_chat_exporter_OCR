# app.py
import flask
from flask import Flask, render_template, request, jsonify, Response
import scraper
import config_ui
import logging
import json
from datetime import datetime
import os

app = Flask(__name__)
CONFIG = {}
CHAT_LOG_CONTENT = ""
DEBUG = True
CONFIG_FILE = 'config.json'

if DEBUG:
    logging.basicConfig(filename='qq_scraper.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
    logging.info("程序以Debug模式启动")

@app.route('/')
def index():
    config_exists = os.path.exists(CONFIG_FILE)
    return render_template('index.html', config_exists=config_exists)

@app.route('/load-config', methods=['GET'])
def load_config():
    global CONFIG
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            CONFIG = json.load(f)
        logging.info(f"成功从 {CONFIG_FILE} 加载配置。")
        return jsonify({'status': 'success', 'config': CONFIG})
    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/configure', methods=['POST'])
def configure():
    global CONFIG
    data = request.json
    step = data.get('step')

    if step == 'region':
        selector = config_ui.RegionSelector()
        region = selector.get_selection()
        if region:
            CONFIG['chat_region'] = region
            return jsonify({'status': 'success', 'region': region})
        return jsonify({'status': 'error', 'message': '未选择区域'})
    
    elif step == 'names_and_colors':
        CONFIG.update({
            'speaker1_name': data.get('s1_name'),
            'speaker2_name': data.get('s2_name'),
        })
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(CONFIG, f, indent=4, ensure_ascii=False)
            logging.info(f"配置已成功保存到 {CONFIG_FILE}")
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
        return jsonify({'status': 'success'})

    elif step == 'get_color':
        import pyautogui
        try:
            pos = pyautogui.position()
            color = pyautogui.screenshot().getpixel(pos)
            color_type = data.get('colorType')
            CONFIG[color_type] = color # 颜色信息也保存在内存中
            return jsonify({'status': 'success', 'color': color})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})

    return jsonify({'status': 'error', 'message': '未知配置步骤'})

# /start-scrape 和 /download 路由保持不变
@app.route('/start-scrape')
def start_scrape():
    if 'chat_region' not in CONFIG:
        return Response("错误：配置未加载。", mimetype='text/event-stream')
    def stream_generator():
        global CHAT_LOG_CONTENT
        final_log_from_scraper = ""
        try:
            for message in scraper.scrape_chat_history(CONFIG, logging):
                if 'text' in message:
                    sse_data = f"data: {json.dumps(message)}\n\n"
                    yield sse_data
                elif 'final_log' in message:
                    final_log_from_scraper = message['final_log']
            CHAT_LOG_CONTENT = final_log_from_scraper
            yield "event: finished\ndata: 抓取完成！\n\n"
        except Exception as e:
            logging.error(f"抓取过程中发生严重错误: {e}", exc_info=True)
            yield f"event: error\ndata: {str(e)}\n\n"
    return Response(stream_generator(), mimetype='text/event-stream')

@app.route('/download')
def download():
    if not CHAT_LOG_CONTENT:
        return "没有可供下载的聊天记录。", 404
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_log_{timestamp}.txt"
    response = flask.make_response(CHAT_LOG_CONTENT)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)