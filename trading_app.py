import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.express as px
from supabase import create_client, Client

# ==========================================
# 1. KONFIGURASI HALAMAN & TAMPILAN PROFESIONAL
# ==========================================
st.set_page_config(
    page_title="Lensjourneyy · Professional Trading Journal & Risk MTRX",
    page_icon="📈",
    layout="wide"
)

# ==================== KUSTOM CSS & MODERN GLASSMORPHISM THEME ====================
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    header[data-testid="stHeader"] {
        display: none !important;
    }
    .stDeployButton, footer {
        visibility: hidden !important;
    }
    [data-testid="stToolbar"] {
        display: none !important;
    }
    .trading-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(0, 173, 181, 0.2);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(4px);
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1rem;
        min-height: 44px;
        background: linear-gradient(135deg, #00ADB5 0%, #007E85 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 14px rgba(0, 173, 181, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #00c4ce 0%, #00939c 100%);
        box-shadow: 0 6px 20px rgba(0, 173, 181, 0.5);
        border: none;
        color: white;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
    }
    .hero-container {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        border: 1px solid rgba(0, 173, 181, 0.3);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .feature-badge {
        background-color: rgba(0, 173, 181, 0.15);
        color: #00ADB5;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin: 4px;
        border: 1px solid rgba(0, 173, 181, 0.4);
    }
    [data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.8);
        border: 1px solid #374151;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
        font-weight: 500;
    }
    [data-testid="stMetricValue"] {
        color: #00ADB5 !important;
        font-weight: 700;
    }
    .footer-watermark {
        position: fixed;
        bottom: 8px;
        left: 12px;
        font-size: 11px;
        color: #6c757d;
        z-index: 999;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #374151;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== PENGATURAN MODE TAMPILAN ====================
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "📱 Mode Khusus Ponsel (Mobile)"

if st.session_state.view_mode == "📱 Mode Khusus Ponsel (Mobile)":
    st.markdown("""
        <style>
        .block-container {
            padding-top: 0.8rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            padding-bottom: 3.5rem !important;
        }
        h1 { font-size: 1.3rem !important; line-height: 1.3 !important; }
        h2 { font-size: 1.15rem !important; }
        h3 { font-size: 1.05rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.15rem !important; }
        [data-testid="column"] {
            width: 100% !important;
            flex: 100% !important;
            min-width: 100% !important;
            margin-bottom: 0.5rem;
        }
        input, select, textarea {
            font-size: 16px !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ==================== KONFIGURASI EMAIL (SMTP) ====================
try:
    EMAIL_SENDER = st.secrets["email"]["sender"]
    EMAIL_PASSWORD = st.secrets["email"]["password"]
except Exception:
    EMAIL_SENDER = "azumimaulana36@gmail.com"
    EMAIL_PASSWORD = "kfud dalb ztal kolp"

# ==================== KONEKSI SUPABASE ====================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

# ==================== FUNGSI DATABASE SUPABASE ====================
def send_email_otp(receiver_email, code):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Lensjourneyy Support <{EMAIL_SENDER}>"
        msg['To'] = receiver_email
        msg['Subject'] = "Kode Verifikasi Keamanan Jurnal Trading"
        body = f"Halo,\n\nBerikut adalah kode verifikasi Anda: {code}\nBerlaku selama 10 menit.\n\nSalam,\nLensjourneyy Support"
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, receiver_email, msg.as_string())
        server.quit()
        return True, "Kode verifikasi berhasil dikirim!"
    except Exception as e:
        return False, f"Gagal mengirim email: {str(e)}"

def check_user(username, password):
    try:
        response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
        return len(response.data) > 0
    except Exception:
        return False

def is_same_as_old_password(username, new_password):
    try:
        response = supabase.table("users").select("password").eq("username", username).execute()
        if response.data:
            return response.data[0]["password"] == new_password
        return False
    except Exception:
        return False

def add_user(username, email, password):
    try:
        check_u = supabase.table("users").select("*").eq("username", username).execute()
        if len(check_u.data) > 0:
            return False, "Username sudah terdaftar. Silakan gunakan username lain."
        
        supabase.table("users").insert({
            "username": username,
            "password": password
        }).execute()
        return True, "Akun berhasil didaftarkan!"
    except Exception as e:
        return False, f"Gagal mendaftarkan akun: {str(e)}"

def load_trades(username):
    try:
        response = supabase.table("trades").select("*").eq("username", username).execute()
        data = response.data
        if not data:
            return pd.DataFrame(columns=["id", "Tanggal", "Pair", "Tipe", "Lot", "Entry", "SL", "Exit", "P/L ($)", "Strategi", "Emosi / Catatan", "screenshot_name"])
        
        df = pd.DataFrame(data)
        rename_map = {
            "id": "id",
            "tanggal": "Tanggal",
            "pair": "Pair",
            "tipe": "Tipe",
            "lot": "Lot",
            "entry": "Entry",
            "sl": "SL",
            "exit": "Exit",
            "pl": "P/L ($)",
            "strategi": "Strategi",
            "emosi": "Emosi / Catatan",
            "screenshot_name": "screenshot_name"
        }
        df = df.rename(columns=rename_map)
        return df
    except Exception:
        return pd.DataFrame()

def save_trade(username, row_data, file_name, file_bytes):
    try:
        import base64
        b64_encoded = base64.b64encode(file_bytes).decode('utf-8') if file_bytes else None

        payload = {
            "username": username,
            "tanggal": str(row_data["Tanggal"]),
            "pair": row_data["Pair"],
            "tipe": row_data["Tipe"],
            "lot": float(row_data["Lot"]),
            "entry": float(row_data["Entry"]),
            "sl": float(row_data["SL"]),
            "exit": float(row_data["Exit"]),
            "pl": float(row_data["P/L ($)"]),
            "strategi": row_data["Strategi"],
            "emosi": row_data["Emosi / Catatan"],
            "screenshot_name": file_name,
            "screenshot_data": b64_encoded
        }
        supabase.table("trades").insert(payload).execute()
    except Exception as e:
        st.error(f"Gagal menyimpan ke cloud: {e}")

# ==================== SESSION STATE LOGIN ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'forgot_step' not in st.session_state:
    st.session_state.forgot_step = 1

# ==================== HALAMAN LANDING & AUTHENTICATION ====================
if not st.session_state.logged_in:
    # Logo Keren & Header di Halaman Login
    st.markdown("""
        <div class="hero-container">
            <div style="display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 1rem;">
                <div style="
                    background: linear-gradient(135deg, #00ADB5 0%, #005F65 100%);
                    width: 60px;
                    height: 60px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 14px;
                    font-size: 30px;
                    box-shadow: 0 0 20px rgba(0, 173, 181, 0.5);
                    border: 1px solid rgba(0, 173, 181, 0.6);
                ">📈</div>
                <div style="text-align: left;">
                    <h1 style="margin: 0; color: #f3f4f6; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.5px;">
                        Lensjourneyy <span style="color: #00ADB5; font-size: 0.95rem; border: 1px solid #00ADB5; padding: 2px 8px; border-radius: 6px; margin-left: 8px; background: rgba(0, 173, 181, 0.1);">PRO</span>
                    </h1>
                    <p style="margin: 0; color: #9CA3AF; font-size: 1.05rem;">Professional Trading Journal & Risk Matrix</p>
                </div>
            </div>
            <div style="margin-top: 1.5rem;">
                <span class="feature-badge">🛡️ Kalkulator Anti-MC</span>
                <span class="feature-badge">📊 Equity Curve Real-Time</span>
                <span class="feature-badge">📸 Galeri Screenshot Chart</span>
                <span class="feature-badge">🔒 Enkripsi Data Privat (Cloud)</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_empty1, col_center, col_empty2 = st.columns([0.05, 1, 0.05])
    
    with col_center:
        st.markdown("<p style='text-align: center; font-weight: bold; margin-bottom: 5px; font-size: 0.95rem; color: #00ADB5;'>📱 Pilih Mode Tampilan Layar:</p>", unsafe_allow_html=True)
        
        selected_mode = st.radio(
            "Pilih Mode Layar",
            ["📱 Mode Khusus Ponsel (Mobile)", "🖥️ Mode Desktop (Lebar)"],
            index=0 if st.session_state.view_mode == "📱 Mode Khusus Ponsel (Mobile)" else 1,
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if selected_mode != st.session_state.view_mode:
            st.session_state.view_mode = selected_mode
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Masuk Akun", "📝 Daftar Baru", "🔄 Pemulihan Sandi"])
        
        with auth_tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            l_user = st.text_input("Username", key="l_user", placeholder="Masukkan username...")
            l_pass = st.text_input("Password", type="password", key="l_pass", placeholder="Masukkan password...")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Masuk ke Workspace", type="primary"):
                if check_user(l_user, l_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = l_user
                    st.success(f"Berhasil masuk! Selamat datang, {l_user}.")
                    st.rerun()
                else:
                    st.error("⚠️ Username atau password salah.")
                    
        with auth_tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            r_user = st.text_input("Username Baru", key="r_user", placeholder="Pilih username unik...")
            r_email = st.text_input("Email Kontak (Opsional)", key="r_email", placeholder="nama@email.com")
            r_pass = st.text_input("Password Baru", type="password", key="r_pass", placeholder="Buat password...")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✨ Buat Akun Gratis Sekarang"):
                if r_user.strip() == "" or r_pass.strip() == "":
                    st.warning("⚠️ Username dan Password wajib diisi.")
                else:
                    success, msg = add_user(r_user, r_email, r_pass)
                    if success:
                        st.success(f"🎉 {msg} Silakan pindah ke tab 'Masuk Akun'.")
                    else:
                        st.error(f"⚠️ {msg}")

        with auth_tab3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Pemulihan Password")
            f_user = st.text_input("Username Akun Anda", key="f_user")
            f_email = st.text_input("Email Tujuan Pengiriman OTP", key="f_email")
            
            if st.button("📤 Kirim Kode OTP"):
                if f_user.strip() == "" or f_email.strip() == "":
                    st.warning("⚠️ Masukkan username dan email tujuan.")
                else:
                    otp_code = str(random.randint(100000, 999999))
                    expiry = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
                    try:
                        supabase.table("users").update({
                            "reset_code": otp_code,
                            "code_expiry": expiry
                        }).eq("username", f_user).execute()
                    except Exception:
                        pass
                    
                    sent_ok, sent_msg = send_email_otp(f_email, otp_code)
                    if sent_ok:
                        st.success("✅ Kode verifikasi terkirim ke email!")
                        st.session_state.forgot_step = 2
                    else:
                        st.warning(f"⚠️ {sent_msg} (Simulasi OTP Anda: **{otp_code}**)")
                        st.session_state.forgot_step = 2

            if st.session_state.forgot_step == 2:
                st.markdown("---")
                entered_otp = st.text_input("Masukkan Kode OTP 6-Digit", key="ent_otp")
                new_p1 = st.text_input("Password Baru", type="password", key="np1")
                new_p2 = st.text_input("Konfirmasi Password Baru", type="password", key="np2")
                
                if st.button("🔒 Konfirmasi Ganti Password"):
                    try:
                        row_res = supabase.table("users").select("reset_code", "code_expiry").eq("username", f_user).execute()
                        if row_res.data:
                            row = row_res.data[0]
                            if row.get("reset_code") == entered_otp:
                                if new_p1 == new_p2 and len(new_p1) > 0:
                                    if is_same_as_old_password(f_user, new_p1):
                                        st.error("⚠️ Password baru tidak boleh sama dengan password lama!")
                                    else:
                                        supabase.table("users").update({
                                            "password": new_p1,
                                            "reset_code": None,
                                            "code_expiry": None
                                        }).eq("username", f_user).execute()
                                        st.success("🎉 Password berhasil diubah! Silakan login.")
                                        st.session_state.forgot_step = 1
                                else:
                                    st.error("⚠️ Konfirmasi password tidak cocok.")
                            else:
                                st.error("⚠️ Kode OTP salah.")
                        else:
                            st.error("⚠️ User tidak ditemukan.")
                    except Exception as e:
                        st.error(f"Gagal memperbarui password: {e}")

    st.markdown('<div class="footer-watermark">⚡ Powered by Lensjourneyy · Terminal Mode</div>', unsafe_allow_html=True)

# ==================== APLIKASI UTAMA SETELAH LOGIN ====================
else:
    # Header mini dengan Logo di dalam workspace utama
    st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 5px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="
                    background: linear-gradient(135deg, #00ADB5 0%, #005F65 100%);
                    width: 40px;
                    height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 10px;
                    font-size: 20px;
                    box-shadow: 0 0 12px rgba(0, 173, 181, 0.4);
                ">📈</div>
                <h3 style="margin: 0; color: #f3f4f6; font-size: 1.2rem; font-weight: 800;">
                    Lensjourneyy <span style="color: #00ADB5; font-size: 0.75rem; border: 1px solid #00ADB5; padding: 1px 6px; border-radius: 4px;">PRO</span>
                </h3>
            </div>
    """, unsafe_allow_html=True)

    col_top1, col_top2 = st.columns([0.6, 0.4])
    with col_top1:
        st.markdown(f"👤 **Active Workspace:** <span style='color: #00ADB5;'>{st.session_state.username}</span>", unsafe_allow_html=True)
    with col_top2:
        if st.button("🚪 Keluar"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    st.markdown("---")
    
    menu = st.selectbox(
        "📌 Pilih Menu Navigasi:", 
        [
            "📊 Dashboard & Analitik", 
            "🧮 Kalkulator Lot & Risiko", 
            "➕ Input Jurnal & Screenshot", 
            "📋 Riwayat & Kalender", 
            "📖 Panduan & Penjelasan Sistem",
            "💬 Masukan & Feedback"
        ],
        label_visibility="visible"
    )
    
    with st.expander("⚙️ Pengaturan Tampilan & Layar"):
        sidebar_mode = st.radio(
            "Pilih Mode Tampilan:",
            ["📱 Mode Khusus Ponsel (Mobile)", "🖥️ Mode Desktop (Lebar)"],
            index=0 if st.session_state.view_mode == "📱 Mode Khusus Ponsel (Mobile)" else 1,
            key="sb_view_mode"
        )
        if sidebar_mode != st.session_state.view_mode:
            st.session_state.view_mode = sidebar_mode
            st.rerun()

    st.markdown("---")

    df_raw = load_trades(st.session_state.username)

    if menu == "📊 Dashboard & Analitik":
        st.title("📊 Dashboard & Analitik Performa Trading")
        st.markdown("Analisis menyeluruh pertumbuhan modal, win rate per strategi, dan performa aset secara visual.")
        
        if len(df_raw) > 0:
            df = df_raw.copy()
            df["Tanggal"] = pd.to_datetime(df["Tanggal"])
            
            total_trades = len(df)
            total_net_profit = df["P/L ($)"].sum()
            winning_trades = df[df["P/L ($)"] > 0]
            losing_trades = df[df["P/L ($)"] < 0]
            
            win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
            gross_profit = winning_trades["P/L ($)"].sum()
            gross_loss = abs(losing_trades["P/L ($)"].sum())
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Net P/L Bersih", value=f"${total_net_profit:,.2f}")
            with col2:
                st.metric(label="Total Posisi", value=total_trades)
            with col3:
                st.metric(label="Win Rate", value=f"{win_rate:.1f}%")
            with col4:
                st.metric(label="Profit Factor", value=f"{profit_factor:.2f}")
                
            st.markdown("---")
            st.subheader("📈 Grafik Pertumbuhan Ekuitas (Equity Curve)")
            
            df = df.sort_values("Tanggal")
            df["Cumulative P/L"] = df["P/L ($)"].cumsum()
            
            fig = px.area(
                df, 
                x="Tanggal", 
                y="Cumulative P/L", 
                markers=True,
                labels={"Cumulative P/L": "Total Akumulasi P/L ($)", "Tanggal": "Tanggal Transaksi"}
            )
            
            fig.update_traces(
                line=dict(color="#00ADB5", width=3),
                marker=dict(size=8, color="#EEEEEE", line=dict(color="#00ADB5", width=2)),
                fill='tozeroy',
                fillcolor='rgba(0, 173, 181, 0.15)'
            )
            
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#CCCCCC", family="sans-serif"),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", zeroline=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", zeroline=False),
                margin=dict(l=20, r=20, t=30, b=20),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader("📅 Rekapitulasi & Perhitungan Otomatis PnL per Bulan")
            
            df["Bulan"] = df["Tanggal"].dt.to_period("M").astype(str)
            monthly_summary = df.groupby("Bulan").agg(
                Total_Trade=("P/L ($)", "count"),
                Total_PnL=("P/L ($)", "sum"),
                Win_Trade=("P/L ($)", lambda x: (x > 0).sum()),
                Loss_Trade=("P/L ($)", lambda x: (x < 0).sum())
            ).reset_index()

            monthly_summary["Win Rate (%)"] = (monthly_summary["Win_Trade"] / monthly_summary["Total_Trade"] * 100).round(1)
            monthly_summary.columns = ["Bulan", "Jumlah Trade", "Net P/L Bulan ($)", "Trade Profit", "Trade Loss", "Win Rate (%)"]

            st.dataframe(monthly_summary, use_container_width=True)

            fig_monthly = px.bar(
                monthly_summary,
                x="Bulan",
                y="Net P/L Bulan ($)",
                text="Net P/L Bulan ($)",
                title="<b>Perbandingan Net P/L Bulanan</b>",
                labels={"Net P/L Bulan ($)": "Net P/L ($)", "Bulan": "Bulan Transaksi"}
            )
            fig_monthly.update_traces(marker_color="#00ADB5", texttemplate='$%{text:,.2f}', textposition='outside')
            fig_monthly.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#CCCCCC", family="sans-serif"),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
            
            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("📊 Performa Berdasarkan Pair")
                pair_summary = df.groupby("Pair")["P/L ($)"].sum().reset_index()
                st.dataframe(pair_summary, use_container_width=True)
            with col_b:
                st.subheader("🎯 Performa Berdasarkan Strategi")
                strat_summary = df.groupby("Strategi")["P/L ($)"].sum().reset_index()
                st.dataframe(strat_summary, use_container_width=True)
        else:
            st.info("Belum ada data trading yang dicatat. Silakan mulai mencatat melalui menu **Input Jurnal & Screenshot**.")

    elif menu == "🧮 Kalkulator Lot & Risiko":
        st.title("🧮 Kalkulator Posisi & Ukuran Lot (Position Sizing)")
        st.markdown("Alat bantu manajemen risiko profesional untuk menghitung ukuran Lot ideal agar modal akun tetap aman.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            acc_balance = st.number_input("Total Modal Akun ($)", value=1000.0, step=100.0)
            risk_pct = st.number_input("Risiko Maksimal (%)", value=1.0, step=0.1)
        with c2:
            calc_pair = st.selectbox("Pair / Aset", ["XAUUSD (Gold)", "BTCUSD (Bitcoin)", "EURUSD", "GBPUSD", "USDJPY"])
            calc_sl_pips = st.number_input("Jarak Stop Loss (dalam Pips / Points)", value=20.0, step=1.0)
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            allowed_risk_usd = acc_balance * (risk_pct / 100.0)
            ideal_lot = allowed_risk_usd / (calc_sl_pips * 10)
            
            st.metric(label="Batas Risiko Dana ($)", value=f"${allowed_risk_usd:,.2f}")
            st.success(f"📌 **Rekomendasi Lot Ideal:** `{max(0.01, round(ideal_lot, 2))}` Lot")

    elif menu == "➕ Input Jurnal & Screenshot":
        st.title("➕ Input Jurnal Trading & Unggah Screenshot")
        st.markdown("Catat transaksi harian Anda lengkap dengan parameter risiko, evaluasi psikologi, serta lampiran gambar bukti setup chart.")
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            t_date = st.date_input("Tanggal Transaksi", datetime.today())
            t_pair = st.selectbox("Pair / Aset", ["XAUUSD (Gold)", "BTCUSD (Bitcoin)", "EURUSD", "GBPUSD", "USDJPY"])
            t_type = st.selectbox("Tipe Order", ["Buy", "Sell"])
        with col2:
            t_lot = st.number_input("Lot / Size", min_value=0.01, value=0.01, step=0.01)
            t_entry = st.number_input("Harga Masuk (Entry)", value=4500.00, step=0.1, format="%.2f")
            t_sl = st.number_input("Harga Stop Loss (SL)", value=4480.00, step=0.1, format="%.2f")
        with col3:
            t_exit = st.number_input("Harga Keluar Aktual (Exit)", value=4530.00, step=0.1, format="%.2f")
            t_strat = st.text_input("Strategi / Setup", "SMC / Price Action")
            t_note = st.selectbox("Evaluasi Emosi / Kondisi", [
                "Disiplin & Sesuai Plan", 
                "FOMO / Masuk Tergesa-gesa", 
                "Cut Loss Terlambat", 
                "Revenge Trading"
            ])
            
        uploaded_file = st.file_uploader("📸 Unggah Screenshot Chart (Opsional - Format PNG/JPG)", type=["png", "jpg", "jpeg"])
        file_name_val = None
        file_bytes_val = None
        if uploaded_file is not None:
            file_name_val = uploaded_file.name
            file_bytes_val = uploaded_file.read()

        if t_type == "Buy":
            sl_diff = t_entry - t_sl
            price_diff = t_exit - t_entry
        else:
            sl_diff = t_sl - t_entry
            price_diff = t_entry - t_exit

        risk_amount = sl_diff * t_lot * 100
        calculated_pl = price_diff * t_lot * 100

        st.markdown("---")
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.warning(f"🛡️ **Potensi Risiko (Stop Loss):** -${abs(risk_amount):,.2f}")
        with info_col2:
            if calculated_pl > 0:
                st.success(f"💡 **Hasil Aktual (Exit):** +${calculated_pl:,.2f} (PROFIT ✅)")
            else:
                st.error(f"💡 **Hasil Aktual (Exit):** -${abs(calculated_pl):,.2f} (LOSS ❌)")
        st.markdown("---")
            
        if st.button("💾 Simpan Jurnal & Screenshot ke Database", type="primary"):
            clean_pair = t_pair.split(" ")[0]
            new_row = {
                "Tanggal": str(t_date), "Pair": clean_pair, "Tipe": t_type, "Lot": t_lot,
                "Entry": t_entry, "SL": t_sl, "Exit": t_exit, "P/L ($)": round(calculated_pl, 2),
                "Strategi": t_strat, "Emosi / Catatan": t_note
            }
            save_trade(st.session_state.username, new_row, file_name_val, file_bytes_val)
            st.success("🎉 Data jurnal dan screenshot berhasil disimpan secara aman ke Cloud Database!")

    elif menu == "📋 Riwayat & Kalender":
        st.title("📋 Riwayat Lengkap & Galeri Jurnal Trading")
        st.markdown("Daftar seluruh transaksi yang pernah Anda catat, lengkap dengan opsi unduh data dan galeri gambar chart.")
        
        if len(df_raw) > 0:
            display_df = df_raw.drop(columns=["id", "screenshot_name", "screenshot_data"], errors="ignore")
            st.dataframe(display_df, use_container_width=True)
            
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Jurnal ke Format CSV",
                data=csv,
                file_name=f'jurnal_trading_{st.session_state.username}.csv',
                mime='text/csv',
            )
            
            st.markdown("---")
            st.subheader("🖼️ Galeri Screenshot Chart Transaksi")
            try:
                img_res = supabase.table("trades").select("tanggal, pair, pl, screenshot_name, screenshot_data").eq("username", st.session_state.username).not_.is_("screenshot_data", "null").execute()
                img_rows = img_res.data
            except Exception:
                img_rows = []
            
            if img_rows:
                import base64
                for row in img_rows:
                    dt = row.get("tanggal")
                    pr = row.get("pair")
                    pl_val = row.get("pl")
                    s_name = row.get("screenshot_name")
                    s_data_b64 = row.get("screenshot_data")
                    
                    if s_data_b64:
                        img_bytes = base64.b64decode(s_data_b64)
                        with st.expander(f"📁 Tanggal: {dt} | Pair: {pr} | P/L: ${pl_val} | File: {s_name}"):
                            st.image(img_bytes, caption=s_name, use_container_width=True)
            else:
                st.info("Belum ada screenshot chart yang diunggah pada riwayat transaksi.")
        else:
            st.info("Belum ada data riwayat trading di akun ini.")

    elif menu == "📖 Panduan & Penjelasan Sistem":
        st.title("📖 Panduan & Penjelasan Sistem Trading Journal")
        st.markdown("Pusat informasi dan dokumentasi komprehensif agar Anda dapat menguasai seluruh fungsi menu aplikasi.")
        st.markdown("---")
        
        with st.expander("📊 1. Panduan Menu: Dashboard & Analitik"):
            st.markdown("""
            * **Fungsi Utama:** Menyediakan ringkasan performa trading secara visual dan menyeluruh bagi akun Anda.
            * **Perhitungan Otomatis PnL per Bulan:** Sistem secara otomatis mengelompokkan data transaksi berdasarkan bulan (`YYYY-MM`) untuk menghitung total net PnL, jumlah trade, win/loss trade, serta tingkat win rate bulanan beserta grafik batangnya.
            * **Metrik Utama (KPI):**
                * **Net P/L Bersih ($):** Total akumulasi keuntungan bersih atau kerugian bersih dari seluruh transaksi tertutup.
                * **Total Posisi:** Jumlah total transaksi yang telah dicatat dan dieksekusi.
                * **Win Rate (%):** Tingkat akurasi persentase kemenangan berdasarkan jumlah posisi profit berbanding total trade.
                * **Profit Factor:** Perbandingan antara *Gross Profit* (total profit kotor) dibagi *Gross Loss* (total loss kotor). Nilai > 1.5 mengindikasikan performa trading yang sehat.
            * **Equity Curve (Grafik Area):** Grafik interaktif yang merekam naik-turunnya akumulasi modal akun dari waktu ke waktu berdasarkan tanggal transaksi.
            * **Performa Pair & Strategi:** Tabel ringkas yang memetakan aset atau strategi mana yang memberikan kontribusi profit terbesar.
            """)
            
        with st.expander("🧮 2. Panduan Menu: Kalkulator Lot & Risiko"):
            st.markdown("""
            * **Fungsi Utama:** Alat bantu perhitungan manajemen risiko (*Risk Management*) sebelum Anda membuka posisi di market agar terhindar dari *over-leverage*.
            * **Cara Penggunaan:**
                1. Masukkan **Total Modal Akun ($)** yang Anda miliki saat ini.
                2. Tentukan **Risiko Maksimal (%)** yang siap ditoleransi per transaksi (umumnya 1% - 2%).
                3. Pilih **Pair / Aset** yang ditransaksikan.
                4. Masukkan **Jarak Stop Loss** dalam satuan Pips atau Points.
            * **Hasil Kalkulasi:** Sistem otomatis menghitung batas risiko dalam dolar ($) serta merekomendasikan **Ukuran Lot Ideal** yang aman untuk dieksekusi.
            """)
            
        with st.expander("➕ 3. Panduan Menu: Input Jurnal & Screenshot"):
            st.markdown("""
            * **Fungsi Utama:** Formulir pencatatan harian untuk mendokumentasikan parameter transaksi secara terstruktur—termasuk penetapan **Stop Loss (SL)** sebagai pengaman risiko utama—beserta evaluasi psikologisnya.
            * **Langkah Input Data & Skenario Terkena SL:**
                * **Tanggal & Pair:** Masukkan tanggal eksekusi dan pilih instrumen aset.
                * **Tipe Order:** Pilih apakah posisi berupa **Buy** (Long) atau **Sell** (Short).
                * **Lot, Entry, & SL:** Masukkan ukuran lot, harga masuk (*entry price*), dan level harga **Stop Loss (SL)**.
                * **Penanganan Saat Terkena SL di Market (Real-Time):** Jika posisi Anda di platform trading (seperti MT5) terkena *Stop Loss* secara *real-time* di market, buka menu ini dan masukkan harga penutupan aktual pada kolom **Harga Keluar Aktual (Exit)** (biasanya nilainya persis atau sangat dekat dengan level *Stop Loss* yang Anda pasang). 
                * **Pencatatan Kerugian:** Dengan memasukkan harga Exit tersebut, sistem akan otomatis menghitung dan menuliskan nominal kerugian bersih (berwarna merah) ke dalam database begitu Anda menekan tombol simpan, sehingga laporan kerugian Anda terekam dengan akurat di jurnal.
                * **Strategi & Emosi:** Masukkan nama strategi teknikal dan evaluasi kondisi psikologis saat trade tersebut terjadi (misalnya: *Disiplin & Sesuai Plan* atau *Cut Loss Terlambat*).
                * **Unggah Screenshot:** Lampirkan gambar bukti chart (PNG/JPG) untuk evaluasi teknikal jangka panjang.
            * **Kalkulasi Otomatis:** Sistem secara instan menampilkan estimasi risiko Stop Loss serta hasil akhir transaksi (Profit/Loss) sebelum data disimpan permanen ke database.
            """)
            
        with st.expander("📋 4. Panduan Menu: Riwayat & Kalender"):
            st.markdown("""
            * **Fungsi Utama:** Pusat arsip data transaksi masa lalu guna keperluan evaluasi berkala dan audit performa trading.
            * **Fitur & Navigasi:**
                * **Tabel Riwayat Transaksi:** Menampilkan seluruh daftar riwayat trade lengkap dalam format tabel bersih.
                * **Ekspor CSV:** Tombol unduh untuk mengunduh seluruh data jurnal ke format CSV agar dapat dibuka atau dianalisis lebih lanjut menggunakan Microsoft Excel / Google Sheets.
                * **Galeri Screenshot Chart:** Bagian ekspansi interaktif untuk meninjau ulang gambar setup chart yang pernah diunggah pada transaksi tertentu, lengkap dengan rincian tanggal, pair, dan hasil P/L-nya.
            """)

        with st.expander("🛠️ 5. Sistem Keamanan, Autentikasi, & Pengaturan Tampilan"):
            st.markdown("""
            * **Registrasi & Login Akun:** Setiap akun diamankan dengan aman untuk menjaga privasi data trading Anda di cloud.
            * **Verifikasi Email & Pemulihan Password:** Dilengkapi sistem pengiriman kode OTP via email (atau simulasi kode di layar) untuk proses reset password yang aman dan terlindungi.
            * **Validasi Password Lama:** Sistem secara otomatis mendeteksi dan menolak apabila Anda mencoba memasukkan password baru yang sama persis dengan password lama Anda.
            * **Mode Tampilan Responsif:** Anda dapat beralih antara **Mode Desktop (Lebar)** dan **Mode Kompak (HP / Mobile)** melalui pengaturan agar aplikasi tetap nyaman diakses lewat berbagai perangkat.
            """)

    elif menu == "💬 Masukan & Feedback":
        st.title("💬 Masukan & Feedback Aplikasi")
        st.markdown("Bantu kami meningkatkan kualitas aplikasi jurnal trading ini dengan mengirimkan kritik, saran, atau laporan kendala.")
        st.markdown("---")

        fb_tab1, fb_tab2 = st.tabs(["📝 Kirim Feedback", "📋 Daftar Feedback Masuk"])

        with fb_tab1:
            st.subheader("Kirim Masukan Anda")
            with st.form("form_feedback_app", clear_on_submit=True):
                pesan_fb = st.text_area(
                    "Pesan / Saran / Laporan Bug", 
                    placeholder="Tuliskan masukan atau kendala yang Anda alami di sini..."
                )
                rating_fb = st.slider(
                    "Rating Kepuasan Aplikasi", 
                    min_value=1, 
                    max_value=5, 
                    value=5,
                    help="1 = Sangat Buruk, 5 = Sangat Baik"
                )
                submitted_fb = st.form_submit_button("Kirim Feedback ke Cloud")
                
                if submitted_fb:
                    if not pesan_fb or not pesan_fb.strip():
                        st.warning("Pesan feedback tidak boleh kosong!")
                    else:
                        try:
                            data_feedback = {
                                "username": st.session_state.username,
                                "pesan": pesan_fb.strip(),
                                "rating": rating_fb
                            }
                            supabase.table("feedback").insert(data_feedback).execute()
                            st.success("🎉 Terima kasih! Feedback Anda berhasil dikirim ke cloud Supabase.")
                        except Exception as e:
                            st.error(f"Gagal mengirim feedback: {e}")

        with fb_tab2:
            st.subheader("Daftar Masukan Pengguna")
            st.write("Berikut adalah rekap feedback yang telah masuk ke database cloud:")
            
            if st.button("🔄 Muat Ulang Data Feedback"):
                st.rerun()
                
            try:
                res_fb = supabase.table("feedback").select("*").order("created_at", desc=True).execute()
                feedback_list = res_fb.data
                
                if not feedback_list:
                    st.info("Belum ada feedback yang dikirimkan.")
                else:
                    for item in feedback_list:
                        with st.container():
                            u_name = item.get("username", "Anonim")
                            u_rating = item.get("rating", "-")
                            u_waktu = item.get("created_at", "")
                            u_pesan = item.get("pesan", "")
                            
                            st.markdown(f"**Pengguna:** `{u_name}` | **Rating:** {'⭐' * int(u_rating)} ({u_rating}/5)")
                            st.markdown(f"*Waktu:* `{u_waktu}`")
                            st.info(u_pesan)
                            st.markdown("---")
            except Exception as e:
                st.warning(f"Gagal memuat data feedback: {e}")

    st.markdown('<div class="footer-watermark">⚡ Powered by Lensjourneyy</div>', unsafe_allow_html=True)
