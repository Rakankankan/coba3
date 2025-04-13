import streamlit as st
import requests
import pandas as pd
import random
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from streamlit_autorefresh import st_autorefresh

# --- CONFIG ---
UBIDOTS_TOKEN = "BBUS-JBKLQqTfq2CPXNytxeUfSaTjekeL1K"
DEVICE_LABEL = "hsc345"
VARIABLES = ["mq2", "humidity", "temperature", "lux"]

# --- STYLE ---
st.markdown("""
    <style>
        .main-title {
            background-color: #001f3f;
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 32px;
            border-radius: 8px;
            margin-bottom: 25px;
        }

        .data-box {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 20px;
            margin-bottom: 10px;
            font-size: 22px;
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
        }

        .label {
            font-weight: bold;
        }

        .data-value {
            font-size: 24px;
            font-weight: bold;
        }

        .refresh-btn {
            position: absolute;
            top: 30px;
            right: 30px;
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
        }

        .refresh-btn:hover {
            background-color: #005a8d;
        }
    </style>
""", unsafe_allow_html=True)

# --- DATA FETCH ---
def get_ubidots_data(variable_label):
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}/{variable_label}/values"
    headers = {
        "X-Auth-Token": UBIDOTS_TOKEN,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        return None

# --- SIMULASI DATA (UNTUK LATIHAN MODEL) ---
@st.cache_data
def generate_mq2_simulation_data(n_samples=100):
    data = []
    for _ in range(n_samples):
        label = random.choices([0, 1], weights=[0.7, 0.3])[0]
        value = random.randint(400, 1000) if label == 1 else random.randint(100, 400)
        data.append((value, label))
    df = pd.DataFrame(data, columns=["mq2_value", "label"])
    return df

@st.cache_resource
def train_mq2_model():
    df = generate_mq2_simulation_data()
    X = df[['mq2_value']]
    y = df['label']
    model = LogisticRegression()
    model.fit(X, y)
    return model

model = train_mq2_model()

# --- AI LOGIC ---
def predict_smoke_status(mq2_value):
    if mq2_value > 800:
        return "🚨 Bahaya! Terdeteksi asap rokok!"
    elif mq2_value >= 500:
        return "⚠️ Mencurigakan: kemungkinan ada asap, tapi belum pasti rokok."
    else:
        return "✅ Semua aman, tidak terdeteksi asap mencurigakan."

def evaluate_lux_condition(lux_value, mq2_value):
    if lux_value <= 50:
        if "Bahaya" in predict_smoke_status(mq2_value):
            return "🚨 Agak mencurigakan: gelap dan ada indikasi asap rokok!"
        elif "Mencurigakan" in predict_smoke_status(mq2_value):
            return "⚠️ Toilet gelap dan ada kemungkinan asap, perlu dipantau."
        else:
            return "🌑 Toilet dalam kondisi gelap, tapi tidak ada asap. Masih aman."
    else:
        return "💡 Lampu menyala, kondisi toilet terang."

def evaluate_temperature_condition(temp_value):
    if temp_value >= 31:
        return "🔥 Suhu sangat panas, bisa tidak nyaman, bisa berbahaya!"
    elif temp_value >= 29:
        return "🌤️ Suhu cukup panas, kurang nyama."
    elif temp_value <= 28:
        return "✅ Suhu normal dan nyaman."
    else:
        return "❄️ Suhu terlalu dingin, bisa tidak nyaman."

def chatbot_response(question, mq2_value, lux_value=None, temperature_value=None):
    question = question.lower()

    if "rokok" in question or "situasi" in question:
        status = predict_smoke_status(mq2_value)
        return status.replace("🚨", "").replace("⚠️", "").replace("✅", "").strip()

    elif "lampu" in question or "lux" in question or "cahaya" in question or "gelap" in question:
        if lux_value is not None:
            status = evaluate_lux_condition(lux_value, mq2_value)
            return status.replace("🚨", "").replace("🌑", "").replace("💡", "").replace("⚠️", "").strip()
        else:
            return "Saya belum bisa membaca data lux sekarang."

    elif "suhu" in question or "temperature" in question or "panas" in question or "dingin" in question:
        if temperature_value is not None:
            status = evaluate_temperature_condition(temperature_value)
            return status.replace("🔥", "").replace("🌤️", "").replace("✅", "").replace("❄️", "").strip()
        else:
            return "Saya belum bisa membaca data suhu sekarang."

    elif "status" in question:
        status_mq2 = predict_smoke_status(mq2_value)
        status_lux = evaluate_lux_condition(lux_value, mq2_value) if lux_value is not None else ""
        return f"Status asap: {status_mq2.replace('🚨','').replace('⚠️','').replace('✅','').strip()} | Penerangan: {status_lux.replace('🚨','').replace('⚠️','').replace('🌑','').replace('💡','').strip()}"

    else:
        return "Maaf, saya belum paham pertanyaannya."

# --- UI START ---
st.markdown('<div class="main-title">Live Stream Data + AI Deteksi Rokok & Cahaya</div>', unsafe_allow_html=True)

mq2_value_latest = None
lux_value_latest = None
temperature_value_latest = None  # Tambahan

# --- Button untuk menghidupkan auto-refresh ---
auto_refresh = st.checkbox("Aktifkan Auto-Refresh Data", value=True)
if auto_refresh:
    st_autorefresh(interval=5000, limit=None, key="auto_refresh")  # Refresh setiap 5 detik

# --- Loop setiap variabel dari Ubidots ---
for var_name in VARIABLES:
    data = get_ubidots_data(var_name)
    if data:
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        value = round(df.iloc[0]['value'], 2)

        if var_name == "mq2":
            var_label = "ASAP/GAS"
            emoji = "💨"
        elif var_name == "humidity":
            var_label = "KELEMBAPAN"
            emoji = "💧"
        elif var_name == "temperature":
            var_label = "SUHU"
            emoji = "🌡️"
        elif var_name == "lux":
            var_label = "INTENSITAS CAHAYA"
            emoji = "💡"

        st.markdown(
            f'<div class="data-box"><span class="label">{emoji} {var_label}</span><span class="data-value">{value}</span></div>',
            unsafe_allow_html=True
        )

        st.line_chart(df[['timestamp', 'value']].set_index('timestamp'))

        if var_name == "mq2":
            mq2_value_latest = value
            status = predict_smoke_status(value)
            if "Bahaya" in status:
                st.error(status)
            elif "Mencurigakan" in status:
                st.warning(status)
            else:
                st.success(status)

        if var_name == "lux":
            lux_value_latest = value
            lux_status = evaluate_lux_condition(value, mq2_value_latest or 0)
            if "mencurigakan" in lux_status.lower():
                st.warning(lux_status)
            else:
                st.info(lux_status)

        if var_name == "temperature":
            temperature_value_latest = value
            temp_status = evaluate_temperature_condition(value)
            if "panas" in temp_status.lower() or "berbahaya" in temp_status.lower():
                st.warning(temp_status)
            elif "dingin" in temp_status.lower():
                st.info(temp_status)
            else:
                st.success(temp_status)

    else:
        st.error(f"Gagal mengambil data dari variabel: {var_name}")

# --- CHATBOT ---
if mq2_value_latest is not None:
    st.markdown("---")
    st.subheader("💬 Chatbot Pengawas")

    questions = [
        "Ada asap rokok di sini?",
        "Bagaimana situasi asap rokok?",
        "Apakah terdeteksi asap rokok?",
        "Ada bahaya asap rokok?",
        "Status umum di sekitar?",
        "Apa status cahaya di toilet?",
        "Bagaimana kondisi cahaya di sini?",
        "Apakah lampu menyala?",
        "Cahaya di sini bagaimana?",
        "Bagaimana situasi pencahayaan?",
        "Apa status terbaru tentang keadaan?",
        "Bagaimana kondisi sekarang?",
        "Apa yang terdeteksi di sini?",
        "Apakah ada bahaya yang perlu diwaspadai?",
        "Ada indikasi asap atau gelap?",
        "Adakah perubahan pada suhu, kelembapan, atau cahaya?",
        "Apa kondisi suhu di sini?",
        "Apakah suhu terlalu panas atau dingin?",
        "Bagaimana kenyamanan suhu sekarang?"
    ]

    selected_question = st.selectbox("Pilih pertanyaan yang ingin ditanyakan:", questions)

    if selected_question:
        response = chatbot_response(selected_question, mq2_value_latest, lux_value_latest, temperature_value_latest)
        st.write(f"🤖: {response}")
