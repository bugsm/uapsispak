# Sistem Pakar Defisiensi Unsur Hara Tomat

Aplikasi web Sistem Pakar untuk mendiagnosa kekurangan unsur hara pada tanaman tomat menggunakan metode **Certainty Factor (CF)**. Sistem ini membantu petani dan pembudidaya tomat dalam mengidentifikasi defisiensi nutrisi secara dini dan akurat.

## Fitur Utama

1. **Diagnosa Berbasis Certainty Factor**: Sistem menghitung tingkat kepastian diagnosa berdasarkan gejala yang dipilih pengguna dengan metode CF yang telah terbukti efektif.

2. **Knowledge Base Lengkap**: 
   - 32+ gejala spesifik tomat dikategorikan: Daun, Batang, Buah, Bunga, Akar
   - 6 jenis defisiensi: Nitrogen (N), Fosfor (P), Kalium (K), Kalsium (Ca), Magnesium (Mg), Boron (B)
   - Aturan CF lengkap menghubungkan gejala dengan defisiensi

3. **Rekomendasi Solusi Detail**: Setiap diagnosa dilengkapi dengan saran penanganan dan rekomendasi pemupukan yang spesifik dan praktis.

4. **Riwayat Konsultasi**: Setiap konsultasi disimpan dalam format JSON untuk tracking dan analisis.

5. **User Interface Modern**: Antarmuka yang user-friendly dengan wizard-style form untuk memudahkan input gejala.

## Struktur Proyek

```
uapsispak/
├── app/
│   ├── main.py              # Entry point aplikasi FastAPI
│   ├── routers/
│   │   └── web.py           # Route handler untuk halaman web (dengan validasi & error handling)
│   ├── services/
│   │   ├── inference_cf.py  # Logika perhitungan Certainty Factor (dengan validasi & logging)
│   │   └── knowledge_base.py # Akses data knowledge base (dengan caching & error handling)
│   ├── templates/           # Template HTML (Jinja2)
│   │   ├── base.html        # Template dasar
│   │   ├── index.html       # Halaman utama
│   │   ├── consult.html            # Form konsultasi (wizard-style)
│   │   ├── result.html             # Hasil diagnosa
│   │   ├── calculation_details.html # Detail perhitungan CF
│   │   └── about.html              # Halaman tentang
│   └── static/              # Static files (CSS)
│       └── css/
│           └── style.css    # Custom styles
├── data/
│   ├── knowledge_base.json  # Basis pengetahuan (gejala, nutrisi, aturan CF)
│   └── logs.json            # Log riwayat konsultasi
├── tests/                   # File testing
├── requirements.txt         # Dependencies Python
└── README.md               # Dokumentasi proyek
```

## Teknologi yang Digunakan

### Backend
- **FastAPI** (Python) - Web framework modern dan cepat
- **Uvicorn** - ASGI server untuk production
- **Jinja2** - Template engine untuk HTML rendering
- **Python Multipart** - Handling form data

### Frontend
- **HTML5** - Struktur halaman
- **TailwindCSS** - Utility-first CSS framework
- **Chart.js** - Visualisasi data hasil diagnosa
- **Alpine.js** - JavaScript framework untuk interaktivitas

### Penyimpanan Data
- **JSON Files** - Flat file database untuk knowledge base dan logs

## Cara Menjalankan

### Prasyarat
- Python 3.10 atau lebih tinggi
- pip (Python package manager)

### Instalasi

1. Clone atau download proyek ini

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Jalankan server:
```bash
# Dari root directory
cd app
python main.py

# Atau menggunakan uvicorn langsung
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Buka browser di `http://127.0.0.1:8000`

### Development Mode

Untuk development dengan auto-reload:
```bash
uvicorn app.main:app --reload
```

## Cara Menggunakan

1. **Akses Halaman Utama**: Buka `http://127.0.0.1:8000`

2. **Mulai Konsultasi**: Klik tombol "Mulai Konsultasi" atau akses `/consult`

3. **Isi Data**: 
   - Nama pemilik (opsional)
   - Umur tanaman (opsional)

4. **Pilih Kategori Gejala**: Pilih satu atau lebih kategori (Daun, Batang, Buah, Bunga, Akar)

5. **Identifikasi Gejala**: 
   - Sistem akan menampilkan gejala satu per satu
   - Pilih tingkat keyakinan untuk setiap gejala:
     - ❌ Tidak (0.0)
     - 🤔 Ragu (0.2)
     - 👀 Mungkin (0.6)
     - ✅ Yakin (0.8)
     - 💯 Sangat Yakin (1.0)

6. **Lihat Hasil**: Setelah selesai, sistem akan menampilkan:
   - Diagnosa utama dengan tingkat keyakinan (CF)
   - Rekomendasi penanganan
   - Grafik semua kemungkinan defisiensi
   - Link ke halaman detail perhitungan CF (step-by-step)

## Metode Certainty Factor

Sistem menggunakan metode **Certainty Factor (CF)** yang dikembangkan oleh Shortliffe & Buchanan (1975) untuk menghitung tingkat kepastian diagnosa.

### Formula Dasar
```
CF(H,E) = CF_pakar × CF_user
```

Dimana:
- `CF_pakar`: Nilai CF dari knowledge base (0.0 - 1.0) - **Ditentukan oleh pakar dan literatur**
- `CF_user`: Tingkat keyakinan user (0.0 - 1.0) - **Dari input form**

### Kombinasi Multiple Evidence
```
CF_new = CF_old + CF_new × (1 - CF_old)
```

Formula ini digunakan untuk mengkombinasikan multiple gejala yang mengarah ke defisiensi yang sama.

