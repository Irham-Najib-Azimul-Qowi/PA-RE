import paho.mqtt.client as mqtt
import cv2
import numpy as np
import face_recognition
import os
import pickle
import json
from datetime import datetime
import requests
from io import BytesIO
import time
import logging
import pandas as pd
from typing import List, Tuple, Dict, Optional
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    UBIDOTS_TOKEN = "BBUS-w4hoDRHaDcWGfZAO4RZITgVz6EoLhq"
    UBIDOTS_DEVICE = "face_recognation"
    UBIDOTS_URL = f"https://industrial.api.ubidots.com/api/v1.6/devices/{UBIDOTS_DEVICE}"

    MQTT_BROKER = "broker.emqx.io"
    MQTT_PORT = 1883
    MQTT_TOPICS = {
        "ip": "lintas_alam/ip",
        "detected": "lintas_alam/detected_person",
        "names": "lintas_alam/dataset_names",
        "schedule": "lintas_alam/schedule",
        "door": "lintas_alam/door",
        "oled": "lintas_alam/oled",
        "attendance_share": "lintas_alam/attendance_share",
        "auto_door": "lintas_alam/auto_door"
    }

    DATASET_PATH = "dataset"
    ENCODINGS_FILE = "encoding/face_encodings.pkl"
    DATASET_INFO_FILE = "metadata/dataset_info.txt"
    ATTENDANCE_CSV = "attendance_log.csv"

class SystemState:
    def __init__(self):
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_names: List[str] = []
        self.mqtt_client: Optional[mqtt.Client] = None
        self.esp32_cam_ip: Optional[str] = None
        self.video_running: bool = False
        self.stream_session: Optional[requests.Session] = None
        self.stream_response: Optional[requests.Response] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.last_detected: Dict[str, datetime] = {}
        self.schedule_course: Optional[Tuple[datetime, datetime]] = None
        self.current_course_name: Optional[str] = None
        self.schedule_individual: Dict[str, Tuple[datetime, datetime]] = {}
        self.detected_persons: Dict[str, datetime] = {}
        self.detection_data: List[Dict[str, str]] = []
        self.attendance_status: Dict[str, Dict[str, str]] = {}
        self.last_oled_message: Optional[str] = None
        self.frame_count: int = 0
        self.use_local_camera: bool = False
        self.door_open_time: Optional[datetime] = None
        self.attendance_recorded: Dict[Tuple[str, str], bool] = {}
        self.sent_to_ubidots: Dict[Tuple[str, str], bool] = {}

state = SystemState()

def send_to_ubidots(name: str, timestamp: Optional[int] = None) -> None:
    """Mengirim data absensi siswa dan mata kuliah ke Ubidots hanya untuk nama yang dikenali."""
    if name not in state.known_face_names and name != "door_status":
        logger.warning(f"Nama {name} tidak dikenali, pengiriman ke Ubidots diabaikan")
        return

    headers = {"X-Auth-Token": Config.UBIDOTS_TOKEN, "Content-Type": "application/json"}
    timestamp_ms = timestamp or int(time.time() * 1000)
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    course_name = state.current_course_name or "Tidak ada jadwal"
    payload = {
        "person_presence": {
            "value": 1,
            "timestamp": timestamp_ms,
            "context": {
                "name": name,
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M:%S"),
                "course": course_name
            }
        },
        "attendance_timestamp": {
            "value": timestamp_ms,
            "timestamp": timestamp_ms
        }
    }

    try:
        response = requests.post(Config.UBIDOTS_URL, json=payload, headers=headers, timeout=5)
        if response.status_code in [200, 201]:
            logger.info(f"Berhasil kirim nama={name}, mata kuliah={course_name} ke Ubidots")
        else:
            logger.error(f"Gagal kirim ke Ubidots: HTTP {response.status_code}, {response.text}")
    except requests.RequestException as e:
        logger.error(f"Error koneksi Ubidots: {e}")

def send_auto_door_to_ubidots(status: str, timestamp: Optional[int] = None) -> None:
    """Mengirim status pintu otomatis ke Ubidots."""
    headers = {"X-Auth-Token": Config.UBIDOTS_TOKEN, "Content-Type": "application/json"}
    timestamp_ms = timestamp or int(time.time() * 1000)
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    payload = {
        "auto_door_status": {
            "value": 1 if status == "OPEN" else 0,
            "timestamp": timestamp_ms,
            "context": {
                "status": status,
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M:%S")
            }
        }
    }

    try:
        response = requests.post(Config.UBIDOTS_URL, json=payload, headers=headers, timeout=5)
        if response.status_code in [200, 201]:
            logger.info(f"Berhasil kirim status pintu otomatis={status} ke Ubidots")
        else:
            logger.error(f"Gagal kirim ke Ubidots: HTTP {response.status_code}, {response.text}")
    except requests.RequestException as e:
        logger.error(f"Error koneksi Ubidots: {e}")

