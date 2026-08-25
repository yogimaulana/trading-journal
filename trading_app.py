import streamlit as st
import sqlite3
import hashlib
import random
import smtplib
import pandas as pd
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import plotly.express as px

# 1. Konfigurasi Halaman (Harus di baris pertama perintah Streamlit)
st.set_page_config(
    page_title="Jurnal & Kalkulator Risiko Trading",
    page_icon="📈",
    layout="wide"
)

# 2. Konfigurasi Email & Secrets (Fallback aman jika secrets.toml belum diatur)
EMAIL_SENDER = st.secrets.get("EMAIL_SENDER", "azumimaulana36@gmail.com")
EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "app_password_gmail_anda")

# ================= DATABASE SETUP =================
def init_db():
    conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Tabel User
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    
    # Tabel Histori Password Lama (untuk mencegah password reuse)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabel Trade / Jurnal
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            date TEXT,
            pair TEXT,
            type TEXT,
            lot REAL,
            entry REAL,
            sl REAL,
            tp REAL,
            pnl REAL,
            status TEXT,
            strategy TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Fungsi Hash Password
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password(password, hashed_password):
    return make_hash(password) == hashed_password

# ================= FUNGSI AUTH & USER =================
def get_user(username):
    conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    data = cursor.fetchone()
    conn.close()
    return data

def get_user_by_email(email):
    conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    data = cursor.fetchone()
    conn.close()
    return data

def add_user(username, email, password):
    conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
    cursor = conn.cursor()
    hashed_pw = make_hash(password)
    try:
        cursor.execute("INSERT INTO users(username, email, password) VALUES (?, ?, ?)", (username, email, hashed_pw))
        cursor.execute("INSERT INTO password_history(username, password_hash) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def check_password_reuse(username, new_password):
    """Mengecek apakah password baru sudah pernah digunakan sebelumnya (mencegah reuse)."""
    conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM password_history WHERE username = ?", (username,))
    history = cursor.fetchall()
    conn.close()
    
    new_hash = make_hash(new_password)
    for row in history:
        if row[0] == new_hash:
            return True # Berarti password pernah dipakai
    return False

def update_password(username, new_password):
    conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
    cursor = conn.cursor()
    hashed_pw = make_hash(new_password)
    
    # Update password utama
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_pw, username))
    # Simpan ke histori password
    cursor.execute("INSERT INTO password_history(username, password_hash) VALUES (?, ?)", (username, hashed_pw))
    conn.commit()
    conn.close()

# ================= FUNGSI EMAIL OTP =================
def send_email_otp(receiver_email, code):
    if not EMAIL_SENDER or EMAIL_SENDER == "azumimaulana36@gmail.com" and EMAIL_PASSWORD == "app_password_gmail_anda":
        return False, "Konfigurasi App Password Gmail belum diatur di secrets!"
    try:
        msg = MIMEMultipart()
        sender_name = "Lensjourneyy Trading"
        msg["From"] = formataddr((str(Header(sender_name, "utf-8")), EMAIL_SENDER))
        msg["To"] = receiver_email
        msg["Subject"] = "Kode OTP Pemulihan Password Jurnal Trading"

        body = f"Halo,\n\nBerikut adalah kode verifikasi OTP Anda: {code}\nKode ini berlaku untuk proses reset password akun Anda.\n\nSalam,\nLensjourneyy Team"
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, receiver_email, msg.as_string())
        server.quit()
        return True, "Email OTP berhasil dikirim!"
    except Exception as e:
        return False, f"Gagal mengirim email: {str(e)}"

# ================= MANAJEMEN SESSION STATE =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login" # Pilihan: Login, Register, Forgot

