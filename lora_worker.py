# lora_worker.py
import threading
import json
import time
from SX127x.LoRa import *
from SX127x.board_config import BOARD

class LoRaWorker(LoRa):
    def __init__(self, verbose=False, callback=None):
        super(LoRaWorker, self).__init__(verbose)
        self.callback = callback # Hàm này sẽ được gọi khi có dữ liệu
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)

    def on_rx_done(self):
        try:
            # 1. Đọc dữ liệu thô từ phần cứng
            payload = self.read_payload(nocheck=True)
            if payload:
                # 2. Giải mã sang chuỗi
                raw_string = bytes(payload).decode("utf-8", 'ignore')
                print(f"[LORA HW] Received: {raw_string}")
                
                # 3. Lọc lấy JSON (Tìm { và })
                start = raw_string.find('{')
                end = raw_string.rfind('}') + 1
                
                if start != -1 and end != -1:
                    json_str = raw_string[start:end]
                    data = json.loads(json_str)
                    
                    # 4. GỬI DỮ LIỆU VỀ MAIN.PY QUA CALLBACK
                    if self.callback:
                        self.callback(data)
                else:
                    print("[LORA HW] Ignored noise (Not JSON)")

        except Exception as e:
            print(f"[LORA HW] Error: {e}")
        
        # 5. Reset để nhận gói tiếp theo
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    # Hàm gửi lệnh xuống End Node (Downlink)
    def send_command(self, device_id, command_key, value):
       with self.lock:
            # Ví dụ gửi chuỗi: {"deviceID":1,"cmd":"AUTO","value":1}
            cmd_json = {
                "deviceID": device_id,
                "cmd": command_key,
                "value": value
            }
            msg = json.dumps(cmd_json)
            
            # Cần chuyển sang mode TX để gửi, sau đó quay lại RX
            current_mode = self.get_mode()
            self.set_mode(MODE.STDBY)
            self.write_payload(list(bytearray(msg, "utf-8")))
            self.set_mode(MODE.TX)
            print(f"[LORA TX] Sent: {msg}")
            
            # Chờ gửi xong rồi quay lại nghe (RXCONT)
            time.sleep(0.2) 
            self.set_mode(MODE.RXCONT)