def save_attendance_to_csv() -> None:
    """Menyimpan tabel absensi ke file CSV."""
    table = update_attendance_table()
    if not table.empty:
        table.to_csv(Config.ATTENDANCE_CSV, index=False)
        logger.info(f"Tabel absensi disimpan ke {Config.ATTENDANCE_CSV}")

def publish_attendance_to_mqtt(name: str, timestamp_str: str) -> None:
    """Mempublikasikan data absensi ke MQTT hanya pada satu topik."""
    if state.mqtt_client:
        data = {
            "name": name,
            "timestamp": timestamp_str,
            "status": "Hadir",
            "course": state.current_course_name or "Tidak ada jadwal"
        }
        state.mqtt_client.publish(Config.MQTT_TOPICS["detected"], json.dumps(data))
        logger.info(f"Data absensi dipublikasikan: {data}")

def is_within_schedule(schedule: Optional[Tuple[datetime, datetime]], now: datetime) -> bool:
    """Memeriksa apakah waktu saat ini dalam rentang jadwal."""
    if not schedule:
        return False
    start, end = schedule
    return start.date() == now.date() and start <= now <= end

def check_schedule(name: str, now: datetime = datetime.now()) -> bool:
    """Memeriksa apakah deteksi sesuai jadwal."""
    course_ok = is_within_schedule(state.schedule_course, now)
    individual_ok = is_within_schedule(state.schedule_individual.get(name), now)
    result = course_ok or individual_ok
    logger.debug(f"Schedule check for {name}: course={course_ok}, individual={individual_ok}, result={result}")
    return result

def publish_schedule_status() -> None:
    """Mengirim pesan OLED berdasarkan status jadwal."""
    if not state.mqtt_client:
        return
    message = "Silahkan Absen!" if check_schedule("") else "Absen Ditutup!\nSilahkan Hubungi Dosen!"
    if state.last_oled_message != message:
        state.mqtt_client.publish(Config.MQTT_TOPICS["oled"], message)
        state.last_oled_message = message
        logger.info(f"Pesan OLED: {message}")

def open_door_and_display(name: str) -> None:
    """Membuka pintu dan menampilkan pesan OLED."""
    if not state.mqtt_client:
        logger.error("MQTT client tidak tersedia")
        return
    logger.info(f"Proses absensi untuk {name}")
    state.mqtt_client.publish(Config.MQTT_TOPICS["door"], "OPEN")
    state.door_open_time = datetime.now()
    timestamp = int(time.time() * 1000)
    current_time_str = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
    key = (name, current_time_str)

    if key not in state.sent_to_ubidots or not state.sent_to_ubidots[key]:
        logger.debug(f"Mengirim data ke Ubidots untuk {name} dengan timestamp {timestamp}")
        send_to_ubidots(name, timestamp)
        state.sent_to_ubidots[key] = True
    else:
        logger.debug(f"Data untuk {name} dengan timestamp {current_time_str} sudah dikirim ke Ubidots, diabaikan")

    send_auto_door_to_ubidots("OPEN", timestamp)
    state.mqtt_client.publish(Config.MQTT_TOPICS["oled"], f"{name} telah absen\nSilahkan masuk!")
    
    def close_door():
        try:
            time.sleep(7)
            logger.info("Mengirim perintah CLOSE ke pintu")
            state.mqtt_client.publish(Config.MQTT_TOPICS["door"], "CLOSE")
            send_auto_door_to_ubidots("CLOSE", int(time.time() * 1000))
            state.door_open_time = None
            logger.info(f"Pintu ditutup setelah absen {name}")
        except Exception as e:
            logger.error(f"Gagal menutup pintu: {e}")
    
    threading.Thread(target=close_door, daemon=True).start()
    publish_schedule_status()

def get_dataset_info() -> List[str]:
    """Mengambil daftar file gambar dari dataset."""
    file_list = []
    if os.path.exists(Config.DATASET_PATH):
        for person_name in sorted(os.listdir(Config.DATASET_PATH)):
            person_path = os.path.join(Config.DATASET_PATH, person_name)
            if os.path.isdir(person_path):
                file_list.extend(
                    os.path.join(person_path, image_name)
                    for image_name in sorted(os.listdir(person_path))
                )
    return file_list