# ================= HALAMAN AUTENTIKASI =================
if not st.session_state.logged_in:
    st.sidebar.title("🔐 Akses Akun")
    choice = st.sidebar.radio("Navigasi", ["Login", "Register", "Lupa Password"])
    
    if choice == "Login":
        st.subheader("Login ke Jurnal Trading")
        uname = st.text_input("Username")
        upass = st.text_input("Password", type="password")
        
        if st.button("Masuk"):
            user = get_user(uname)
            if user and check_password(upass, user[3]):
                st.session_state.logged_in = True
                st.session_state.username = uname
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Username atau Password salah!")
                
    elif choice == "Register":
        st.subheader("Daftar Akun Baru")
        new_user = st.text_input("Username Baru")
        new_email = st.text_input("Email Aktif")
        new_pass = st.text_input("Password", type="password")
        confirm_pass = st.text_input("Konfirmasi Password", type="password")
        
        if st.button("Daftar"):
            if new_pass != confirm_pass:
                st.error("Password tidak cocok!")
            elif get_user(new_user):
                st.error("Username sudah terdaftar!")
            elif get_user_by_email(new_email):
                st.error("Email sudah terdaftar!")
            else:
                if add_user(new_user, new_email, new_pass):
                    st.success("Registrasi berhasil! Silakan login melalui menu samping.")
                else:
                    st.error("Terjadi kesalahan saat mendaftar.")
                    
    elif choice == "Lupa Password":
        st.subheader("Reset Password via OTP Email")
        
        if "otp_step" not in st.session_state:
            st.session_state.otp_step = 1
        
        if st.session_state.otp_step == 1:
            reset_email = st.text_input("Masukkan Email Terdaftar")
            if st.button("Kirim Kode OTP"):
                user_data = get_user_by_email(reset_email)
                if user_data:
                    otp_code = str(random.randint(100000, 999999))
                    st.session_state.temp_otp = otp_code
                    st.session_state.temp_email = reset_email
                    st.session_state.temp_username = user_data[1]
                    
                    success, msg = send_email_otp(reset_email, otp_code)
                    if success:
                        st.success(msg)
                        st.session_state.otp_step = 2
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Email tidak ditemukan di database.")
                    
        elif st.session_state.otp_step == 2:
            st.info(f"Kode OTP telah dikirim ke: {st.session_state.temp_email}")
            entered_otp = st.text_input("Masukkan 6 Digit Kode OTP", max_chars=6)
            
            if st.button("Verifikasi OTP"):
                if entered_otp == st.session_state.temp_otp:
                    st.success("OTP Valid! Silakan buat password baru.")
                    st.session_state.otp_step = 3
                    st.rerun()
                else:
                    st.error("Kode OTP salah.")
                    
        elif st.session_state.otp_step == 3:
            new_p1 = st.text_input("Password Baru", type="password")
            new_p2 = st.text_input("Konfirmasi Password Baru", type="password")
            
            if st.button("Simpan Password Baru"):
                if new_p1 != new_p2:
                    st.error("Password baru tidak cocok!")
                elif check_password_reuse(st.session_state.temp_username, new_p1):
                    st.error("Password ini pernah digunakan sebelumnya. Gunakan password yang belum pernah dipakai!")
                else:
                    update_password(st.session_state.temp_username, new_p1)
                    st.success("Password berhasil diubah! Silakan login kembali.")
                    # Reset sesi lupa password
                    del st.session_state.otp_step
                    del st.session_state.temp_otp
                    del st.session_state.temp_email
                    del st.session_state.temp_username

