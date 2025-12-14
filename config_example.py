# config_example.py
# Đổi tên file này thành config.py và điền thông tin thật vào

# --- CẤU HÌNH CHẾ ĐỘ ---
USE_SIMULATION = True 

# --- THINGSBOARD ---
THINGSBOARD_HOST = "thingsboard.cloud"
ACCESS_TOKEN = "YOUR_TOKEN_HERE"  # <--- Người dùng sẽ tự điền token của họ

# --- LORA HARDWARE ---
LORA_FREQUENCY = 923.0
LORA_SYNC_WORD = 0xF3

# --- DANH SÁCH THIẾT BỊ ---
DEVICE_MAP = {
    1: "Light A",
    2: "Light B",
    3: "Light C"
}

# --- INFLUXDB CONFIG ---
INFLUX_URL = "http://xxxx/api/v2/write" 
INFLUX_TOKEN = "xxxx"                   #
INFLUX_ORG = "IIOT"
INFLUX_BUCKET = "MONITORING_DATA"