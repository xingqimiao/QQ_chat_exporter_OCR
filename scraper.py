# scraper.py
import pyautogui
from pynput import keyboard
import time
import numpy as np
import cv2
import math
import sys
import os
import re
from datetime import datetime
import requests
import io
import base64

DEBUG_MODE = True
OCR_API_URL = "http://127.0.0.1:5005/ocr"

class StoppableListener(keyboard.Listener):
    def __init__(self, **kwargs):
        super().__init__(on_press=self.on_press_callback, **kwargs)
        self._scraping_active = True
    def on_press_callback(self, key):
        # 【核心改变】将停止键从 Esc 改为 's'
        try:
            if key.char == 's':
                self._scraping_active = False
                return False
        except AttributeError:
            pass # 忽略特殊按键
    def is_scraping_active(self):
        return self._scraping_active

def clean_text(text):
    return re.sub(r'^\s*\d+\s*[、.]\s*', '', text.strip())

def is_potential_system_msg(text):
    # 这个函数现在非常可靠，无需改动
    time_pattern = r'(\d{1,2}:\d{1,2})|昨天|今天'
    system_patterns = ['撤回了一条消息', '拍了拍', '揉了揉', '碰了碰', '戳了戳']
    if re.search(time_pattern, text): return True
    for pat in system_patterns:
        if pat in text: return True
    return False

def scrape_chat_history(config, logging):
    try:
        response = requests.get(OCR_API_URL.replace('/ocr', '/'))
        if response.status_code != 200: raise ConnectionError()
        logging.info("OnnxOCR API服务器连接成功！")
    except requests.exceptions.RequestException:
        yield {'final_log': "错误：无法连接到OCR服务器。请先运行 'run_1_ocr_server.bat'。"}
        return

    run_debug_folder = None
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_debug_folder = os.path.join('debug', f'run_{timestamp}')
        os.makedirs(run_debug_folder, exist_ok=True)
        logging.info(f"调试模式已开启，截图将保存在: {run_debug_folder}")
    
    full_log, processed_texts_set, scroll_count = [], set(), 0
    region = tuple(config['chat_region'])
    region_center_x = region[2] / 2
    center_zone_start, center_zone_end = region_center_x * 0.8, region_center_x * 1.2
    s1_name, s2_name = config.get('speaker1_name'), config.get('speaker2_name')

    with StoppableListener() as listener:
        print("\n[抓取开始] 已连接OnnxOCR API。按【s】键可随时停止。")
        
        while listener.is_scraping_active():
            scroll_count += 1
            screenshot_pil = pyautogui.screenshot(region=region)
            
            if DEBUG_MODE:
                raw_path = os.path.join(run_debug_folder, f'scroll_{scroll_count}.png')
                screenshot_pil.save(raw_path)

            try:
                img_byte_arr = io.BytesIO()
                screenshot_pil.save(img_byte_arr, format='PNG')
                base64_encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                payload = {"image": base64_encoded_image}
                response = requests.post(OCR_API_URL, json=payload, timeout=10)
                response.raise_for_status()
                result = response.json().get('results', [])
            except Exception as e:
                logging.error(f"调用OCR API时发生错误: {e}")
                continue

            if result:
                current_screen_texts = []
                for res in result:
                    txt, score = res['text'], res['confidence']
                    
                    if score < 0.65: continue
                    cleaned_txt = clean_text(txt)
                    if not cleaned_txt: continue
                    
                    if cleaned_txt in processed_texts_set: continue
                    
                    box = np.array(res['bounding_box']).astype(int)
                    w, h = np.max(box[:, 0]) - np.min(box[:, 0]), np.max(box[:, 1]) - np.min(box[:, 1])

                    # 【核心优化】引入“密度过滤器”
                    # 如果文本框面积相对于文本长度过大，则判定为图片或贴纸
                    # 500这个阈值可以根据实际情况微调
                    if len(cleaned_txt) > 1 and (w * h) / len(cleaned_txt) > 600:
                        logging.info(f"过滤掉低密度识别块(可能是图片): w={w}, h={h}, text='{cleaned_txt[:20]}'")
                        continue
                    
                    y_pos, center_x = int(np.mean(box[:, 1])), int(np.mean(box[:, 0]))

                    is_system = is_potential_system_msg(cleaned_txt) or (center_zone_start < center_x < center_zone_end)
                    speaker = "系统消息" if is_system else (s1_name if center_x < region_center_x else s2_name)
                    
                    entry = {'speaker': speaker, 'text': cleaned_txt, 'scroll': scroll_count, 'y_pos': y_pos}
                    current_screen_texts.append(entry)

                if current_screen_texts:
                    current_screen_texts.sort(key=lambda x: x['y_pos'])
                    for entry in current_screen_texts:
                        processed_texts_set.add(entry['text'])
                        full_log.append(entry)
                        yield entry

            pyautogui.click(region[0] + region[2] / 2, region[1] + region[3] / 2)
            pyautogui.scroll(-700)
            logging.info(f"第 {scroll_count} 次滚动完成。")
            time.sleep(1.2)

    full_log.sort(key=lambda x: (x['scroll'], x['y_pos']))
    # ... 最终排序和格式化逻辑已很完美，保持不变 ...
    final_lines = []
    if full_log:
        final_texts_set = set()
        for entry in full_log:
            if entry['text'] not in final_texts_set:
                if entry['speaker'] == "系统消息": final_lines.append(f"\n--- {entry['text']} ---\n")
                else: final_lines.append(f"{entry['speaker']}：{entry['text']}")
                final_texts_set.add(entry['text'])
    final_log_text = "\n".join(final_lines)
    
    if DEBUG_MODE and run_debug_folder:
        final_log_path = os.path.join(run_debug_folder, 'final_log.txt')
        with open(final_log_path, 'w', encoding='utf-8') as f: f.write(final_log_text)
    
    yield {'final_log': final_log_text}
    logging.info("全过程抓取结束。")