def save_encodings(encodings: List[np.ndarray], names: List[str]) -> None:
    """Menyimpan encoding wajah."""
    os.makedirs(os.path.dirname(Config.ENCODINGS_FILE), exist_ok=True)
    with open(Config.ENCODINGS_FILE, "wb") as f:
        pickle.dump({"encodings": encodings, "names": names}, f)

def load_encodings() -> Tuple[List[np.ndarray], List[str]]:
    """Memuat encoding wajah."""
    if os.path.exists(Config.ENCODINGS_FILE):
        with open(Config.ENCODINGS_FILE, "rb") as f:
            data = pickle.load(f)
        return data["encodings"], data["names"]
    return [], []

def save_dataset_info(file_list: List[str]) -> None:
    """Menyimpan info dataset."""
    os.makedirs(os.path.dirname(Config.DATASET_INFO_FILE), exist_ok=True)
    with open(Config.DATASET_INFO_FILE, "w") as f:
        f.write("\n".join(file_list))

def load_dataset_info() -> List[str]:
    """Memuat info dataset."""
    if os.path.exists(Config.DATASET_INFO_FILE):
        with open(Config.DATASET_INFO_FILE, "r") as f:
            return [line.strip() for line in f]
    return []

def load_known_faces() -> Tuple[List[np.ndarray], List[str]]:
    """Memuat encoding wajah dari dataset."""
    encodings, names = [], []
    if not os.path.exists(Config.DATASET_PATH):
        return encodings, names
    for person_name in os.listdir(Config.DATASET_PATH):
        person_path = os.path.join(Config.DATASET_PATH, person_name)
        if not os.path.isdir(person_path):
            continue
        for image_name in os.listdir(person_path):
            image_path = os.path.join(person_path, image_name)
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            if face_encodings:
                encodings.append(face_encodings[0])
                names.append(person_name)
    return encodings, names

def publish_dataset_names() -> None:
    """Mengirim daftar nama siswa ke MQTT."""
    if state.mqtt_client and state.known_face_names:
        names_data = {"names": list(set(state.known_face_names))}
        state.mqtt_client.publish(Config.MQTT_TOPICS["names"], json.dumps(names_data))
        logger.info(f"Daftar nama siswa: {names_data}")

def on_connect(client: mqtt.Client, userdata, flags, rc, properties=None) -> None:
    """Callback saat terhubung ke MQTT."""
    if rc == 0:
        logger.info("Terhubung ke MQTT")
        client.subscribe([
            (Config.MQTT_TOPICS["ip"], 0),
            (Config.MQTT_TOPICS["schedule"], 0),
            (Config.MQTT_TOPICS["auto_door"], 0)
        ])
        publish_dataset_names()
    else:
        logger.error(f"Gagal terhubung ke MQTT, kode: {rc}")