# ================= HALAMAN UTAMA APLIKASI (SETELAH LOGIN) =================
else:
    st.sidebar.title(f"👤 Halo, {st.session_state.username}")
    menu = st.sidebar.selectbox("Menu Utama", ["Dashboard & Analisis", "Catat Trade Baru", "Kalkulator Risiko", "Kelola Data Trade"])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # Koneksi untuk Ambil Data Trade User
    conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
    df_trades = pd.read_sql("SELECT * FROM trades WHERE username = ?", conn, params=(st.session_state.username,))
    conn.close()

    if menu == "Dashboard & Analisis":
        st.title("📈 Dashboard Performa Trading")
        
        if df_trades.empty:
            st.info("Belum ada data trade yang dicatat. Silakan tambah data melalui menu 'Catat Trade Baru'.")
        else:
            total_trades = len(df_trades)
            total_pnl = df_trades["pnl"].sum()
            win_trades = len(df_trades[df_trades["pnl"] > 0])
            win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Trades", total_trades)
            col2.metric("Total Net PnL ($)", f"${total_pnl:.2f}")
            col3.metric("Win Rate", f"{win_rate:.1f}%")
            
            st.divider()
            
            # Grafik Equity / PnL Cumulative
            df_trades['date'] = pd.to_datetime(df_trades['date'])
            df_trades = df_trades.sort_values('date')
            df_trades['Cumulative_PnL'] = df_trades['pnl'].cumsum()
            
            fig = px.line(df_trades, x='date', y='Cumulative_PnL', title="Kurva Pertumbuhan Akun (Equity Curve)", markers=True)
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "Catat Trade Baru":
        st.title("📝 Catat Trade Harian")
        
        with st.form("trade_form"):
            col1, col2 = st.columns(2)
            with col1:
                t_date = st.date_input("Tanggal Trade", value=date.today())
                t_pair = st.text_input("Pair / Instrumen (Contoh: XAUUSD, EURUSD)").upper()
                t_type = st.selectbox("Tipe Posisi", ["BUY", "SELL"])
                t_lot = st.number_input("Ukuran Lot", min_value=0.01, step=0.01, value=0.10)
            with col2:
                t_entry = st.number_input("Harga Entry", format="%.5f")
                t_sl = st.number_input("Stop Loss (SL)", format="%.5f")
                t_tp = st.number_input("Take Profit (TP)", format="%.5f")
                t_pnl = st.number_input("Profit/Loss (PnL dalam $)", step=0.01)
                
            t_strategy = st.selectbox("Strategi / Konsep", ["Smart Money Concepts (SMC)", "Price Action", "Breakout", "Grid / DCA"])
            t_notes = st.text_area("Catatan Psikologi / Alasan Entry")
            
            submit_trade = st.form_submit_button("Simpan Trade")
            
            if submit_trade:
                status = "WIN" if t_pnl > 0 else "LOSS" if t_pnl < 0 else "BEP"
                conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trades (username, date, pair, type, lot, entry, sl, tp, pnl, status, strategy, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (st.session_state.username, str(t_date), t_pair, t_type, t_lot, t_entry, t_sl, t_tp, t_pnl, status, t_strategy, t_notes))
                conn.commit()
                conn.close()
                st.success("Trade berhasil disimpan ke jurnal!")

    elif menu == "Kalkulator Risiko":
        st.title("🧮 Kalkulator Risiko & Posisi Lot")
        
        col1, col2 = st.columns(2)
        with col1:
            account_balance = st.number_input("Saldo Akun Saat Ini ($)", min_value=10.0, value=1000.0, step=50.0)
            risk_pct = st.slider("Risiko per Trade (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
        with col2:
            entry_price = st.number_input("Harga Entry Target", value=2000.0, step=0.1)
            sl_price = st.number_input("Harga Stop Loss (SL)", value=1990.0, step=0.1)
            pip_value_per_lot = st.number_input("Nilai Kontrak / Pip per Lot Standar", value=10.0)
            
        if st.button("Hitung Ukuran Posisi"):
            risk_amount = account_balance * (risk_pct / 100.0)
            distance_sl = abs(entry_price - sl_price)
            
            if distance_sl > 0:
                recommended_lot = risk_amount / (distance_sl * pip_value_per_lot)
                st.success(f"**Dana yang di Risiko (Risk Amount):** ${risk_amount:.2f}")
                st.info(f"**Ukuran Lot yang Disarankan:** {recommended_lot:.2f} Lot")
            else:
                st.warning("Jarak Entry dan Stop Loss tidak boleh 0!")

    elif menu == "Kelola Data Trade":
        st.title("📊 Riwayat & Manajemen Jurnal Trade")
        
        if df_trades.empty:
            st.info("Belum ada data riwayat trade.")
        else:
            st.dataframe(df_trades, use_container_width=True)
            
            trade_ids = df_trades["id"].tolist()
            selected_id = st.selectbox("Pilih ID Trade yang ingin dihapus", trade_ids)
            
            if st.button("Hapus Trade Terpilih"):
                conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM trades WHERE id = ? AND username = ?", (selected_id, st.session_state.username))
                conn.commit()
                conn.close()
                st.success(f"Trade dengan ID {selected_id} berhasil dihapus.")
                st.rerun()
