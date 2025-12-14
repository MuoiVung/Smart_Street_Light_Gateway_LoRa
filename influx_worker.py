# influx_worker.py
import requests
import config

class InfluxWorker:
    def __init__(self):
        self.url = config.INFLUX_URL
        self.headers = {
            'Authorization': f'Token {config.INFLUX_TOKEN}',
            'Content-Type': 'text/plain; charset=utf-8',
            'Accept': 'application/json'
        }
        self.params = {
            'org': config.INFLUX_ORG,
            'bucket': config.INFLUX_BUCKET,
            'precision': 's'
        }

    def send_data(self, device_name, raw_data, device_state):
        """
        device_name: Tên thiết bị (VD: "Light A") -> Sẽ làm Tag
        raw_data: Dữ liệu cảm biến từ LoRa (JSON)
        device_state: Trạng thái nút ấn hiện tại (lấy từ bộ nhớ Gateway)
        """
        try:
            # 1. Chẩn bị Tag (Thay khoảng trắng bằng _ để tránh lỗi Line Protocol)
            # VD: "Light A" -> "Light_A"
            tag_device = device_name.replace(" ", "_")

            # 2. Chuẩn bị Fields (Dữ liệu đo đạc)
            # Cấu trúc: field_key=field_value
            # Lưu ý: InfluxDB phân biệt int (thêm i), float, bool
            
            # Lấy dữ liệu từ gói tin LoRa + Trạng thái từ bộ nhớ
            fields = []
            
            # --- Cảm biến (Telemetry) ---
            fields.append(f"light={raw_data.get('ambientLightIntensity', 0)}i") # i là integer
            fields.append(f"voltage={raw_data.get('voltage', 0)}")             # float
            fields.append(f"current={raw_data.get('current', 0)}")
            fields.append(f"power={raw_data.get('power', 0)}")
            fields.append(f"motion={str(raw_data.get('isMotion', False))}")    # Boolean
            
            # --- Trạng thái (Attributes) ---
            fields.append(f"brightness={device_state.get('led_brightness', 0)}i")
            fields.append(f"auto_mode={str(device_state.get('auto_mode', False))}")
            fields.append(f"yellow_color={str(device_state.get('yellow_color', False))}")

            # 3. Tạo chuỗi Line Protocol
            # Cấu trúc: measurement,tag_set field_set
            # VD: street_light,device=Light_A voltage=220,power=100...
            field_str = ",".join(fields)
            payload = f"street_light,device={tag_device} {field_str}"

            # 4. Gửi Request
            response = requests.post(
                self.url, 
                headers=self.headers, 
                params=self.params, 
                data=payload,
                timeout=2 # Timeout 2s để tránh treo Gateway nếu mạng lag
            )

            if response.status_code == 204:
                print(f"[INFLUX] Sent OK: {device_name}")
            else:
                print(f"[INFLUX] Error {response.status_code}: {response.text}")

        except Exception as e:
            print(f"[INFLUX] Exception: {e}")