def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
    """Callback saat menerima pesan MQTT."""
    try:
        message = msg.payload.decode()
        topic = msg.topic
        logger.debug(f"Pesan MQTT di {topic}: {message}")
        
        if topic == Config.MQTT_TOPICS["ip"]:
            state.esp32_cam_ip = message
            logger.info(f"IP ESP32-CAM: {state.esp32_cam_ip}")
        
        elif topic == Config.MQTT_TOPICS["schedule"]:
            data = json.loads(message)
            start = datetime.strptime(data["start"], "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(data["end"], "%Y-%m-%d %H:%M:%S")
            if "course" in data:
                state.schedule_course = (start, end)
                new_course_name = data.get("course", "Tidak ada jadwal")
                state.current_course_name = new_course_name
                for name in state.known_face_names:
                    state.attendance_recorded[(name, new_course_name)] = False
                logger.info(f"Jadwal mata kuliah: {new_course_name}, {start} - {end}")
            elif "person" in data:
                state.schedule_individual[data["person"]] = (start, end)
                logger.info(f"Jadwal individu {data['person']}: {start} - {end}")
            publish_schedule_status()
        
        elif topic == Config.MQTT_TOPICS["auto_door"]:
            logger.info(f"Pintu otomatis: {message}")
            send_auto_door_to_ubidots(message, int(time.time() * 1000))
            if message not in ["OPEN", "CLOSE"]:
                logger.warning(f"Pesan {message} di topik auto_door diabaikan karena bukan status pintu yang valid")
            else:
                state.detection_data.append({
                    "nama": "Pintu Otomatis",
                    "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    except Exception as e:
        logger.error(f"Error pesan MQTT di {topic}: {e}")

def init_mqtt() -> Optional[mqtt.Client]:
    """Inisialisasi client MQTT."""
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)
        client.loop_start()
        return client
    except Exception as e:
        logger.error(f"Gagal menghubungkan MQTT: {e}")
        return None

def start_video_stream() -> bool:
    """Memulai streaming video."""
    if state.video_running:
        logger.info("Streaming sudah berjalan")
        return True
    
    if state.use_local_camera:
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
        for backend in backends:
            for index in range(3):
                try:
                    cap = cv2.VideoCapture(index, backend)
                    if cap.isOpened():
                        state.cap = cap
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        state.video_running = True
                        logger.info(f"Kamera lokal dibuka dengan backend {backend} pada indeks {index}")
                        return True
                except Exception as e:
                    logger.error(f"Gagal membuka kamera lokal dengan backend {backend} pada indeks {index}: {e}")
        logger.error("Gagal membuka kamera lokal")
        return False
    
    if not state.esp32_cam_ip:
        logger.warning("IP ESP32-CAM tidak tersedia")
        return False

    stream_url = f"http://{state.esp32_cam_ip}/stream"
    for attempt in range(3):
        try:
            state.stream_session = requests.Session()
            state.stream_response = state.stream_session.get(stream_url, stream=True, timeout=10)
            state.stream_response.raise_for_status()
            logger.info(f"Streaming dimulai: {stream_url}")
            state.video_running = True
            return True
        except requests.RequestException as e:
            logger.error(f"Percobaan {attempt + 1}/3 gagal: {e}")
            stop_video_stream()
            time.sleep(1)
    logger.error("Gagal memulai streaming")
    return False

def stop_video_stream() -> None:
    """Menghentikan streaming video."""
    if state.use_local_camera and state.cap is not None:
        state.cap.release()
        state.cap = None
        logger.info("Kamera lokal dilepaskan")
    if state.stream_session:
        state.stream_session.close()
        state.stream_session = None
        state.stream_response = None
        logger.info("Streaming ESP32-CAM dihentikan")
    state.video_running = False

def get_mjpeg_frame() -> Optional[np.ndarray]:
    """Mengambil frame video."""
    if state.use_local_camera:
        if state.cap is not None:
            ret, frame = state.cap.read()
            if ret:
                return frame
            logger.warning("Gagal membaca frame dari kamera lokal")
            stop_video_stream()
            return None
        return None

    if not state.video_running or not state.stream_session:
        return None

    buffer = b""
    max_buffer_size = 512 * 1024
    timeout = time.time() + 8

    try:
        for chunk in state.stream_response.iter_content(chunk_size=2048):
            if time.time() > timeout:
                logger.error("Timeout MJPEG")
                stop_video_stream()
                return None

            buffer += chunk
            if len(buffer) > max_buffer_size:
                buffer = buffer[buffer.find(b"--frame"):] if b"--frame" in buffer else b""

            content_length_pos = buffer.find(b"Content-Length: ")
            if content_length_pos == -1:
                continue

            content_length_end = buffer.find(b"\r\n", content_length_pos)
            content_length = int(buffer[content_length_pos + 16:content_length_end])
            data_start = buffer.find(b"\r\n\r\n") + 4

            if data_start < 4 or len(buffer) < data_start + content_length:
                continue

            jpeg_data = buffer[data_start:data_start + content_length]
            buffer = buffer[data_start + content_length:]

            frame = cv2.imdecode(np.frombuffer(jpeg_data, np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                return frame
            logger.warning("Gagal dekode frame")
    except Exception as e:
        logger.error(f"Error MJPEG: {e}")
        stop_video_stream()
        return None

def process_video_frame(frame: np.ndarray) -> Optional[np.ndarray]:
    """Memproses frame untuk deteksi wajah, mengabaikan wajah 'Unknown' dan mencegah duplikat absensi per jadwal."""
    if frame is None:
        return None

    # Rotate frame -90 degrees (clockwise 90 degrees)
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    state.frame_count += 1
    if state.frame_count % 3 != 0:
        return frame

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    try:
        face_locations = face_recognition.face_locations(rgb_frame, model="hog", number_of_times_to_upsample=1)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        logger.debug(f"Frame {state.frame_count}: {len(face_locations)} wajah")

        current_time = datetime.now()
        current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        course_name = state.current_course_name or "Tidak ada jadwal"

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(state.known_face_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"

            if any(matches):
                face_distances = face_recognition.face_distance(state.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index] and face_distances[best_match_index] < 0.5:
                    name = state.known_face_names[best_match_index]

            if name == "Unknown":
                logger.debug(f"Wajah tidak dikenali diabaikan pada frame {state.frame_count}")
                continue

            if name not in state.known_face_names:
                logger.warning(f"Nama {name} tidak ada di dataset, diabaikan")
                continue

            key = (name, course_name)
            if key not in state.attendance_recorded:
                state.attendance_recorded[key] = False
            if state.attendance_recorded[key]:
                logger.debug(f"Absensi untuk {name} pada {course_name} sudah tercatat, diabaikan")
                continue

            if check_schedule(name, current_time):
                state.last_detected[name] = current_time
                state.detected_persons[name] = current_time

                entry_exists = any(
                    entry["nama"] == name and entry["waktu"] == current_time_str
                    for entry in state.detection_data
                )
                if not entry_exists:
                    state.detection_data.append({"nama": name, "waktu": current_time_str})

                state.attendance_status[name] = {
                    "status": "Hadir",
                    "waktu": current_time_str,
                    "course": course_name
                }
                publish_attendance_to_mqtt(name, current_time_str)
                save_attendance_to_csv()
                open_door_and_display(name)
                state.attendance_recorded[key] = True
            else:
                logger.info(f"Deteksi {name} diabaikan: di luar jadwal")

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    except Exception as e:
        logger.error(f"Error deteksi wajah: {e}")

    return frame

def update_attendance_table() -> pd.DataFrame:
    """Membuat tabel absensi tanpa duplikat."""
    unique_attendance = {}
    for name in set(state.known_face_names):
        unique_attendance[name] = state.attendance_status.get(name, {"status": "Tidak Hadir", "waktu": "-", "course": "Tidak ada jadwal"})

    data = [
        {
            "Nama": name,
            "Status": entry["status"],
            "Waktu": entry["waktu"],
            "Mata Kuliah": entry["course"]
        }
        for name, entry in unique_attendance.items()
    ]
    df = pd.DataFrame(data) if data else pd.DataFrame(columns=["Nama", "Status", "Waktu", "Mata Kuliah"])
    logger.debug(f"Tabel absensi: {len(data)} entri")
    return df

def main():
    """Fungsi utama."""
    state.mqtt_client = init_mqtt()
    if not state.mqtt_client:
        logger.error("Gagal inisialisasi MQTT")
        return

    current_dataset = get_dataset_info()
    saved_dataset = load_dataset_info()

    if current_dataset != saved_dataset:
        logger.info("Dataset berubah, memperbarui encoding...")
        state.known_face_encodings, state.known_face_names = load_known_faces()
        save_encodings(state.known_face_encodings, state.known_face_names)
        save_dataset_info(current_dataset)
    else:
        logger.info("Dataset tidak berubah, memuat encoding...")
        state.known_face_encodings, state.known_face_names = load_encodings()

    logger.info(f"Wajah dimuat: {len(state.known_face_names)}")
    for name in set(state.known_face_names):
        state.attendance_status.setdefault(name, {"status": "Tidak Hadir", "waktu": "-", "course": "Tidak ada jadwal"})
    publish_dataset_names()

    try:
        while True:
            if state.door_open_time and (datetime.now() - state.door_open_time).total_seconds() > 10:
                logger.warning("Pintu terbuka terlalu lama, mengirim perintah CLOSE")
                state.mqtt_client.publish(Config.MQTT_TOPICS["door"], "CLOSE")
                send_auto_door_to_ubidots("CLOSE", int(time.time() * 1000))
                state.door_open_time = None

            if not state.video_running and (state.esp32_cam_ip or state.use_local_camera):
                if not start_video_stream():
                    state.esp32_cam_ip = None
                    time.sleep(1)
                    continue

            if state.video_running:
                frame = get_mjpeg_frame()
                if frame is None:
                    logger.warning("Gagal menerima frame")
                    time.sleep(0.1)
                    continue

                processed_frame = process_video_frame(frame)
                if processed_frame is not None:
                    cv2.imshow("Face Recognition", processed_frame)

                if state.frame_count % 30 == 0:
                    table = update_attendance_table()
                    if not table.empty:
                        print("\n=== Tabel Absensi ===")
                        print(table.to_string(index=False))
                        print("=====================\n")
                        save_attendance_to_csv()

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("Menghentikan aplikasi")
                    break

            time.sleep(0.03)

    finally:
        stop_video_stream()
        cv2.destroyAllWindows()
        if state.mqtt_client:
            state.mqtt_client.loop_stop()
            state.mqtt_client.disconnect()
            logger.info("MQTT ditutup")
        save_attendance_to_csv()

if __name__ == "__main__":
    main()