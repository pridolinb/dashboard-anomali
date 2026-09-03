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
st.markdown("<p style='text-align: center; font-size: 18px; color: #555;'>Pilih anomali pada menu dropdown di bawah untuk melihat grafik progress penyelesaiannya.</p>", unsafe_allow_html=True)
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
}

@st.cache_data
def load_data(sheet_name):
    df = pd.read_excel('monitoring pengerjaan anomali.xlsx', sheet_name=sheet_name, header=1)
    return df

@st.cache_data
def load_all_data(sheet_names_list):
    all_dfs = []
    for sheet in sheet_names_list:
        df = pd.read_excel('monitoring pengerjaan anomali.xlsx', sheet_name=sheet, header=1)
        if 'jumlah_baris_anomali' in df.columns and 'jumlah_sudah' in df.columns and 'kab' in df.columns:
            all_dfs.append(df[['kab', 'jumlah_baris_anomali', 'jumlah_sudah']])
    
    if all_dfs:
        combined_df = pd.concat(all_dfs)
        summary_df = combined_df.groupby('kab', as_index=False).sum()
        summary_df['persentase_penyelesaian'] = (summary_df['jumlah_sudah'] / summary_df['jumlah_baris_anomali']) * 100
        summary_df['persentase_penyelesaian'] = summary_df['persentase_penyelesaian'].fillna(0)
        return summary_df
    return pd.DataFrame()

try:
    sheet_names = get_sheet_names()
    
    # Tambahkan opsi "Semua Anomali" di urutan pertama
    options = ["Semua Anomali"] + sheet_names
    
    # Menambahkan pilihan Anomali dengan nama yang lebih deskriptif
    selected_sheet = st.selectbox(
        "🔍 Pilih Anomali:", 
        options=options, 
        index=0,
        format_func=lambda x: "Total Anomali" if x == "Semua Anomali" else f"{x.capitalize()}: {ANOMALI_LABELS.get(x, x)}"
    )
    
    if selected_sheet == "Semua Anomali":
        df = load_all_data(sheet_names)
    else:
        df = load_data(selected_sheet)
        
    # Memastikan urutan spesifik untuk Kabupaten (berlaku untuk Diagram dan Tabel)
    if 'kab' in df.columns:
        urutan_kab = ['MAJENE', 'POLEWALI MANDAR', 'MAMASA', 'MAMUJU', 'PASANGKAYU', 'MAMUJU TENGAH']
        df['kab'] = df['kab'].astype(str).str.upper()
        df['kab'] = pd.Categorical(df['kab'], categories=urutan_kab, ordered=True)
        df = df.sort_values('kab')
    
    # Menampilkan metrik utama
    if 'jumlah_baris_anomali' in df.columns and 'jumlah_sudah' in df.columns:
        total_anomali = df['jumlah_baris_anomali'].sum()
        total_selesai = df['jumlah_sudah'].sum()
        sisa_pekerjaan = total_anomali - total_selesai
        persentase_total = (total_selesai / total_anomali * 100) if total_anomali > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔴 Total Anomali", f"{total_anomali:,}")
        col2.metric("✅ Total Selesai", f"{total_selesai:,}")
        col3.metric("⏳ Sisa Pekerjaan", f"{sisa_pekerjaan:,}")
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
                                 color='kab',
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
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
            if 'kab' in df.columns and 'jumlah_baris_anomali' in df.columns and 'jumlah_sudah' in df.columns:
                # Mengambil kolom yang relevan dan mengganti namanya agar rapi
                df_tabel = df[['kab', 'jumlah_baris_anomali', 'jumlah_sudah']].copy()
                df_tabel.columns = ['Kabupaten', 'Jumlah Anomali', 'Jumlah Selesai']
                
                # Mengatur style tabel: text rata tengah untuk semua kolom
                styler = df_tabel.style.set_properties(**{'text-align': 'center'})
                
                # Menambahkan spasi kosong agar letak tabel turun sejajar dengan garis horizontal grafik
                st.markdown("<div style='margin-top: 100px;'></div>", unsafe_allow_html=True)
                
                # Menghilangkan argumen height agar tabel menyesuaikan ukuran 6 baris secara otomatis
                st.dataframe(styler, use_container_width=True, hide_index=True)
            else:
                st.warning("Data tabel tidak tersedia.")
    else:
        st.error(f"Format kolom pada data ini tidak sesuai (butuh 'jumlah_baris_anomali' & 'jumlah_sudah').")

except Exception as e:
    st.error(f"Gagal memuat data: {e}")
