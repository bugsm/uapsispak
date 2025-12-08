# Sistem Pakar Defisiensi Unsur Hara Pepaya

Aplikasi web Sistem Pakar Hybrid untuk mendiagnosa kekurangan unsur hara pada tanaman pepaya menggunakan metode Certainty Factor dan simulasi Analisis Citra.

## Fitur Utama

1.  **Diagnosa Manual (Certainty Factor)**: Pengguna memilih gejala yang terlihat, dan sistem menghitung kemungkinan defisiensi (N, P, K).
2.  **Analisis Citra (Dummy)**: Simulasi deteksi penyakit melalui upload foto daun.
3.  **Sistem Hybrid**: Mengintegrasikan hasil dari kedua metode untuk memberikan rekomendasi yang lebih akurat.
4.  **Rekomendasi Solusi**: Memberikan saran penanganan berdasarkan hasil diagnosa.
5.  **Riwayat Konsultasi**: Menyimpan log konsultasi dalam format JSON.

## Struktur Proyek

```
project_root/
  app/
    main.py              # Entry point aplikasi
    routers/             # Route handler
    services/            # Logika bisnis (CF, KB, Integration)
    ml/                  # Modul Machine Learning (Dummy)
    templates/           # File HTML (Jinja2)
    static/              # CSS, JS, Uploads
  data/
    knowledge_base.json  # Basis pengetahuan (Gejala, Aturan)
    logs.json            # Log riwayat konsultasi
```

## Cara Menjalankan

1.  Pastikan Python 3.10+ terinstall.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Jalankan server:
    ```bash
    cd app
    uvicorn main:app --reload
    ```
    Atau jalankan file `main.py` langsung.

4.  Buka browser di `http://127.0.0.1:8000`.

## Teknologi

-   **Backend**: FastAPI (Python)
-   **Frontend**: HTML, TailwindCSS, Chart.js
-   **Database**: JSON (Flat file)

## Catatan

-   Modul ML saat ini masih berupa **Dummy** (simulasi) sesuai spesifikasi proyek.
-   Data Knowledge Base dapat diedit di `data/knowledge_base.json`.
