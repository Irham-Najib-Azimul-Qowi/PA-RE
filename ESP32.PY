from machine import Pin, PWM, I2C
from ssd1306 import SSD1306_I2C
import utime
import network
import umqtt.simple
import ujson
import gc  # For memory management

# WiFi Configuration
WIFI_SSID = "apasih"  # Replace with your WiFi SSID
WIFI_PASSWORD = "11111111"  # Replace with your WiFi password

# MQTT Configuration
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "esp32_door"
MQTT_TOPIC_DOOR = "lintas_alam/door"
MQTT_TOPIC_OLED = "lintas_alam/oled"
MQTT_TOPIC_FLASH = "lintas_alam/lampu"
MQTT_TOPIC_SCHEDULE = "lintas_alam/schedule"

# Servo Configuration
SERVO_PIN = 23
servo = PWM(Pin(SERVO_PIN), freq=50)  # 50Hz frequency for servo

# Flash Configuration (ESP32-CAM)
FLASH_PIN = 4  # GPIO 4 for flash
flash = Pin(FLASH_PIN, Pin.OUT)
flash.value(0)  # Flash off at start

# OLED Configuration
I2C_SDA = 21
I2C_SCL = 22
i2c = I2C(1, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA))
OLED_WIDTH = 128
OLED_HEIGHT = 64
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

# Ultrasonic Sensor HC-SR04 Configuration
TRIGGER_PIN = 5
ECHO_PIN = 18
trigger = Pin(TRIGGER_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)

# Servo Angles
CLOSE_ANGLE = 90
OPEN_ANGLE = 0
FULL_OPEN_ANGLE = 180  # For ultrasonic trigger

