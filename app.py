from flask import Flask, render_template, request, redirect, url_for, make_response
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_NAME = 'ceklis_pamling.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS master_item (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 kategori TEXT NOT NULL,
                 nama_item TEXT NOT NULL,
                 standar TEXT
               )''')

    c.execute('''CREATE TABLE IF NOT EXISTS hasil_ceklis (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 tanggal TEXT NOT NULL,
                 petugas TEXT NOT NULL,
                 lokasi TEXT NOT NULL,
                 item_id INTEGER NOT NULL,
                 status TEXT NOT NULL,
                 catatan TEXT,
                 FOREIGN KEY(item_id) REFERENCES master_item(id)
               )''')

    # Isi data master default kalau kosong
    cek = c.execute('SELECT COUNT(*) FROM master_item').fetchone()[0]
    if cek == 0:
        data_awal = [
            ('Pintu & Akses', 'Pintu gerbang utama', 'Terkunci, engsel normal'),
            ('Pintu & Akses', 'Pintu darurat', 'Tidak terhalang, rambu jelas'),
            ('Pintu & Akses', 'Access card/Mesin absensi', 'Fungsi normal'),
            ('Penerangan', 'Lampu area parkir', 'Semua menyala >200 lux'),
            ('Penerangan', 'Lampu koridor', 'Tidak ada yang mati'),
            ('Penerangan', 'Lampu emergency', 'Menyala saat listrik padam'),
            ('CCTV & Alarm', 'Kamera CCTV lobby', 'Online, rekam, tidak blur'),
            ('CCTV & Alarm', 'Kamera CCTV parkir', 'Online, sudut pantau pas'),
            ('CCTV & Alarm', 'DVR/NVR', 'HDD normal, >14 hari rekaman'),
            ('CCTV & Alarm', 'Alarm kebakaran', 'Tombol & sirine fungsi'),
            ('APAR & Hydrant', 'APAR lantai 1', 'Tekanan hijau, belum expired'),
            ('APAR & Hydrant', 'APAR lantai 2', 'Tekanan hijau, belum expired'),
            ('APAR & Hydrant', 'Hydrant box', 'Selang + nozzle lengkap'),
            ('Pagar & Perimeter', 'Pagar keliling', 'Tidak ada bolong/rusak'),
            ('Pagar & Perimeter', 'Kawat duri', 'Terpasang rapat'),
            ('Pos Satpam', 'Buku mutasi', 'Diisi lengkap'),
            ('Pos Satpam', 'HT/Radio komunikasi', 'Baterai full, suara jelas'),
            ('Pos Satpam', 'Senter', 'Fungsi normal'),
        ]
        c.executemany('INSERT INTO master_item (kategori, nama_item, standar) VALUES (?,?,?)', data_awal)

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db()
    kategori_list = conn.execute('SELECT DISTINCT kategori FROM master_item ORDER BY kategori').fetchall()

    data_ceklis = {}
    for kat in kategori_list:
        items = conn.execute('SELECT * FROM master_item WHERE kategori =? ORDER BY id', (kat['kategori'],)).fetchall()
        data_ceklis[kat['kategori']] = items

    conn.close()
    return render_template('index.html', data_ceklis=data_ceklis, tanggal=datetime.now().strftime('%Y-%m-%d'))

@app.route('/simpan', methods=['POST'])
def simpan():
    tanggal = request.form['tanggal']
    petugas = request.form['petugas']
    lokasi = request.form['lokasi']

    conn = get_db()
    item_list = conn.execute('SELECT id FROM master_item').fetchall()

    for item in item_list:
        item_id = item['id']
        status = request.form.get(f'status_{item_id}', 'Tidak Dicek')
        catatan = request.form.get(f'catatan_{item_id}', '')

        conn.execute('''INSERT INTO hasil_ceklis (tanggal, petugas, lokasi, item_id, status, catatan)
                        VALUES (?,?,?,?,?,?)''', (tanggal, petugas, lokasi, item_id, status, catatan))

    conn.commit()
    conn.close()
    return redirect(url_for('laporan', tanggal=tanggal))

@app.route('/laporan')
def laporan():
    tanggal = request.args.get('tanggal', datetime.now().strftime('%Y-%m-%d'))
    conn = get_db()
    hasil = conn.execute('''
        SELECT h.tanggal, h.petugas, h.lokasi, m.kategori, m.nama_item, m.standar, h.status, h.catatan
        FROM hasil_ceklis h
        JOIN master_item m ON h.item_id = m.id
        WHERE h.tanggal =?
        ORDER BY m.kategori, m.id
    ''', (tanggal,)).fetchall()
    conn.close()
    return render_template('laporan.html', hasil=hasil, tanggal=tanggal)

@app.route('/tambah_item', methods=['POST'])
def tambah_item():
    conn = get_db()
    conn.execute('INSERT INTO master_item (kategori, nama_item, standar) VALUES (?,?,?)',
                 (request.form['kategori'], request.form['nama_item'], request.form['standar']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')