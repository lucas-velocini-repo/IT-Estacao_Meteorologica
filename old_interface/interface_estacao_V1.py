# streamlit run "C:\Users\Lucas Velocini\Desktop\Atalhos\Unicamp\IT-Estacao_Meteorologica\interface_estacao_V1.py"

import streamlit as st
import requests
import pandas as pd
import time

# CONFIGURAÇÕES INICIAIS
st.set_page_config(page_title="Estação Meteorológica", layout="wide")

st.title("Monitoramento em Tempo Real — Estação Meteorológica")
st.markdown("Visualização ao vivo dos sensores conectados ao ESP32")

# CONFIGURAÇÃO DO ENDEREÇO DO ESP32
svr_ip = st.text_input("Endereço IP do Servidor", "192.168.1.101:8000")
url = f"http://{svr_ip}/dados"

# ÁREA DE ATUALIZAÇÃO AUTOMÁTICA
update_interval = st.slider("Intervalo de atualização (segundos)", 2, 30, 10)

# Dados armazenados
if "dados" not in st.session_state:
    st.session_state["dados"] = pd.DataFrame()

# LOOP DE ATUALIZAÇÃO
placeholder = st.empty()

while True:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()

            # Organiza os dados
            novo = {
                "Hora": time.strftime("%H:%M:%S"),
                "Temperatura (°C)": data["temperature"],
                "Umidade (%)": data["humidity"],
                "Pressão (hPa)": data["pressure"],
                "Luz (lux)": data["light"],
                "PM 1.0 (µg/m³)": data["pm"]["1.0"],
                "PM 2.5 (µg/m³)": data["pm"]["2.5"],
                "PM 4 (µg/m³)": data["pm"]["4.0"],
                "PM 10 (µg/m³)": data["pm"]["10.0"],
                "NC 0.5 (Particulas/cm³)": data["nc"]["0.5"],
                "NC 1.0 (Particulas/cm³)": data["nc"]["1.0"],
                "NC 2.5 (Particulas/cm³)": data["nc"]["2.5"],
                "NC 4 (Particulas/cm³)": data["nc"]["4.0"],
                "NC 10 (Particulas/cm³)": data["nc"]["10.0"]
                
            }

            st.session_state["dados"] = pd.concat(
                [st.session_state["dados"], pd.DataFrame([novo])],
                ignore_index=True
            )

            # Mantém só os últimos 50 registros
            st.session_state["dados"] = st.session_state["dados"].tail(50)

            df = st.session_state["dados"]

            # VISUALIZAÇÃO
            with placeholder.container():
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🌡️ Temperatura (°C)", f"{novo['Temperatura (°C)']:.2f}")
                col2.metric("💧 Umidade (%)", f"{novo['Umidade (%)']:.2f}")
                col3.metric("🌤️ Luminosidade (lux)", f"{novo['Luz (lux)']:.2f}")
                col4.metric("🧭 Pressão (hPa)", f"{novo['Pressão (hPa)']:.2f}")

                st.markdown("### 🌦️ Pressão, Temperatura e Umidade")
                st.line_chart(df.set_index("Hora")[["Temperatura (°C)", "Umidade (%)", "Pressão (hPa)"]])

                st.markdown("### 🌤️ Luminosidade")
                st.line_chart(df.set_index("Hora")[["Luz (lux)"]])

                st.markdown("### 🌫️ Particulados (PM)")
                st.line_chart(df.set_index("Hora")[["PM 1.0 (µg/m³)", "PM 2.5 (µg/m³)", "PM 4 (µg/m³)", "PM 10 (µg/m³)"]])

                st.markdown("### 🌫️ Particulados (NC)")
                st.line_chart(df.set_index("Hora")[["NC 0.5 (Particulas/cm³)", "NC 1.0 (Particulas/cm³)", "NC 2.5 (Particulas/cm³)", "NC 4 (Particulas/cm³)", "NC 10 (Particulas/cm³)"]])

                st.markdown("### 💾 Dados brutos")
                st.dataframe(df, use_container_width=True)

        else:
            st.warning("⚠️ Não foi possível obter dados. Verifique o IP e a conexão Wi-Fi.")

    except Exception as e:
        st.error(f"Erro ao conectar ao ESP32: {e}")

    time.sleep(update_interval)