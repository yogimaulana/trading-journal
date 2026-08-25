import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.express as px

st.set_page_config(
    page_title="Lensjourneyy · Professional Trading Journal & Risk MTRX", 
    page_icon="📈", 
    layout="wide"
)

# ==================== KONFIGURASI EMAIL PENGIRIM (SMTP) ====================
try:
    EMAIL_SENDER = st.secrets["email"]["sender"]
    EMAIL_PASSWORD = st.secrets["email"]["password"]
except Exception:
    EMAIL_SENDER = st.secrets.get("EMAIL_SENDER", "azumimaulana36@gmail.com")
    EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "kfud dalb ztal kolp")

# ==================== PENGATURAN MODE TAMPILAN ====================
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "📱 Mode Khusus Ponsel (Mobile)"

# ==================== CUSTOM CSS DINAMIS & MOBILE OPTIMIZED ====================
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.6rem 1rem;
        min-height: 44px;
    }
    .footer-watermark {
        position: fixed;
        bottom: 5px;
        left: 10px;
        font-size: 11px;
        color: #6c757d;
        z-index: 999;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    .stDataFrame {
        overflow-x: auto;
    }
    </style>
""", unsafe_allow_html=True)

# Jika dipilih mode ponsel, terapkan CSS yang memaksimalkan layar kecil & merapikan kolom
if st.session_state.view_mode == "📱 Mode Khusus Ponsel (Mobile)":
    st.markdown("""
        <style>
        .block-container {
            padding-top: 0.8rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            padding-bottom: 3rem !important;
        }
        h1 { font-size: 1.25rem !important; line-height: 1.3 !important; }
        h2 { font-size: 1.1rem !important; }
        h3 { font-size: 1.0rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
        
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

# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            reset_code TEXT,
            code_expiry TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            tanggal TEXT,
            pair TEXT,
            tipe TEXT,
            lot REAL,
            entry REAL,
            sl REAL,
            exit REAL,
            pl REAL,
            strategi TEXT,
            emosi TEXT,
            screenshot_name TEXT,
            screenshot_data BLOB
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def is_same_as_old_password(username, new_password):
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    if data:
        return data[0] == make_hash(new_password)
    return False

def send_email_otp(receiver_email, code):
    if EMAIL_SENDER == "email_anda@gmail.com":
        return False, "Konfigurasi email server belum diatur oleh developer."
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Lensjourneyy Support <{EMAIL_SENDER}>"
        msg['To'] = receiver_email
        msg['Subject'] = "Kode Verifikasi Keamanan Jurnal Trading"
        
        body = f"Halo,\n\nBerikut adalah kode verifikasi Anda: {code}\nKode ini berlaku selama 10 menit.\n\nSalam,\nLensjourneyy Support Team"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, receiver_email, msg.as_string())
        server.quit()
        return True, "Kode verifikasi berhasil dikirim ke email!"
    except Exception as e:
        return False, f"Gagal mengirim email: {str(e)}"

def check_user(username, password):
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    if data:
        return data[0] == make_hash(password)
    return False

def add_user(username, email, password):
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, email, password) VALUES (?, ?, ?)', (username, email, make_hash(password)))
        conn.commit()
        conn.close()
        return True, "Akun berhasil didaftarkan."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username atau Email sudah terdaftar."

def load_trades(username):
    conn = sqlite3.connect('trading_journal.db')
    query = '''
        SELECT id, tanggal as Tanggal, pair as Pair, tipe as Tipe, lot as Lot, 
               entry as Entry, sl as SL, exit as Exit, pl as "P/L ($)", 
               strategi as Strategi, emosi as "Emosi / Catatan", screenshot_name 
        FROM trades WHERE username = ?
    '''
    df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()
    return df

def save_trade(username, row_data, file_name, file_bytes):
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO trades (username, tanggal, pair, tipe, lot, entry, sl, exit, pl, strategi, emosi, screenshot_name, screenshot_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        username, row_data["Tanggal"], row_data["Pair"], row_data["Tipe"], row_data["Lot"], 
        row_data["Entry"], row_data["SL"], row_data["Exit"], row_data["P/L ($)"], 
        row_data["Strategi"], row_data["Emosi / Catatan"], file_name, file_bytes
    ))
    conn.commit()
    conn.close()

