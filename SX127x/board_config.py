# FILE: SX127x/board_config.py
import RPi.GPIO as GPIO
import spidev
import time

class BOARD:
    # --- CẤU HÌNH ---
    DIO0 = 22   # Chân ngắt (Kiểm tra kỹ xem dây xanh dương cắm pin 15 hay 17?)
    
    # QUAN TRỌNG: Đặt RST = None vì bạn không đấu dây
    RST  = None 
    
    # Các chân thừa
    DIO1 = 23; DIO2 = 24; DIO3 = 27; LED = 18; SWITCH = 4
    low_band = False
    spi = None

    @staticmethod
    def setup():
        try:
            GPIO.setmode(GPIO.BCM)
        except:
            pass
        GPIO.setwarnings(False)
        
        # --- BỎ QUA PHẦN RESET CỨNG ---
        # Vì bạn không đấu dây Reset
        # ------------------------------

        # Setup chân DIO0 input với trở kéo xuống (PUD_DOWN) để chống nhiễu
        GPIO.setup(BOARD.DIO0, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    @staticmethod
    def teardown():
        try:
            GPIO.remove_event_detect(BOARD.DIO0)
        except:
            pass
        GPIO.cleanup()
        if BOARD.spi: BOARD.spi.close()

    @staticmethod
    def SpiDev():
        BOARD.spi = spidev.SpiDev()
        BOARD.spi.open(0, 0)
       # BOARD.spi.max_speed_hz = 5000000 
        BOARD.spi.max_speed_hz = 500000
        return BOARD.spi

    @staticmethod
    def add_events(cb_dio0, cb_dio1=None, cb_dio2=None, cb_dio3=None, cb_dio4=None, cb_dio5=None):
        try:
            GPIO.remove_event_detect(BOARD.DIO0)
        except:
            pass
        # Thêm sự kiện ngắt (Thêm bouncetime=100ms để lọc nhiễu)
        GPIO.add_event_detect(BOARD.DIO0, GPIO.RISING, callback=cb_dio0, bouncetime=100)