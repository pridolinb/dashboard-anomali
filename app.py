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

try:
    sheet_names = get_sheet_names()
    
    # Menambahkan pilihan Anomali dengan nama yang lebih deskriptif
    selected_sheet = st.selectbox(
        "🔍 Pilih Anomali:", 
        options=sheet_names, 
        index=0,
        format_func=lambda x: f"{x.capitalize()}: {ANOMALI_LABELS.get(x, x)}"
    )
    
    df = load_data(selected_sheet)
    
    # Menampilkan metrik utama
    if 'jumlah_baris_anomali' in df.columns and 'jumlah_sudah' in df.columns:
        total_anomali = df['jumlah_baris_anomali'].sum()
        total_selesai = df['jumlah_sudah'].sum()
        persentase_total = (total_selesai / total_anomali * 100) if total_anomali > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🔴 Total Baris Anomali", f"{total_anomali:,}")
        col2.metric("✅ Total Sudah Dikerjakan", f"{total_selesai:,}")
        col3.metric("🎯 Persentase Penyelesaian", f"{persentase_total:.2f}%")
        
        st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='color: #2E86C1; text-align: center;'>📈 Progress Penyelesaian per Kab (%)</h3>", unsafe_allow_html=True)
        if 'persentase_penyelesaian' in df.columns and 'kab' in df.columns:
            try:
                fig = px.bar(df, x='kab', y='persentase_penyelesaian', 
                             text='persentase_penyelesaian',
                             labels={'kab': 'Kabupaten', 'persentase_penyelesaian': 'Persentase (%)'},
                             color='kab',
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_tickangle=-45, 
                                  showlegend=False, plot_bgcolor='rgba(0,0,0,0)', height=500)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.bar_chart(df.set_index('kab')['persentase_penyelesaian'])
        else:
            st.warning("Data persentase penyelesaian tidak tersedia di sheet ini.")
    else:
        st.error(f"Format kolom pada {selected_sheet} tidak sesuai (butuh 'jumlah_baris_anomali' & 'jumlah_sudah').")

except Exception as e:
    st.error(f"Gagal memuat data: {e}")
