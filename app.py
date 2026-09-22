import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Monitoring Anomali", page_icon="📊", layout="wide")

# Kustomisasi CSS untuk mempercantik tampilan metrik dan layout
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 2px solid #e0e0e0;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
        text-align: center;
    }
    div[data-testid="metric-container"] > div {
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# Judul Dashboard dengan warna
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>📊 Dashboard Monitoring Pengerjaan Anomali</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px; color: #555;'>Data 21 September</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

@st.cache_data
def get_sheet_names():
    xl = pd.ExcelFile('monitoring pengerjaan anomali.xlsx')
    return xl.sheet_names

# Pemetaan nama sheet (anomali 1-13) ke deskripsi lengkapnya
ANOMALI_LABELS = {
    "anomali 1": "Cek Duplikat Assignment Usaha",
    "anomali 2": "Usaha dalam BTT, Usaha Keliling, Usaha diluar BTT tapi lokasi dibongkar namun omset > 15 milyar",
    "anomali 3": "Omset > 15 milyar tapi total pekerja hanya 1 orang",
    "anomali 4": "List Usaha kategori P dan U",
    "anomali 5": "Produk atau Kegiatan \"Sawit\" tetapi NTB < 0",
    "anomali 6": "Perseroan (1.a) tapi Modal 100% Pribadi",
    "anomali 7": "Kesesuaian Umur Anggota Keluarga dengan Pendidikan",
    "anomali 8": "Kesesuaian nama usaha dan badan usaha",
    "anomali 9": "Perdagangan besar omset kecil < 50jt/tahun",
    "anomali 10": "Selisih Pendapatan Keluarga dan Pengeluaran Keluarga > 100jt",
    "anomali 11": "Usaha konstruksi dan penggalian tidak sesuai lokasi usaha",
    "anomali 12": "Keluarga memiliki lebih dari 1 ART disabilitas",
    "anomali 13": "Usaha pertanian tetapi jenis usaha bukan usaha pertanian",
    "anomali 14": "Bermitra dengan KDKMP tapi bukan kategori \"G\" & \"F\"",
}

@st.cache_data
def load_data(sheet_name):
    df = pd.read_excel('monitoring pengerjaan anomali.xlsx', sheet_name=sheet_name, header=1)
    return df

@st.cache_data
def load_all_data(sheet_names_list, include_pusat=True):
    all_dfs = []
    for sheet in sheet_names_list:
        df = pd.read_excel('monitoring pengerjaan anomali.xlsx', sheet_name=sheet, header=1)
        if 'jumlah_baris_anomali' in df.columns and 'jumlah_sudah' in df.columns and 'kab' in df.columns:
            all_dfs.append(df[['kab', 'jumlah_baris_anomali', 'jumlah_sudah']])
            
    if include_pusat:
        # Menambahkan data dari Anomali Pusat
        try:
            df_pusat = load_anomali_pusat()
            if not df_pusat.empty and 'kab' in df_pusat.columns:
                all_dfs.append(df_pusat[['kab', 'jumlah_baris_anomali', 'jumlah_sudah']])
        except Exception as e:
            pass # Abaikan jika gagal memuat anomali pusat untuk agregasi
    
    if all_dfs:
        combined_df = pd.concat(all_dfs)
        # Samakan huruf kapital agar grouping akurat (misal 'Majene' dan 'MAJENE' tergabung)
        combined_df['kab'] = combined_df['kab'].astype(str).str.upper()
        
        summary_df = combined_df.groupby('kab', as_index=False).sum()
        summary_df['persentase_penyelesaian'] = (summary_df['jumlah_sudah'] / summary_df['jumlah_baris_anomali']) * 100
        summary_df['persentase_penyelesaian'] = summary_df['persentase_penyelesaian'].fillna(0)
        return summary_df
    return pd.DataFrame()

@st.cache_data
def load_anomali_pusat():
    df = pd.read_excel('Tabel_Jumlah_Anomali_Ringkas.xlsx', header=2)
    
    # Memaksa kolom 'No' menjadi angka. Teks seperti 'Rumus:' akan berubah menjadi NaN
    df['No'] = pd.to_numeric(df['No'], errors='coerce')
    
    # Hapus baris catatan/rumus di bagian bawah excel (serta baris 'Total' yang kolom No-nya kosong/NaN)
    df = df.dropna(subset=['No'])
    
    # Mengonversi kolom ke tipe numerik dan mengganti nilai teks menjadi NaN lalu diubah jadi 0
    df['Total Anomali'] = pd.to_numeric(df['Total Anomali'], errors='coerce').fillna(0)
    df['Total Sudah Ditindaklanjuti'] = pd.to_numeric(df['Total Sudah Ditindaklanjuti'], errors='coerce').fillna(0)
    
    # Menghitung Persentase Secara Dinamis
    persen_sudah = (df['Total Sudah Ditindaklanjuti'] / df['Total Anomali'].replace({0: float('nan')})).fillna(0) * 100
    
    # Menghitung Belum Ditindaklanjuti
    belum_ditindaklanjuti = df['Total Anomali'] - df['Total Sudah Ditindaklanjuti']
    
    # Menghindari pembagian dengan nol menggunakan numpy.where atau masking pandas
    persen_belum = (belum_ditindaklanjuti / df['Total Anomali'].replace({0: float('nan')})).fillna(0) * 100
    
    df_pusat = pd.DataFrame({
        'No': df['No'].astype(int),  # Memastikan kolom No adalah angka (bukan teks)
        'kab': df['Kabupaten'],
        'jumlah_baris_anomali': df['Total Anomali'].astype(int),
        'jumlah_sudah': df['Total Sudah Ditindaklanjuti'].astype(int),
        'persentase_penyelesaian': persen_sudah,
        'persentase_belum': persen_belum
    })
    return df_pusat

try:
    sheet_names = get_sheet_names()
    
    # Tambahkan opsi "Semua Anomali", "Total Anomali Daerah", dan "Anomali Pusat" di urutan pertama
    options = ["Semua Anomali", "Total Anomali Daerah", "Anomali Pusat"] + sheet_names
    
    # Menambahkan pilihan Anomali dengan nama yang lebih deskriptif
    selected_sheet = st.selectbox(
        "🔍 Pilih Anomali:", 
        options=options, 
        index=0,
        format_func=lambda x: "Total Keseluruhan" if x == "Semua Anomali" else ("Total Anomali Daerah" if x == "Total Anomali Daerah" else ("Total Anomali Pusat" if x == "Anomali Pusat" else f"{x.capitalize()}: {ANOMALI_LABELS.get(x, x)}"))
    )
    
    if selected_sheet == "Semua Anomali":
        df = load_all_data(sheet_names, include_pusat=True)
    elif selected_sheet == "Total Anomali Daerah":
        df = load_all_data(sheet_names, include_pusat=False)
    elif selected_sheet == "Anomali Pusat":
        df = load_anomali_pusat()
    else:
        df = load_data(selected_sheet)
        
    # Memastikan urutan spesifik untuk Kabupaten (berlaku untuk Diagram dan Tabel)
    if 'kab' in df.columns:
        urutan_kab = ['MAJENE', 'POLEWALI MANDAR', 'MAMASA', 'MAMUJU', 'PASANGKAYU', 'MAMUJU TENGAH']
        df['kab'] = df['kab'].astype(str).str.upper()
        df['kab'] = pd.Categorical(df['kab'], categories=urutan_kab, ordered=True)
        df = df.dropna(subset=['kab'])
        df = df.sort_values('kab')
    
    # Menampilkan metrik utama
    if 'jumlah_baris_anomali' in df.columns and 'jumlah_sudah' in df.columns:
        total_anomali = df['jumlah_baris_anomali'].sum()
        total_selesai = df['jumlah_sudah'].sum()
        sisa_pekerjaan = total_anomali - total_selesai
        persentase_total = (total_selesai / total_anomali * 100) if total_anomali > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔴 Total Anomali", f"{int(total_anomali):,}")
        col2.metric("✅ Total Selesai", f"{int(total_selesai):,}")
        col3.metric("⏳ Sisa Pekerjaan", f"{int(sisa_pekerjaan):,}")
        col4.metric("🎯 Persentase Penyelesaian", f"{persentase_total:.2f}%")
        
        st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)
        
        # Layout 2 kolom: Kiri untuk grafik (3 bagian), Kanan untuk tabel (2 bagian)
        col_chart, col_table = st.columns([3, 2])
        
        with col_chart:
            st.markdown("<h3 style='color: #2E86C1; text-align: center;'>📈 Progres Penyelesaian per Kab (%)</h3>", unsafe_allow_html=True)
            if 'persentase_penyelesaian' in df.columns and 'kab' in df.columns:
                try:
                    fig = px.bar(df, x='kab', y='persentase_penyelesaian', 
                                 text='persentase_penyelesaian',
                                 labels={'kab': 'Kabupaten', 'persentase_penyelesaian': 'Persentase (%)'},
                                 color_discrete_sequence=['#FF9800'])
                    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_tickangle=0, 
                                      showlegend=False, plot_bgcolor='rgba(0,0,0,0)', height=500)
                    fig.update_yaxes(range=[0, 100])  # Mengunci sumbu Y dari 0 hingga 100
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.bar_chart(df.set_index('kab')['persentase_penyelesaian'])
            else:
                st.warning("Data persentase penyelesaian tidak tersedia di sheet ini.")
                
        with col_table:
            st.markdown("<h3 style='color: #2E86C1; text-align: center;'>📋 Tabel Data</h3>", unsafe_allow_html=True)
            if selected_sheet == "Anomali Pusat" and 'persentase_belum' in df.columns:
                df_tabel = df[['kab', 'jumlah_baris_anomali', 'jumlah_sudah', 'persentase_penyelesaian']].copy()
                df_tabel.columns = ['Kabupaten', 'Total Anomali', 'Total Sudah Ditindaklanjuti', 'Total Sudah Ditindaklanjuti (%)']
                
                # Format persentase
                df_tabel['Total Sudah Ditindaklanjuti (%)'] = df_tabel['Total Sudah Ditindaklanjuti (%)'].apply(lambda x: f"{x:.2f}%")
                
                st.markdown("<div style='margin-top: 100px;'></div>", unsafe_allow_html=True)
                st.dataframe(df_tabel, use_container_width=True, hide_index=True)
                
            elif 'kab' in df.columns and 'jumlah_baris_anomali' in df.columns and 'jumlah_sudah' in df.columns:
                # Mengambil kolom yang relevan dan mengganti namanya agar rapi
                df_tabel = df[['kab', 'jumlah_baris_anomali', 'jumlah_sudah']].copy()
                df_tabel.columns = ['Kabupaten', 'Jumlah Anomali', 'Jumlah Selesai']
                
                # Menambahkan spasi kosong agar letak tabel turun sejajar dengan garis horizontal grafik
                st.markdown("<div style='margin-top: 100px;'></div>", unsafe_allow_html=True)
                st.dataframe(df_tabel, use_container_width=True, hide_index=True)
            else:
                st.warning("Data tabel tidak tersedia.")
    else:
        st.error(f"Format kolom pada data ini tidak sesuai (butuh 'jumlah_baris_anomali' & 'jumlah_sudah').")
        
    # === BAGIAN KEDUA: ANALISIS DATA TAMBAHAN ===
    st.markdown("<br><hr style='border: 2px solid #ddd;'><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>📊 Cakupan dan Koherensi Data</h2>", unsafe_allow_html=True)
    
    pilihan_kedua = [
        "Jumlah Penduduk hasil SE vs Jumlah Penduduk Dukcapil",
        "Jumlah hasil SE SPPG vs Kemenkes",
        "Jumlah Perguruan Tinggi vs Data SKTNP",
        "Jumlah Pendidikan Dasar",
        "Jumlah Pendidikan Menengah Pertama",
        "Jumlah Pendidikan Menengah Atas",
        "Jumlah hasil SE Rumah Sakit vs Kemenkes",
        "Jumlah Puskesmas",
        "Jumlah Koperasi",
        "Jumlah Hotel dan Penginapan",
        "Jumlah Perusahaan Pertanian (perkebunan, perikanan, dll)",
        "Jumlah Industri Besar dan Sedang",
        "Jumlah industri Kontruksi pertambangan dan Penggalian",
        "Jumlah Jasa Keuangan (Bank)",
        "Jumlah Jasa Kesehatan (Praktek Dokter/Bidan dll)"
    ]
    
    selected_pilihan_kedua = st.selectbox(
        "🔍 Pilih Analisis Data:",
        options=pilihan_kedua,
        index=0
    )
    
    urutan_kab_2 = ['MAJENE', 'POLEWALI MANDAR', 'MAMASA', 'MAMUJU', 'PASANGKAYU', 'MAMUJU TENGAH']
    
    if selected_pilihan_kedua == "Jumlah Penduduk hasil SE vs Jumlah Penduduk Dukcapil":
        try:
            df_pop = pd.read_excel('Perbandingan Jumlah Penduduk.xlsx', header=2)
            # Ffill kabupaten to handle merged cells
            df_pop['Kabupaten'] = df_pop['Kabupaten'].ffill()
            
            # Kolom yang diperlukan untuk dijumlahkan
            cols_to_sum = ['Jumlah Penduduk Dukcapil', 'Jumlah Penduduk SE2026 Versi 2', 'Selisih\nVersi 2']
            for col in cols_to_sum:
                df_pop[col] = pd.to_numeric(df_pop[col], errors='coerce').fillna(0)
                
            df_grouped = df_pop.groupby('Kabupaten', as_index=False)[cols_to_sum].sum()
            pct = (df_grouped['Jumlah Penduduk SE2026 Versi 2'] / df_grouped['Jumlah Penduduk Dukcapil'].replace({0: float('nan')})).fillna(0) * 100
            df_grouped['persentase_penyelesaian'] = pct.clip(upper=100)
            
            df_grouped['kab'] = df_grouped['Kabupaten'].astype(str).str.upper()
            df_grouped['kab'] = pd.Categorical(df_grouped['kab'], categories=urutan_kab_2, ordered=True)
            df_grouped = df_grouped.dropna(subset=['kab'])
            df_grouped = df_grouped.sort_values('kab')
            
            df_kedua_chart = df_grouped[['kab', 'persentase_penyelesaian']].copy()
            
            df_tabel_2 = df_grouped[['kab', 'Jumlah Penduduk Dukcapil', 'Jumlah Penduduk SE2026 Versi 2', 'Selisih\nVersi 2']].copy()
            # Menghapus kata 'Versi 2' dari nama tabel
            df_tabel_2.columns = ['Kabupaten', 'Jumlah Penduduk Dukcapil', 'Jumlah Penduduk SE2026', 'Selisih']
            
            # Format integer untuk tabel
            for col in ['Jumlah Penduduk Dukcapil', 'Jumlah Penduduk SE2026', 'Selisih']:
                df_tabel_2[col] = df_tabel_2[col].astype(int)
                
        except Exception as e:
            st.error("Gagal memuat data Penduduk: " + str(e))
            df_kedua_chart = pd.DataFrame({'kab': pd.Categorical(urutan_kab_2, categories=urutan_kab_2, ordered=True), 'persentase_penyelesaian': [0.0]*6}).sort_values('kab')
            df_tabel_2 = pd.DataFrame({'Kabupaten': urutan_kab_2, 'Data Kosong': [0]*6})
            
    elif selected_pilihan_kedua in ["Jumlah hasil SE SPPG vs Kemenkes", "Jumlah Perguruan Tinggi vs Data SKTNP", "Jumlah hasil SE Rumah Sakit vs Kemenkes"]:
        try:
            if selected_pilihan_kedua == "Jumlah hasil SE SPPG vs Kemenkes":
                df_src = pd.read_excel('tabulasi SPPG, PT, dan Rumah sakit.xlsx', sheet_name='SPPG', header=0)
                col_sumber = 'Kemenkes'
            elif selected_pilihan_kedua == "Jumlah Perguruan Tinggi vs Data SKTNP":
                df_src = pd.read_excel('tabulasi SPPG, PT, dan Rumah sakit.xlsx', sheet_name='Perguruan Tinggi', header=1)
                col_sumber = 'SKTNP'
            elif selected_pilihan_kedua == "Jumlah hasil SE Rumah Sakit vs Kemenkes":
                df_src = pd.read_excel('tabulasi SPPG, PT, dan Rumah sakit.xlsx', sheet_name='Rumah sakit', header=1)
                col_sumber = 'Kemenkes'

            col_se = 'SE 2026'
            col_selisih = 'Selisih'
            tabel_headers = ['Kabupaten', f'Jumlah {col_sumber}', 'Jumlah SE 2026', 'Selisih']

            # Bersihkan spasi kosong yang tidak sengaja terketik di nama kolom Excel (seperti ' SKTNP')
            df_src.columns = df_src.columns.str.strip()
            df_src['Kabupaten'] = df_src['Kabupaten'].ffill()
            
            for col in [col_sumber, col_se, col_selisih]:
                df_src[col] = pd.to_numeric(df_src[col], errors='coerce').fillna(0)
                
            df_grouped = df_src.groupby('Kabupaten', as_index=False)[[col_sumber, col_se, col_selisih]].sum()
            pct = (df_grouped[col_se] / df_grouped[col_sumber].replace({0: float('nan')})).fillna(0) * 100
            df_grouped['persentase_penyelesaian'] = pct.clip(upper=100)
            
            # Ganti POLMAN menjadi POLEWALI MANDAR agar terbaca sistem
            df_grouped['kab'] = df_grouped['Kabupaten'].astype(str).str.upper().replace('POLMAN', 'POLEWALI MANDAR')
            df_grouped['kab'] = pd.Categorical(df_grouped['kab'], categories=urutan_kab_2, ordered=True)
            df_grouped = df_grouped.dropna(subset=['kab'])
            df_grouped = df_grouped.sort_values('kab')
            
            df_kedua_chart = df_grouped[['kab', 'persentase_penyelesaian']].copy()
            df_tabel_2 = df_grouped[['kab', col_sumber, col_se, col_selisih]].copy()
            df_tabel_2.columns = tabel_headers
            
            for col in tabel_headers[1:]:
                df_tabel_2[col] = df_tabel_2[col].astype(int)
                
        except Exception as e:
            st.error("Gagal memuat data: " + str(e))
            df_kedua_chart = pd.DataFrame({'kab': pd.Categorical(urutan_kab_2, categories=urutan_kab_2, ordered=True), 'persentase_penyelesaian': [0.0]*6}).sort_values('kab')
            df_tabel_2 = pd.DataFrame({'Kabupaten': urutan_kab_2, 'Data Kosong': [0]*6})
            
    else:
        # Data kosong statis
        df_kedua_chart = pd.DataFrame({
            'kab': pd.Categorical(urutan_kab_2, categories=urutan_kab_2, ordered=True),
            'persentase_penyelesaian': [0.0] * 6
        }).sort_values('kab')
        
        df_tabel_2 = pd.DataFrame({
            'Kabupaten': urutan_kab_2,
            'Jumlah Anomali': [0] * 6,
            'Jumlah Selesai': [0] * 6
        })
    
    col_chart_2, col_table_2 = st.columns([3, 2])
    
    with col_chart_2:
        st.markdown("<h3 style='color: #2E86C1; text-align: center;'>📈 Persentase (%)</h3>", unsafe_allow_html=True)
        try:
            fig2 = px.bar(df_kedua_chart, x='kab', y='persentase_penyelesaian', 
                         text='persentase_penyelesaian',
                         labels={'kab': 'Kabupaten', 'persentase_penyelesaian': 'Persentase (%)'},
                         color_discrete_sequence=['#FF9800'])
            fig2.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig2.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_tickangle=0, 
                              showlegend=False, plot_bgcolor='rgba(0,0,0,0)', height=500)
            
            # Ambil nilai max untuk sumbu y
            max_val = df_kedua_chart['persentase_penyelesaian'].max()
            if max_val < 100:
                fig2.update_yaxes(range=[0, 100])
            else:
                fig2.update_yaxes(range=[0, max_val + 10])
                
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.warning("Diagram tidak dapat ditampilkan.")
            
    with col_table_2:
        st.markdown("<h3 style='color: #2E86C1; text-align: center;'>📋 Tabel Data</h3>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top: 100px;'></div>", unsafe_allow_html=True)
        st.dataframe(df_tabel_2, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Gagal memuat data: {e}")