## Knowledge Base

Knowledge base disimpan dalam `data/knowledge_base.json` dengan struktur:

```json
{
  "symptoms": [
    {
      "code": "G01",
      "name": "Daun bagian bawah menguning (klorosis) dimulai dari ujung",
      "category": "Daun"
    }
  ],
  "nutrients": [
    {
      "code": "D01",
      "name": "Defisiensi Nitrogen (N)",
      "solusi": "Berikan pupuk nitrogen..."
    }
  ],
  "rules": [
    {
      "nutrient": "D01",
      "symptom": "G01",
      "cf": 0.85
    }
  ]
}
```

### Menambah/Mengubah Knowledge Base

1. Edit file `data/knowledge_base.json`
2. Pastikan struktur JSON valid
3. Restart aplikasi (atau clear cache jika menggunakan caching)
4. Sistem akan otomatis memvalidasi struktur saat startup

## API Endpoints

### Web Routes
- `GET /` - Halaman utama
- `GET /consult` - Form konsultasi
- `POST /consult` - Process konsultasi dan tampilkan hasil
- `GET /calculation-details` - Detail perhitungan CF secara manual
- `GET /about` - Halaman tentang sistem

### API Routes
- `GET /health` - Health check endpoint
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Error Handling

Sistem dilengkapi dengan error handling yang komprehensif:

- **Validasi Input**: Semua input divalidasi sebelum processing
- **Error Logging**: Semua error dicatat dengan detail untuk debugging
- **User-Friendly Messages**: Error messages yang mudah dipahami
- **Global Error Handlers**: Menangani semua jenis exception

## Logging

Sistem menggunakan Python logging dengan konfigurasi:
- Level: INFO (default)
- Format: Timestamp, logger name, level, message
- Logs mencakup:
  - Request/response logging
  - CF calculation details
  - Error dengan stack trace
  - Consultation logs

## Testing

File testing tersedia di folder `tests/`:
```bash
python tests/verify_expert_system.py
```

## Troubleshooting

### Knowledge Base Error
Jika terjadi error "Knowledge base tidak tersedia":
1. Pastikan file `data/knowledge_base.json` ada
2. Validasi struktur JSON
3. Check file permissions

### Port Already in Use
Jika port 8000 sudah digunakan:
```bash
uvicorn app.main:app --port 8001
```

### Static Files Not Loading
Pastikan folder `app/static/` ada dan memiliki file CSS yang diperlukan.

## Kontribusi

Proyek ini dikembangkan untuk keperluan akademik. Untuk kontribusi:
1. Fork proyek
2. Buat feature branch
3. Commit changes
4. Push ke branch
5. Buat Pull Request

## Lisensi

Proyek ini dikembangkan untuk keperluan akademik mata kuliah Sistem Pakar.

## Catatan Penting

- **Data Knowledge Base**: Dapat diedit di `data/knowledge_base.json`
- **Logs Konsultasi**: Disimpan di `data/logs.json`
- **Validasi**: Sistem otomatis memvalidasi knowledge base saat startup
- **Caching**: Knowledge base di-cache untuk performa (bisa di-clear dengan restart)

## Versi

**Version 2.0.0** - Sistem Pakar Defisiensi Unsur Hara Tomat
- Knowledge base lengkap untuk tomat
- Backend dengan validasi dan error handling detail
- Logging komprehensif
- User interface yang modern dan user-friendly

**Penting**: Sistem ini adalah **Sistem Pakar yang sesungguhnya**, bukan hanya aplikasi web biasa. Nilai CF_pakar ditentukan melalui wawancara dengan pakar, review literatur, dan validasi.

## Kontak & Support

Untuk pertanyaan atau issue, silakan buat issue di repository ini.

---

**Dikembangkan untuk Tugas Akhir Mata Kuliah Sistem Pakar 2025**

**Referensi**: Shortliffe, E. H., & Buchanan, B. G. (1975). A model of inexact reasoning in medicine. Mathematical Biosciences, 23(3-4), 351-379.


32 gejala, 6 defisensi, 37 rules cf

distribusi gejala per kategori
Daun: 14 gejala (G01, G02, G04, G08, G09, G10, G13, G14, G15, G21, G23, G24, G26, G30)
Batang: 7 gejala (G03, G06, G11, G18, G25, G27, G28)
Buah: 6 gejala (G05, G16, G19, G20, G29, G31)
Bunga: 3 gejala (G07, G17, G22)
Akar: 2 gejala (G12, G32)

rules per kategori
Daun: 15 rules
D01 (Nitrogen): G01, G02, G04 = 3 rules
D02 (Fosfor): G08, G09, G10 = 3 rules
D03 (Kalium): G13, G14, G15 = 3 rules
D04 (Kalsium): G21 = 1 rule
D05 (Magnesium): G23, G24, G01, G30 = 4 rules
D06 (Boron): G26 = 1 rule
Batang: 6 rules
D01 (Nitrogen): G03, G06 = 2 rules
D02 (Fosfor): G11, G03 = 2 rules
D05 (Magnesium): G25 = 1 rule
D06 (Boron): G27, G28, G03, G18 = 4 rules
Buah: 6 rules
D01 (Nitrogen): G05 = 1 rule
D03 (Kalium): G16, G29, G31 = 3 rules
D04 (Kalsium): G19, G20 = 2 rules
Bunga: 4 rules
D01 (Nitrogen): G07 = 1 rule
D03 (Kalium): G17 = 1 rule
D04 (Kalsium): G22 = 1 rule
D06 (Boron): G22 = 1 rule
Akar: 2 rules
D02 (Fosfor): G12, G32 = 2 rules



