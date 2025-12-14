import time
import json
import random
import threading
import config

class LoRaWorker:
    def __init__(self, verbose=False, callback=None):
        self.callback = callback
        self.running = True
        
        # [QUAN TRỌNG] Tạo bộ nhớ giả lập riêng cho các Node (Giống ESP32 thật)
        # Mặc định ban đầu
        self.simulated_nodes = {
            1: {"auto_mode": False, "yellow_color": False, "ledBrightness": 0},
            2: {"auto_mode": False, "yellow_color": False, "ledBrightness": 0},
            3: {"auto_mode": False, "yellow_color": False, "ledBrightness": 0}
        }
        
        # Luồng sinh dữ liệu
        self.thread = threading.Thread(target=self._simulation_loop)
        self.thread.daemon = True
        self.thread.start()
        print("[MOCK] Simulation Worker Started (Smart Mode)")

    # --- CÁC HÀM GIẢ (DUMMY) ---
    def set_mode(self, mode): pass
    def set_freq(self, freq): pass
    def set_sync_word(self, word): pass
    def set_pa_config(self, pa_select): pass
    
    # --- LOGIC GIẢ LẬP (UPLINK) ---
    def _simulation_loop(self):
        while self.running:
            time.sleep(5) # 5 giây gửi 1 lần
            
            # Chọn ngẫu nhiên 1 thiết bị để gửi tin
            dev_id = random.choice(list(config.DEVICE_MAP.keys()))
            
            # Lấy trạng thái hiện tại trong bộ nhớ giả
            node_state = self.simulated_nodes[dev_id]
            
            # Tính toán công suất giả dựa trên độ sáng (cho logic)
            p_consum = 0
            if node_state["ledBrightness"] > 0:
                p_consum = random.randint(50, 150)

            # Sinh dữ liệu fake nhưng dựa trên TRẠNG THÁI THẬT trong bộ nhớ
            fake_data = {
                "deviceID": dev_id,
                "ambientLightIntensity": random.randint(0, 100),
                "voltage": random.randint(220, 230),
                "current": round(random.uniform(0.5, 2.0), 2),
                "power": p_consum,
                "isMotion": random.choice([True, False]),
                "isRain": random.choice([True, False]),
                
                # [QUAN TRỌNG] Lấy giá trị từ bộ nhớ giả lập thay vì hardcode
                "auto_mode": node_state["auto_mode"], 
                "ledBrightness": node_state["ledBrightness"],
                "yellow_color": node_state["yellow_color"]
            }
            
            print(f"[MOCK RX] Node {dev_id} sending data (Auto: {fake_data['auto_mode']})")
            print(f"          Data: {fake_data}")
            
            if self.callback:
                self.callback(fake_data)

    # --- GIẢ LẬP NHẬN LỆNH (DOWNLINK) ---
    def send_command(self, device_id, command_key, value):
        # Đây là nơi cập nhật bộ nhớ giả khi Gateway gửi lệnh xuống
        # Mô phỏng việc ESP32 nhận được tín hiệu LoRa và đổi trạng thái
        
        print(f"[MOCK TX] >>> Command received for ID {device_id}: {command_key}={value}")
        
        if device_id in self.simulated_nodes:
            if command_key == "AUTO":
                self.simulated_nodes[device_id]["auto_mode"] = bool(value)
            elif command_key == "COLOR":
                self.simulated_nodes[device_id]["yellow_color"] = bool(value)
            elif command_key == "DIM":
                self.simulated_nodes[device_id]["ledBrightness"] = int(value)

    def close(self):
        self.running = False