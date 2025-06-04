from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pandas as pd
import numpy as np

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Simulasi user login
users = {'admin': 'admin'}  

# Placeholder untuk ranking data (default)
ranking_data = []

def process_excel(filepath):
    """
    Memproses file Excel untuk mendapatkan data penilaian guru
    """
    try:
        df = pd.read_excel(filepath, sheet_name='Sheet1', header=None)

        # Mencari baris mulai dan akhir data alternatif
        start_row = df[df[0] == 'ALTERNATIF'].index[0] + 1
        end_row = df[df[0] == 'PEMBOBOTAN KRITERIA'].index[0] - 1

        # Mengambil data alternatif
        data = df.iloc[start_row:end_row+1, :6]
        data.columns = ['Kode', 'Nama', 'C1', 'C2', 'C3', 'C4']
        data = data.drop(columns='Kode')
        data = data.dropna()

        # Convert kolom kriteria ke numeric
        for col in ['C1', 'C2', 'C3', 'C4']:
            data[col] = pd.to_numeric(data[col], errors='coerce')

        # Hitung skor akhir (rata-rata dari semua kriteria)
        data['Skor Akhir'] = data[['C1', 'C2', 'C3', 'C4']].mean(axis=1)
        
        # Urutkan berdasarkan skor akhir
        data = data.sort_values(by='Skor Akhir', ascending=False).reset_index(drop=True)
        data['Ranking'] = data.index + 1

        return data[['Nama', 'C1', 'C2', 'C3', 'C4', 'Skor Akhir', 'Ranking']].to_dict(orient='records')
    
    except Exception as e:
        print(f"Error processing Excel: {e}")
        return []

@app.route('/')
def home():
    """
    Halaman utama - Dashboard
    """
    if 'username' in session:
        return render_template("index.html", data=ranking_data)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Halaman login
    """
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if uname in users and users[uname] == pwd:
            session['username'] = uname
            flash('Login berhasil! Selamat datang.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login gagal. Username atau password salah.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Logout user
    """
    session.pop('username', None)
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    Halaman upload file Excel
    """
    global ranking_data
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith(('.xlsx', '.xls')):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            # Proses file Excel
            ranking_data = process_excel(filepath)
            
            if ranking_data:
                flash('File berhasil diunggah dan data diproses.', 'success')
                return redirect(url_for('hasil'))
            else:
                flash('Gagal memproses file. Pastikan format file sesuai.', 'error')
        else:
            flash('Pilih file Excel yang valid (.xlsx atau .xls).', 'error')
    
    return render_template('upload.html')

@app.route('/hasil')
def hasil():
    """
    Halaman hasil penilaian
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if not ranking_data:
        flash('Belum ada data untuk ditampilkan. Silakan upload file terlebih dahulu.', 'warning')
        return redirect(url_for('upload'))
    
    # Convert data ke HTML table
    df = pd.DataFrame(ranking_data)
    table_html = df.to_html(classes='table table-striped table-hover', 
                           table_id='hasilTable',
                           index=False, 
                           escape=False,
                           border=0)
    
    return render_template('hasil.html', tables=table_html)

if __name__ == '__main__':
    # Buat folder uploads jika belum ada
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)