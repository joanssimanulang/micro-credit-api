from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app) # Mengizinkan Appsmith mengakses API ini

# ==========================================
# KONFIGURASI BASEROW (GANTI DENGAN MILIKMU)
# ==========================================
BASEROW_TOKEN = "0CawW79CV0MCwUZFQsfjJwXZJeNaD6wt"
BASEROW_TABLE_ID = "931979" 
# Cara cari Table ID: Di Baserow, klik titik tiga di samping nama tabel "Riwayat Pengajuan", lalu akan terlihat (id: xxxxx). Masukkan angkanya saja.

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "API Micro-Credit Scoring Engine Aktif!"})

@app.route('/hitung', methods=['POST'])
def hitung_skor():
    try:
        # 1. Menangkap data dari Appsmith
        data = request.json
        nama = data.get('nama', 'Tanpa Nama')
        pendapatan = float(data.get('pendapatan', 0))
        cicilan = float(data.get('cicilan', 0))
        tanggungan = int(data.get('tanggungan', 0))
        nominal_pinjaman = float(data.get('nominal_pinjaman', 0))
        
        # Tambahan: Karena di Bab 7 ada Skor Karakter, kita buat default 80 jika tidak diinput petugas
        skor_karakter = float(data.get('skor_karakter', 80)) 

        # 2. Logika Matematika Sains Data (Kalkulasi DTI)
        # Asumsi: Nominal pinjaman dicicil selama 12 bulan
        estimasi_cicilan_baru = nominal_pinjaman / 12
        total_beban_bulanan = cicilan + estimasi_cicilan_baru

        if pendapatan > 0:
            dti_ratio = (total_beban_bulanan / pendapatan) * 100
        else:
            dti_ratio = 100 # Jika pendapatan 0, risiko maksimal

        # 3. Normalisasi Skor DTI (S_DTI)
        if dti_ratio <= 30:
            s_dti = 100
        elif dti_ratio >= 60:
            s_dti = 0
        else:
            # Interpolasi linier: makin besar DTI, makin kecil skor
            s_dti = 100 - ((dti_ratio - 30) * (100 / 30))

        # 4. Normalisasi Skor Tanggungan (S_Tanggungan)
        if tanggungan <= 1:
            s_tanggungan = 100
        elif tanggungan <= 3:
            s_tanggungan = 75
        elif tanggungan <= 5:
            s_tanggungan = 50
        else:
            s_tanggungan = 25

        # 5. Menghitung Total Score (Weighted Scoring Model Bab 7)
        total_score = (s_dti * 0.5) + (s_tanggungan * 0.2) + (skor_karakter * 0.3)
        total_score = round(total_score, 2)
        dti_ratio = round(dti_ratio, 2)

        # 6. Menentukan Keputusan (Threshold)
        if total_score >= 80:
            keputusan = "Approve"
        elif total_score >= 60:
            keputusan = "Manual Review"
        else:
            keputusan = "Reject"

        # 7. Menyimpan Data ke Baserow
        baserow_url = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ID}/?user_field_names=true"
        headers = {
            "Authorization": f"Token {BASEROW_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Pastikan nama field ini sama PERSIS huruf besar/kecilnya dengan yang kamu buat di Baserow
        payload = {
            "Nama Peminjam": nama,
            "Pendapatan Bersih": pendapatan,
            "Total Cicilan": cicilan,
            "Jumlah Tanggungan": tanggungan,
            "Nominal Pinjaman": nominal_pinjaman,
            "DTI Ratio": dti_ratio,
            "Credit Score": total_score,
            "Keputusan Akhir": keputusan,
            "Skor Karakter": skor_karakter
        }
        
        # Kirim ke Baserow
        requests.post(baserow_url, headers=headers, json=payload)

        # 8. Kembalikan hasil ke Appsmith
        return jsonify({
            "status": "Sukses",
            "dti_ratio": dti_ratio,
            "credit_score": total_score,
            "keputusan": keputusan
        })

    except Exception as e:
        return jsonify({"status": "Gagal", "error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
    

# Update dari VS Code
