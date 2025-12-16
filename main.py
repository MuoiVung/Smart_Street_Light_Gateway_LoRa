# main.py
import time
import json
import sys
import paho.mqtt.client as mqtt
import config

# Tự động chọn module dựa trên Config
if config.USE_SIMULATION:
    from mock_lora_worker import LoRaWorker
    # Mock mode không cần BOARD setup của Raspberry Pi

    class DummyBoard:
        def setup(self): pass
        def teardown(self): pass
    BOARD = DummyBoard()
else:
    from lora_worker import LoRaWorker
    from SX127x.board_config import BOARD
    from SX127x.LoRa import MODE  # Chỉ import MODE khi dùng thật

# --- BỘ NHỚ TRẠNG THÁI (Source of Truth) ---
device_states = {
    1: {"auto_mode": False, "yellow_color": False, "led_brightness": 0},
    2: {"auto_mode": False, "yellow_color": False, "led_brightness": 0},
    3: {"auto_mode": False, "yellow_color": False, "led_brightness": 0}
}

client = mqtt.Client()
lora = None

# --- XỬ LÝ DỮ LIỆU NHẬN ĐƯỢC TỪ LORA (Real Data) ---


def process_lora_data(data):
    # Data này là JSON thật từ ESP32 gửi lên
    # Ví dụ: {"deviceID":1, "vol":220, "cur":2...}

    dev_id = data.get("deviceID")

    if dev_id in config.DEVICE_MAP:
        dev_name = config.DEVICE_MAP[dev_id]

        # 1. Cập nhật vào bộ nhớ trạng thái Gateway (để đồng bộ UI)
        if "auto_mode" in data:
            device_states[dev_id]["auto_mode"] = data["auto_mode"]
        if "ledBrightness" in data:
            device_states[dev_id]["led_brightness"] = data["ledBrightness"]
        if "yellow_color" in data:
            device_states[dev_id]["yellow_color"] = data["yellow_color"]

        # 2. Đóng gói Telemetry (Thông số cảm biến)
        telemetry = {
            "light": data.get("ambientLightIntensity", 0),
            "voltage": data.get("voltage", 0),
            "current": data.get("current", 0),
            "power": data.get("power", 0),
            "motion": data.get("isMotion", False),
            "raining": data.get("isRain", False),
            "led_brightness": device_states[dev_id]["led_brightness"]
        }

        # 3. Đóng gói Attributes (Trạng thái nút ấn)
        attributes = {
            "auto_mode": device_states[dev_id]["auto_mode"],
            "yellow_color": device_states[dev_id]["yellow_color"],
            "led_brightness": device_states[dev_id]["led_brightness"]
        }

        # 4. Gửi lên ThingsBoard
        client.publish("v1/gateway/telemetry",
                       json.dumps({dev_name: [telemetry]}))
        client.publish("v1/gateway/attributes",
                       json.dumps({dev_name: attributes}))

        # 5. Gửi lên InfluxDB
        # influx_worker.send_data(dev_name, data, device_states[dev_id])

        print(f"-> Synced {dev_name} to Cloud.")

# --- MQTT HANDLERS ---


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected code: {rc}")
    client.subscribe("v1/gateway/rpc")
    for name in config.DEVICE_MAP.values():
        client.publish("v1/gateway/connect", json.dumps({"device": name}))


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"\n[RPC] {payload}")

        device_name = payload.get("device")
        data = payload.get("data")
        method = data.get("method")
        params = data.get("params")

        # Tìm ID thiết bị
        target_id = 0
        for pid, pname in config.DEVICE_MAP.items():
            if pname == device_name:
                target_id = pid
                break

        if target_id != 0:
            # 1. Cập nhật bộ nhớ đệm Gateway
            if method == "setAutoMode":
                device_states[target_id]["auto_mode"] = params
                # 2. Gửi lệnh xuống LoRa (Hardware)
                if lora:
                    lora.send_command(target_id, "AUTO", 1 if params else 0)

            elif method == "setYellowColor":
                device_states[target_id]["yellow_color"] = params
                # 2 is yellow color, 1 is white color
                if lora:
                    lora.send_command(target_id, "COLOR", 2 if params else 1)

            elif method == "setBrightness":
                device_states[target_id]["led_brightness"] = int(params)
                if lora:
                    lora.send_command(target_id, "DIM", int(params))

            # 3. Phản hồi GUI ngay lập tức
            force_update_attributes(target_id)

    except Exception as e:
        print(f"RPC Error: {e}")


def force_update_attributes(device_id):
    dev_name = config.DEVICE_MAP[device_id]
    attr = {
        "auto_mode": device_states[device_id]["auto_mode"],
        "yellow_color": device_states[device_id]["yellow_color"],
        "led_brightness": device_states[device_id]["led_brightness"]
    }
    client.publish("v1/gateway/attributes", json.dumps({dev_name: attr}))


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    try:
        # 1. Setup LoRa
        BOARD.setup()
        # Truyền hàm process_lora_data vào để LoRa gọi khi có tin mới
        lora = LoRaWorker(verbose=False, callback=process_lora_data)

        if not config.USE_SIMULATION:
            lora.set_mode(MODE.STDBY)
            lora.set_freq(config.LORA_FREQUENCY)
            lora.set_sync_word(config.LORA_SYNC_WORD)
            lora.set_pa_config(pa_select=1)
            lora.set_mode(MODE.RXCONT)
            print("--- REAL LoRa Hardware Started ---")
        else:
            print("--- MOCK Simulation Started ---")

        # 2. Setup MQTT
        client.username_pw_set(config.ACCESS_TOKEN)
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(config.THINGSBOARD_HOST, 1883, 60)
        client.loop_start()
        print("--- MQTT Connected ---")

        # 3. Vòng lặp chính (Giờ chỉ cần giữ chương trình chạy)
        while True:
            time.sleep(3)

    except KeyboardInterrupt:
        print("Exit.")
        if hasattr(lora, 'close'):
            lora.close()  # Dừng thread giả lập nếu có
        BOARD.teardown()
        client.disconnect()
