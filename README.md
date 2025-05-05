
# 📸 PA-RE (Presensi Absensi Real-Time)

PA-RE adalah sistem absensi berbasis web yang memanfaatkan kamera ESP32-CAM untuk menangkap gambar pengguna saat melakukan presensi. Sistem ini dirancang untuk memberikan solusi absensi yang efisien dan real-time, cocok untuk kegiatan seperti lintas alam, pelatihan, atau acara organisasi lainnya.

---

## 🚀 Fitur Utama

- **Presensi Real-Time**: Pengguna dapat melakukan absensi secara langsung melalui antarmuka web.
- **Integrasi ESP32-CAM**: Menggunakan ESP32-CAM untuk menangkap foto saat presensi, meningkatkan keakuratan dan keamanan.
- **Dashboard Admin**: Antarmuka khusus untuk admin dalam mengelola data presensi dan pengguna.
- **API Terstruktur**: Backend API yang terorganisir untuk integrasi dan pengembangan lebih lanjut.
- **Deploy Mudah**: Konfigurasi yang kompatibel dengan Vercel untuk deployment yang cepat dan efisien.

---

## 🧱 Struktur Proyek

```
PA-RE/
├── ESP32-CAM/           # Kode dan konfigurasi untuk ESP32-CAM
├── api/                 # Endpoint API untuk backend
├── docs/                # Dokumentasi proyek
├── lib/                 # Library dan utilitas pendukung
├── models/              # Definisi model data
├── public/              # Aset publik seperti gambar dan stylesheet
├── .env                 # Variabel lingkungan (jangan lupa untuk mengatur ini)
├── ESP32.PY             # Skrip Python untuk komunikasi dengan ESP32
├── SERVER.py            # Server backend utama
├── package.json         # Dependensi dan skrip Node.js
├── vercel.json          # Konfigurasi untuk deployment di Vercel
└── LICENSE              # Lisensi MIT
```

---

## ⚙️ Teknologi yang Digunakan

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **Microcontroller**: ESP32-CAM
- **Deployment**: Vercel

---

## 🛠️ Tutorial Setup Lengkap

### 1. Kloning Proyek
```bash
git clone https://github.com/Irham-Najib-Azimul-Qowi/PA-RE.git
cd PA-RE
```

### 2. Siapkan Lingkungan Backend
- Pastikan Python dan pip sudah terinstal.
- Install dependency:
```bash
pip install -r requirements.txt
```

- Buat file `.env`:
```env
SECRET_KEY=your_secret_key
DB_URI=your_database_uri
```

### 3. Jalankan Server Backend
```bash
python SERVER.py
```

Server berjalan di `http://localhost:5000`

### 4. Setup ESP32-CAM
- Upload kode dari folder `ESP32-CAM/` ke ESP32-CAM.
- Sesuaikan nama SSID, password WiFi, dan URL server API di kode sebelum di-upload.

### 5. Deploy ke Vercel (Opsional)
- Login ke Vercel dan hubungkan ke repositori GitHub Anda.
- Pastikan file `vercel.json` sudah sesuai.
- Deploy otomatis akan berjalan setelah push ke GitHub.

---

## 📷 Contoh Antarmuka

*Tambahkan tangkapan layar antarmuka sistem di sini.*

---

## 🤝 Kontribusi

1. Fork repositori ini.
2. Buat branch fitur Anda: `git checkout -b fitur/fitur-baru`
3. Commit perubahan Anda: `git commit -m 'Menambahkan fitur baru'`
4. Push ke branch Anda: `git push origin fitur/fitur-baru`
5. Buat pull request.

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).

---

## 👨‍💻 Pengembang

- **Lintas Alam** - [GitHub](https://github.com/Irham-Najib-Azimul-Qowi)

---