# ==================== SESSION STATE LOGIN ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'forgot_step' not in st.session_state:
    st.session_state.forgot_step = 1

# ==================== HALAMAN AUTHENTICATION ====================
if not st.session_state.logged_in:
    col_empty1, col_center, col_empty2 = st.columns([0.05, 1, 0.05])
    
    with col_center:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #00ADB5;'>📈 TRADING JOURNAL & RISK MTRX</h1>", unsafe_allow_html=True)
       st.markdown("<h1 style='text-align: center; color: #00ADB5;'>📈 TRADING JOURNAL & RISK MTRX</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #AAAAAA; font-size: 0.9rem;'>Sistem Jurnal Trading & Manajemen Risiko</p>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("<p style='text-align: center; font-weight: bold; margin-bottom: 5px; font-size: 0.95rem;'>📱 Pilih Mode Tampilan Layar:</p>", unsafe_allow_html=True)
        
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
            
        st.markdown("---")
        
        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Masuk", "📝 Daftar", "🔄 Pemulihan"])
        
        with auth_tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            l_user = st.text_input("Username", key="l_user", placeholder="Masukkan username...")
            l_pass = st.text_input("Password", type="password", key="l_pass", placeholder="Masukkan password...")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Masuk ke Aplikasi", type="primary"):
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
            r_email = st.text_input("Email Aktif", key="r_email", placeholder="nama@email.com")
            r_pass = st.text_input("Password Baru", type="password", key="r_pass", placeholder="Buat password...")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✨ Daftar Akun Sekarang"):
                if r_user.strip() == "" or r_email.strip() == "" or r_pass.strip() == "":
                    st.warning("⚠️ Semua kolom data harus diisi.")
                else:
                    success, msg = add_user(r_user, r_email, r_pass)
                    if success:
                        st.success(f"🎉 {msg} Silakan pindah ke tab 'Masuk'.")
                    else:
                        st.error(f"⚠️ {msg}")

        with auth_tab3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Pemulihan Password via Email")
            
            f_user = st.text_input("Username Akun Anda", key="f_user")
            f_email = st.text_input("Email Terdaftar", key="f_email")
            
            if st.button("📤 Kirim Kode OTP"):
                conn = sqlite3.connect('trading_journal.db')
                c = conn.cursor()
                c.execute('SELECT email FROM users WHERE username = ? AND email = ?', (f_user, f_email))
                res = c.fetchone()
                conn.close()
                
                if res:
                    otp_code = str(random.randint(100000, 999999))
                    expiry = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    conn = sqlite3.connect('trading_journal.db')
                    c = conn.cursor()
                    c.execute('UPDATE users SET reset_code = ?, code_expiry = ? WHERE username = ?', (otp_code, expiry, f_user))
                    conn.commit()
                    conn.close()
                    
                    sent_ok, sent_msg = send_email_otp(f_email, otp_code)
                    if sent_ok:
                        st.success("✅ Kode verifikasi telah dikirim ke email!")
                        st.session_state.forgot_step = 2
                    else:
                        st.warning(f"⚠️ {sent_msg} (Simulasi OTP Anda: **{otp_code}**)")
                        st.session_state.forgot_step = 2
                else:
                    st.error("⚠️ Username dan Email tidak cocok.")

            if st.session_state.forgot_step == 2:
                st.markdown("---")
                entered_otp = st.text_input("Masukkan Kode OTP 6-Digit", key="ent_otp")
                new_p1 = st.text_input("Password Baru", type="password", key="np1")
                new_p2 = st.text_input("Konfirmasi Password Baru", type="password", key="np2")
                
                if st.button("🔒 Konfirmasi Ganti Password"):
                    conn = sqlite3.connect('trading_journal.db')
                    c = conn.cursor()
                    c.execute('SELECT reset_code, code_expiry FROM users WHERE username = ?', (f_user,))
                    row = c.fetchone()
                    conn.close()
                    
                    if row and row[0] == entered_otp:
                        if datetime.now() <= datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S'):
                            if new_p1 == new_p2 and len(new_p1) > 0:
                                if is_same_as_old_password(f_user, new_p1):
                                    st.error("⚠️ Password baru tidak boleh sama dengan password lama!")
                                else:
                                    conn = sqlite3.connect('trading_journal.db')
                                    c = conn.cursor()
                                    c.execute('UPDATE users SET password = ?, reset_code = NULL, code_expiry = NULL WHERE username = ?', (make_hash(new_p1), f_user))
                                    conn.commit()
                                    conn.close()
                                    st.success("🎉 Password berhasil diubah! Silakan login.")
                                    st.session_state.forgot_step = 1
                            else:
                                st.error("⚠️ Password tidak cocok atau kosong.")
                        else:
                            st.error("⚠️ Kode verifikasi kedaluwarsa.")
                    else:
                        st.error("⚠️ Kode verifikasi salah.")

    st.markdown('<div class="footer-watermark">⚡ Powered by Lensjourneyy</div>', unsafe_allow_html=True)

# ==================== APLIKASI UTAMA SETELAH LOGIN ====================
else:
    st.sidebar.title(f"👤 Akun: {st.session_state.username}")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📱 Pengaturan Tampilan")
    sidebar_mode = st.sidebar.radio(
        "Pilih Mode Tampilan:",
        ["📱 Mode Khusus Ponsel (Mobile)", "🖥️ Mode Desktop (Lebar)"],
        index=0 if st.session_state.view_mode == "📱 Mode Khusus Ponsel (Mobile)" else 1,
        key="sb_view_mode"
    )
    if sidebar_mode != st.session_state.view_mode:
        st.session_state.view_mode = sidebar_mode
        st.rerun()

    if st.sidebar.button("🚪 Keluar (Logout)"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.title("📈 Navigasi Jurnal")
    menu = st.sidebar.radio("Pilih Menu:", [
        "📊 Dashboard & Analitik", 
        "🧮 Kalkulator Lot & Risiko", 
        "➕ Input Jurnal & Screenshot", 
        "📋 Riwayat & Kalender", 
        "📖 Panduan & Penjelasan Sistem"
    ])

    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='text-align: center; color: #6c757d; font-size: 12px;'>⚡ Powered by <b>Lensjourneyy</b></p>", unsafe_allow_html=True)

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
            st.success("🎉 Data jurnal dan screenshot berhasil disimpan ke akun Anda!")

    elif menu == "📋 Riwayat & Kalender":
        st.title("📋 Riwayat Lengkap & Galeri Jurnal Trading")
        st.markdown("Daftar seluruh transaksi yang pernah Anda catat, lengkap dengan opsi unduh data dan galeri gambar chart.")
        
        if len(df_raw) > 0:
            display_df = df_raw.drop(columns=["id", "screenshot_name"], errors="ignore")
            st.dataframe(display_df, use_container_width=True)
            
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Jurnal ke Format CSV",
                data=csv,
                file_name=f'jurnal_trading_{st.session_state.username}.csv',
                mime='text/css',
            )
            
            st.markdown("---")
            st.subheader("🖼️ Galeri Screenshot Chart Transaksi")
            conn = sqlite3.connect('trading_journal.db')
            c = conn.cursor()
            c.execute('SELECT tanggal, pair, pl, screenshot_name, screenshot_data FROM trades WHERE username = ? AND screenshot_data IS NOT NULL', (st.session_state.username,))
            img_rows = c.fetchall()
            conn.close()
            
            if img_rows:
                for row in img_rows:
                    dt, pr, pl_val, s_name, s_data = row
                    with st.expander(f"📁 Tanggal: {dt} | Pair: {pr} | P/L: ${pl_val} | File: {s_name}"):
                        st.image(s_data, caption=s_name, use_container_width=True)
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
            * **Registrasi & Login Akun:** Setiap akun diamankan dengan enkripsi *hash* SHA-256 untuk menjaga privasi data trading Anda.
            * **Verifikasi Email & Pemulihan Password:** Dilengkapi sistem pengiriman kode OTP 6-digit via email untuk proses reset password yang aman dan terlindungi.
            * **Validasi Password Lama:** Sistem secara otomatis mendeteksi dan menolak apabila Anda mencoba memasukkan password baru yang sama persis dengan password lama Anda.
            * **Mode Tampilan Responsif:** Anda dapat beralih antara **Mode Desktop (Lebar)** dan **Mode Kompak (HP / Mobile)** melalui tombol pengaturan di menu login maupun sidebar utama agar aplikasi tetap nyaman diakses lewat berbagai perangkat.
            """)
