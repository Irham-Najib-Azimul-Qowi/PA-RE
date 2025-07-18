# 📸 PA-RE (Presensi Absensi Real-Time)

**PA-RE (Presensi Absensi Real-Time)** adalah sistem absensi berbasis web yang dirancang untuk memberikan solusi absensi yang efisien, akurat, dan real-time. Sistem ini memanfaatkan **ESP32-CAM** untuk menangkap gambar pengguna saat melakukan presensi, memastikan keamanan dan validitas data. PA-RE sangat cocok untuk berbagai kegiatan seperti lintas alam, pelatihan, acara organisasi, atau lingkungan pendidikan yang membutuhkan pencatatan kehadiran berbasis teknologi.

🌐 **Akses Dashboard IoT**: Kunjungi [https://absensi-lintas-alam-web.vercel.app/](https://absensi-lintas-alam-web.vercel.app/) untuk melihat dashboard absensi real-time yang telah dikembangkan oleh tim kami.

---

## 🚀 Fitur Utama

- **Presensi Real-Time**  
  Pengguna dapat melakukan absensi secara langsung melalui antarmuka web, dengan data yang langsung tersinkronisasi.

- **Integrasi ESP32-CAM**  
  Menggunakan ESP32-CAM untuk menangkap foto pengguna saat absensi, memastikan bahwa presensi dilakukan oleh orang yang tepat.

- **Dashboard Admin Interaktif**  
  Admin dapat melihat data presensi melalui dashboard yang user-friendly di [https://absensi-lintas-alam-web.vercel.app/](https://absensi-lintas-alam-web.vercel.app/).

- **Jadwal Absensi Otomatis**  
  Sistem mendukung pengaturan jadwal (baik untuk mata kuliah atau individu), yang akan dikirim ke ESP32 melalui protokol MQTT untuk mengontrol waktu absensi.

- **API Terstruktur**  
  Backend menyediakan API yang terorganisir untuk mendukung pengembangan lebih lanjut, seperti integrasi dengan aplikasi lain.

- **Deployment Mudah**  
  Konfigurasi proyek kompatibel dengan Vercel untuk deployment frontend yang cepat, sementara backend dapat dijalankan di server lokal atau cloud.

---

## 🧱 Struktur Proyek

Berikut adalah struktur direktori proyek PA-RE:

```
PA-RE/
├── ESP32-CAM/               # Kode dan konfigurasi untuk ESP32-CAM
│   ├── esp32_cam.ino        # Skrip utama Arduino untuk ESP32-CAM
│   └── config.h             # File konfigurasi (SSID, password, server URL)
├── api/                     # Endpoint API untuk backend
│   ├── routes/              # Definisi rute API (misalnya, save-message, get-messages)
│   └── middleware/          # Middleware untuk autentikasi dan validasi
├── docs/                    # Dokumentasi proyek
│   ├── setup.md             # Panduan setup lebih lanjut
│   └── api.md               # Dokumentasi API
├── lib/                     # Library dan utilitas pendukung
│   ├── mqtt.js              # Klien MQTT untuk komunikasi dengan ESP32
│   └── chart.min.js         # Library Chart.js untuk visualisasi data
├── models/                  # Definisi model data
├── public/                  # Aset publik
│   ├── index.html           # Halaman utama aplikasi web
│   ├── style.css            # Stylesheet untuk antarmuka
│   └── script.js            # Logika JavaScript untuk frontend
├── .env                     # Variabel lingkungan (contoh: secret key)
├── ESP32.PY                 # Skrip Python untuk komunikasi dengan ESP32
├── SERVER.py                # Server backend utama menggunakan Flask
├── requirements.txt         # Daftar dependensi Python
├── package.json             # Dependensi dan skrip Node.js untuk frontend
├── vercel.json              # Konfigurasi untuk deployment di Vercel
└── LICENSE                  # Lisensi MIT
```

---

## ⚙️ Teknologi yang Digunakan

- **Frontend**  
  - HTML5, CSS3, JavaScript (ES6)
  - Chart.js untuk visualisasi data di dashboard
  - MQTT.js untuk komunikasi real-time dengan ESP32

- **Backend**  
  - Python 3.8+ dengan framework Flask
  - Paho MQTT untuk komunikasi dengan ESP32
  - Face Recognition (library Python) untuk deteksi wajah

- **Microcontroller**  
  - ESP32-CAM dengan modul kamera OV2640
  - Arduino IDE untuk pemrograman ESP32-CAM

- **Deployment**  
  - Vercel untuk deployment frontend
  - Local server atau VPS (misalnya, AWS, DigitalOcean) untuk backend

- **Protokol Komunikasi**  
  - MQTT (broker: `broker.emqx.io`, port: 1883)
  - HTTP untuk komunikasi API

---

## 🛠️ Tutorial Setup Lengkap

### Prasyarat
Sebelum memulai, pastikan Anda memiliki:
- Python 3.8+ dan pip terinstal
- Node.js dan npm untuk dependensi frontend
- Arduino IDE untuk mengunggah kode ke ESP32-CAM
- Koneksi internet stabil untuk MQTT

### 1. Kloning Proyek
Klon repositori ke komputer Anda:
```bash
git clone https://github.com/Irham-Najib-Azimul-Qowi/PA-RE.git
cd PA-RE
```

### 2. Siapkan Lingkungan Backend
#### a. Instal Dependensi Python
Pastikan Anda berada di direktori proyek, lalu instal dependensi:
```bash
pip install -r requirements.txt
```
Dependensi utama meliputi:
- `flask`
- `paho-mqtt`
- `face_recognition`
- `opencv-python`

#### b. Konfigurasi Variabel Lingkungan
Buat file `.env` di root direktori proyek dan isi dengan kredensial berikut:
```env
# Kunci rahasia untuk aplikasi Flask
SECRET_KEY=your_secret_key_here

# MQTT Broker (opsional, default: broker.emqx.io)
MQTT_BROKER=broker.emqx.io
MQTT_PORT=1883
```

> **Catatan**: Ganti `SECRET_KEY` dengan nilai yang aman.

#### c. Siapkan Folder Dataset
Buat folder `dataset` untuk menyimpan gambar wajah pengguna:
```bash
mkdir dataset
```
Struktur folder dataset:
```
dataset/
├── nama_pengguna_1/
│   ├── 1.jpg
│   └── 2.jpg
├── nama_pengguna_2/
│   ├── 1.jpg
│   └── 2.jpg
```

### 3. Jalankan Server Backend
Jalankan server Flask untuk menangani API dan komunikasi MQTT:
```bash
python SERVER.py
```
Server akan berjalan di `http://localhost:5000`. Anda akan melihat log seperti:
```
2025-05-05 10:00:00,123 - INFO - Terhubung ke MQTT
2025-05-05 10:00:00,125 - INFO - * Running on http://127.0.0.1:5000
```

### 4. Setup ESP32-CAM
#### a. Siapkan Perangkat Keras
- Pastikan ESP32-CAM terhubung dengan modul kamera OV2640.
- Gunakan kabel USB untuk menghubungkan ESP32-CAM ke komputer.

#### b. Konfigurasi Kode
1. Buka Arduino IDE.
2. Buka file `ESP32-CAM/esp32_cam.ino`.
3. Edit file `ESP32-CAM/config.h` untuk mengatur kredensial WiFi dan URL server:
   ```cpp
   #define WIFI_SSID "your_wifi_ssid"
   #define WIFI_PASSWORD "your_wifi_password"
   #define SERVER_URL "http://your_server_ip:5000"
   #define MQTT_SERVER "broker.emqx.io"
   #define MQTT_PORT 1883
   ```
   Ganti `your_wifi_ssid`, `your_wifi_password`, dan `your_server_ip` sesuai dengan konfigurasi Anda.

#### c. Unggah Kode
1. Hubungkan ESP32-CAM ke komputer melalui USB.
2. Pilih board **ESP32 Wrover Module** di Arduino IDE.
3. Pilih port yang sesuai di menu **Tools > Port**.
4. Unggah kode ke ESP32-CAM:
   - Klik tombol **Upload** di Arduino IDE.
   - Jika gagal, tekan tombol **BOOT** pada ESP32-CAM saat proses upload dimulai.

#### d. Verifikasi Koneksi
Buka Serial Monitor di Arduino IDE (baud rate: 115200) untuk memastikan ESP32-CAM terhubung ke WiFi dan MQTT broker. Anda akan melihat pesan seperti:
```
WiFi connected
IP Address: 192.168.1.100
MQTT connected
```

### 5. Siapkan Frontend
#### a. Instal Dependensi Node.js
Instal dependensi frontend yang diperlukan (misalnya, MQTT.js, Chart.js):
```bash
npm install
```

#### b. Jalankan Frontend Secara Lokal
Buka file `public/index.html` di browser untuk mengakses antarmuka web. Pastikan server backend (`SERVER.py`) sedang berjalan agar frontend dapat terhubung ke API dan MQTT. Alternatifnya, akses dashboard langsung di [https://absensi-lintas-alam-web.vercel.app/](https://absensi-lintas-alam-web.vercel.app/).

### 6. Deploy ke Vercel (Opsional)
Jika Anda ingin mendeploy frontend ke Vercel:
#### a. Siapkan Repositori
Pastikan repositori Anda sudah di-push ke GitHub:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

#### b. Konfigurasi Vercel
1. Login ke [Vercel](https://vercel.com) menggunakan akun GitHub Anda.
2. Impor repositori `PA-RE` dari GitHub.
3. Atur konfigurasi di `vercel.json`:
   ```json
   {
       "version": 2,
       "builds": [
           {
               "src": "public/**",
               "use": "@vercel/static"
           }
       ],
       "routes": [
           {
               "src": "/(.*)",
               "dest": "public/$1"
           }
       ]
   }
   ```
4. Deploy proyek. Vercel akan memberikan URL publik, misalnya: `https://pa-re.vercel.app`.

#### c. Catatan Deployment
- Backend (`SERVER.py`) tetap harus berjalan di server lokal atau VPS karena Vercel hanya mendukung aplikasi statis untuk frontend.
- Pastikan URL API di `public/script.js` diubah ke alamat server backend Anda:
  ```javascript
  const apiUrl = 'http://your_server_ip:5000';
  ```

---

## 📷 Contoh Antarmuka

Berikut adalah tampilan antarmuka sistem PA-RE, yang dapat diakses di [https://absensi-lintas-alam-web.vercel.app/](https://absensi-lintas-alam-web.vercel.app/):

- **Dashboard Admin**  
  ![Dashboard Admin](public/screenshots/dashboard.png)

- **Halaman Presensi**  
  ![Halaman Presensi](public/screenshots/presensi.png)

- **Pengaturan Jadwal**  
  ![Pengaturan Jadwal](public/screenshots/schedule.png)

> **Catatan**: Tambahkan tangkapan layar ke folder `public/screenshots/` dan perbarui path di atas sesuai kebutuhan.

---

## 🔍 Cara Kerja Sistem

1. **ESP32-CAM**:
   - ESP32-CAM menangkap gambar dan mengirimkan data ke server melalui HTTP atau MQTT.
   - ESP32 juga menerima jadwal absensi melalui MQTT untuk mengontrol waktu pengambilan gambar.

2. **Backend (SERVER.py)**:
   - Server Flask menangani API untuk memproses data absensi.
   - Menggunakan Face Recognition untuk memverifikasi wajah pengguna dari gambar yang dikirim ESP32-CAM.
   - Mengirimkan notifikasi ke ESP32 (misalnya, membuka pintu) melalui MQTT.

3. **Frontend (index.html)**:
   - Menampilkan dashboard dengan data absensi, grafik, dan log aktivitas di [https://absensi-lintas-alam-web.vercel.app/](https://absensi-lintas-alam-web.vercel.app/).
   - Memungkinkan admin untuk mengatur jadwal dan mengunggah dataset wajah pengguna.

---

## 🛠️ Troubleshooting

### 1. Server Gagal Memproses Data
- Periksa log server untuk kesalahan, misalnya:
  ```
  Error pesan MQTT: Connection refused
  ```
- Pastikan semua dependensi terinstal dengan benar (`pip install -r requirements.txt`).

### 2. ESP32-CAM Tidak Terhubung ke WiFi
- Periksa SSID dan password di `config.h`.
- Pastikan ESP32-CAM dalam jangkauan WiFi.
- Gunakan Serial Monitor untuk debugging.

### 3. MQTT Tidak Berfungsi
- Pastikan broker (`broker.emqx.io`) dapat diakses.
- Periksa log server untuk pesan seperti:
  ```
  Gagal terhubung ke MQTT, kode: 5
  ```

### 4. Wajah Tidak Terdeteksi
- Pastikan gambar di folder `dataset` memiliki wajah yang jelas.
- Tambahkan lebih banyak gambar per pengguna (minimal 2-3 gambar).

---

## 🤝 Kontribusi

Kami sangat menyambut kontribusi untuk meningkatkan PA-RE. Ikuti langkah berikut:

1. **Fork Repositori**  
   Klik tombol "Fork" di GitHub untuk membuat salinan repositori.

2. **Buat Branch Fitur**  
   ```bash
   git checkout -b fitur/fitur-baru
   ```

3. **Lakukan Perubahan**  
   Tambahkan fitur atau perbaikan bug, lalu commit:
   ```bash
   git commit -m "Menambahkan fitur baru"
   ```

4. **Push ke GitHub**  
   ```bash
   git push origin fitur/fitur-baru
   ```

5. **Buat Pull Request**  
   Buka GitHub dan buat pull request dari branch Anda ke repositori utama.

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE). Anda bebas menggunakan, memodifikasi, dan mendistribusikan kode ini sesuai dengan ketentuan lisensi.

---

## 👨‍💻 Pengembang

- **Irham Najib Azimul Qowi**  
  GitHub: [Irham-Najib-Azimul-Qowi](https://github.com/Irham-Najib-Azimul-Qowi)  
  Email: [irham.najib@example.com](mailto:irham.najib@example.com)

- **Tim Lintas Alam**  
  Kontribusi: Pengembangan sistem, integrasi ESP32-CAM, dan pengujian.

---

## 📬 Kontak dan Dukungan

Jika Anda memiliki pertanyaan atau membutuhkan bantuan:
- Buka [Issue](https://github.com/Irham-Najib-Azimul-Qowi/PA-RE/issues) di GitHub.
- Hubungi pengembang melalui email di atas.

Terima kasih telah menggunakan PA-RE! 🚀