# Set servo angle with inverted rotation
def set_servo_angle(angle):
    try:
        angle = max(0, min(180, angle))  # Limit angle to 0-180
        inverted_angle = 180 - angle  # Invert angle for reverse rotation
        pulse_width = 500 + (1900 * inverted_angle // 180)  # 500us to 2400us
        duty = int(pulse_width * 1023 // 20000)  # Scale to duty cycle
        servo.duty(duty)
        print(f"Servo diatur ke: {angle} derajat (terbalik ke: {inverted_angle} derajat)")
        utime.sleep_ms(50)  # Small delay for stability
    except Exception as e:
        print(f"Galat servo: {e}")

# Control flash
def set_flash(state):
    try:
        if state == "ON":
            flash.value(1)
            print("Lampu menyala")
        elif state == "OFF":
            flash.value(0)
            print("Lampu mati")
    except Exception as e:
        print(f"Galat lampu: {e}")

# Display text on OLED
def display_text(text):
    try:
        oled.fill(0)
        lines = text.split('\n')
        y = 0
        for line in lines:
            if y < OLED_HEIGHT - 8:
                oled.text(line[:15], 0, y)  # Limit to 15 chars per line
                y += 8
        oled.show()
        print(f"OLED menampilkan: {text}")
    except Exception as e:
        print(f"Galat OLED: {e}")

# Display animated initialization text
def display_init_animation():
    try:
        text = "LINTAS ALAM"
        max_x = OLED_WIDTH
        for x in range(max_x, -len(text) * 8, -2):  # Scroll from right to left
            oled.fill(0)
            oled.text("Memulai...", 0, 0)
            oled.text(text, x, 16)
            oled.text("Samsung", 0, 32)
            oled.text("Innovation", 0, 40)
            oled.text("Campus", 0, 48)
            oled.show()
            utime.sleep_ms(50)  # Animation speed
        # Display final static text for 1 second
        oled.fill(0)
        oled.text("Memulai...", 0, 0)
        oled.text(text, 0, 16)
        oled.text("Samsung", 0, 32)
        oled.text("Innovation", 0, 40)
        oled.text("Campus", 0, 48)
        oled.show()
        utime.sleep_ms(1000)
    except Exception as e:
        print(f"Galat animasi OLED: {e}")
        display_text("Galat Inisialisasi")

# Display schedule on OLED
def display_schedule(payload):
    try:
        data = ujson.loads(payload)
        if "course" in data and data["course"] == "delete":
            text = "Tidak Ada\nMatkul\nMenunggu\nJadwal Baru"
            display_text(text)
        elif "person" in data and data["person"] == "delete":
            text = "Tidak Ada\nOrang\nMenunggu\nJadwal Baru"
            display_text(text)
        elif "course" in data:
            text = f"Mata Kuliah:\n{data['course']}\nMulai:\n{data['start']}\nSelesai:\n{data['end']}"
            display_text(text)
        elif "person" in data:
            text = f"Orang:\n{data['person']}\nMulai:\n{data['start']}\nSelesai:\n{data['end']}"
            display_text(text)
        else:
            text = "Jadwal Tidak\nValid"
            display_text(text)
    except Exception as e:
        print(f"Gagal memproses jadwal: {e}")
        display_text("Galat Jadwal")

# Measure distance using HC-SR04
def measure_distance():
    try:
        # Send 10us pulse to trigger
        trigger.value(0)
        utime.sleep_us(2)
        trigger.value(1)
        utime.sleep_us(10)
        trigger.value(0)

        # Measure echo pulse duration
        while echo.value() == 0:
            start = utime.ticks_us()
        while echo.value() == 1:
            end = utime.ticks_us()

        # Calculate distance (speed of sound = 343 m/s, or 0.0343 cm/us)
        duration = utime.ticks_diff(end, start)
        distance = (duration * 0.0343) / 2  # Divide by 2 for round trip
        print(f"Jarak: {distance:.2f} cm")
        return distance
    except Exception as e:
        print(f"Galat ultrasonik: {e}")
        return None

# Connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"Mencoba terhubung ke WiFi: {WIFI_SSID}")
        # Try to connect directly to the specified SSID
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 10
        start = utime.time()
        while not wlan.isconnected():
            if utime.time() - start > timeout:
                print("Batas waktu koneksi WiFi habis")
                # Perform a targeted scan to confirm SSID availability
                scan_results = wlan.scan()
                ssid_found = False
                for net in scan_results:
                    if net[0].decode() == WIFI_SSID:
                        ssid_found = True
                        break
                if not ssid_found:
                    print(f"WiFi SSID {WIFI_SSID} tidak ditemukan")
                    return False
                # Retry connection if SSID is found
                print(f"Mencoba kembali ke {WIFI_SSID}")
                wlan.connect(WIFI_SSID, WIFI_PASSWORD)
                start = utime.time()
                while not wlan.isconnected():
                    if utime.time() - start > timeout:
                        print("Koneksi WiFi gagal")
                        return False
                    utime.sleep_ms(500)
            utime.sleep_ms(500)
    print(f"WiFi terhubung: {wlan.ifconfig()}")
    return True

# MQTT callback for received messages
def on_message(topic, msg):
    try:
        topic_str = topic.decode()
        message = msg.decode()
        print(f"Pesan diterima di {topic_str}: {message}")
        if topic_str == MQTT_TOPIC_DOOR:
            if message == "OPEN":
                set_servo_angle(OPEN_ANGLE)
                display_text("Pintu Dibuka!")
            elif message == "CLOSE":
                set_servo_angle(CLOSE_ANGLE)
                display_text("Pintu Ditutup!")
        elif topic_str == MQTT_TOPIC_OLED:
            display_text(message)
        elif topic_str == MQTT_TOPIC_FLASH:
            set_flash(message)
        elif topic_str == MQTT_TOPIC_SCHEDULE:
            display_schedule(message)
        gc.collect()  # Free memory after processing
    except Exception as e:
        print(f"Galat dalam pemrosesan pesan: {e}")

# Initialize MQTT
def init_mqtt():
    try:
        client = umqtt.simple.MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.set_callback(on_message)
        client.connect()
        client.subscribe(MQTT_TOPIC_DOOR)
        client.subscribe(MQTT_TOPIC_OLED)
        client.subscribe(MQTT_TOPIC_FLASH)
        client.subscribe(MQTT_TOPIC_SCHEDULE)
        print("Terhubung ke broker MQTT")
        return client
    except Exception as e:
        print(f"Koneksi MQTT gagal: {e}")
        return None

# Main program
def main():
    # Connect to WiFi
    if not connect_wifi():
        display_text("Koneksi WiFi\nGagal")
        while True:
            utime.sleep(1)

    # Initialize OLED with animation
    display_init_animation()

    # Initialize Servo
    set_servo_angle(CLOSE_ANGLE)  # Close door at start
    display_text("Absen Ditutup!\n\nSilahkan\nHubungi\nDosen!")

    # Initialize MQTT
    client = init_mqtt()
    if client is None:
        display_text("Koneksi MQTT\nGagal")
        while True:
            utime.sleep(1)

    # Main loop
    last_distance_check = utime.time()
    while True:
        try:
            client.check_msg()  # Check for MQTT messages

            # Check distance every 500ms
            if utime.time() - last_distance_check > 0.5:
                distance = measure_distance()
                if distance is not None and distance < 10:
                    display_text("Pintu Otomatis!")
                    set_servo_angle(FULL_OPEN_ANGLE)  # Open to 180 degrees
                    utime.sleep(2)  # Wait for 2 seconds
                    set_servo_angle(CLOSE_ANGLE)  # Return to close
                    display_text("Absen Ditutup!\n\nSilahkan\nHubungi\nDosen!")
                last_distance_check = utime.time()

            utime.sleep_ms(200)  # Increase delay to reduce load
            gc.collect()  # Free memory periodically
        except Exception as e:
            print(f"Galat MQTT: {e}")
            client.disconnect()
            client = init_mqtt()
            if client is None:
                display_text("Koneksi MQTT\nGagal")
                utime.sleep(5)
                display_text("Absen Ditutup!\n\nSilahkan\nHubungi\nDosen!")

if __name__ == "__main__":
    main()