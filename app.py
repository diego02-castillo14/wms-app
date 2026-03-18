import os
os.environ["DYLD_LIBRARY_PATH"] = "/opt/homebrew/lib"

import streamlit as st
import pandas as pd

# 📷 Escáner
from streamlit_webrtc import webrtc_streamer
import cv2
from pyzbar import pyzbar

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="WMS Buscador", layout="centered")

# -------------------------
# ESTILOS
# -------------------------
st.markdown("""
<style>
.card {
    background-color: #0f172a;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 15px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    color: white;
}
.title {
    font-size: 20px;
    font-weight: bold;
}
.desc {
    font-size: 14px;
    margin-bottom: 10px;
    color: #cbd5f5;
}
.grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# CARGA DE DATOS
# -------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_excel("inventario.xlsx")
    df.columns = df.columns.str.strip()

    df["Clave"] = df["Clave"].astype(str).str.strip()
    df["Descripción"] = df["Descripción"].astype(str).str.strip()
    df["Ubicación"] = df["Ubicación"].astype(str).str.strip()

    return df

df = cargar_datos()

# -------------------------
# FUNCIONES
# -------------------------
def interpretar_ubicacion(codigo):
    partes = str(codigo).strip().upper().split("-")

    # -------------------------
    # ALMACÉN
    # -------------------------
    almacen_map = {
        "A": "Álamos",
        "B": "Balboa"
    }

    almacen = almacen_map.get(partes[0], partes[0])

    # -------------------------
    # ANAQUEL
    # -------------------------
    anaquel_raw = partes[1] if len(partes) > 1 else ""

    if anaquel_raw == "AR":
        anaquel = "Sin anaquel (Arriba)"
    elif anaquel_raw.startswith("A"):
        anaquel = f"Anaquel {anaquel_raw[1:]}"
    else:
        anaquel = anaquel_raw

    # -------------------------
    # PISO
    # -------------------------
    piso_raw = partes[2] if len(partes) > 2 else ""

    if piso_raw == "AR":
        piso = "Arriba"
    elif piso_raw == "00":
        piso = "Sin piso"
    elif piso_raw.startswith("P"):
        piso = f"Piso {piso_raw[1:]}"
    else:
        piso = piso_raw

    # -------------------------
    # CAJA
    # -------------------------
    caja_raw = partes[3] if len(partes) > 3 else ""

    if caja_raw == "00":
        caja = "Sin caja"

    elif caja_raw.startswith("CM"):
        caja = f"Caja Mediana {caja_raw[2:]}"

    elif caja_raw.startswith("MG"):
        caja = f"Mini Gaveta {caja_raw[2:]}"

    elif caja_raw.startswith("GM"):
        caja = f"Gaveta Mediana {caja_raw[2:]}"

    elif caja_raw.startswith("G"):
        caja = f"Gaveta {caja_raw[1:]}"

    elif caja_raw.startswith("C"):
        caja = f"Caja {caja_raw[1:]}"

    else:
        # Nombre personalizado
        caja = caja_raw.capitalize()

    return almacen, anaquel, piso, caja


def buscar(query):
    query = str(query).strip().lower()
    query = query.replace(".0", "")

    df_temp = df.copy()

    df_temp["Clave"] = df_temp["Clave"].str.lower()
    df_temp["Descripción"] = df_temp["Descripción"].str.lower()
    df_temp["Ubicación"] = df_temp["Ubicación"].str.lower()

    return df_temp[
        df_temp["Clave"].str.contains(query, na=False) |
        df_temp["Descripción"].str.contains(query, na=False) |
        df_temp["Ubicación"].str.contains(query, na=False)
    ]

# -------------------------
# ESCÁNER
# -------------------------
def escanear_codigo(frame):
    imagen = frame.to_ndarray(format="bgr24")
    codigos = pyzbar.decode(imagen)

    for codigo in codigos:
        data = codigo.data.decode("utf-8")
        st.session_state["scanner"] = data

    return imagen

# -------------------------
# SESSION STATE
# -------------------------
if "scanner" not in st.session_state:
    st.session_state["scanner"] = ""

# -------------------------
# UI
# -------------------------
st.title("🔎 WMS Buscador de Ubicaciones")

# 📷 Escáner
st.subheader("📷 Escanear código")
webrtc_streamer(key="camera", video_frame_callback=escanear_codigo)

# 🔍 Input manual
query_manual = st.text_input("🔍 Buscar producto", key="busqueda")

# Mostrar scanner detectado
if st.session_state["scanner"]:
    st.success(f"📷 Código detectado: {st.session_state['scanner']}")

# 🔄 Botón limpiar
if st.button("🔄 Limpiar búsqueda"):
    st.session_state["scanner"] = ""
    st.session_state["busqueda"] = ""

# 🎯 LÓGICA DE BÚSQUEDA (CORREGIDA)
query = query_manual

if st.session_state["scanner"]:
    query = st.session_state["scanner"]

# -------------------------
# RESULTADOS
# -------------------------
if query:
    resultados = buscar(query)

    if resultados.empty:
        st.error("❌ No se encontraron resultados")
    else:
        st.success(f"Resultados encontrados: {len(resultados)}")

        for _, row in resultados.iterrows():
            almacen, anaquel, piso, caja = interpretar_ubicacion(row["Ubicación"])

            with st.container():
                st.markdown("---")

                st.markdown(f"### 🔩 {row['Clave']}")
                st.write(row["Descripción"])

                col1, col2 = st.columns(2)

                with col1:
                    st.info(f"📍 Almacén: {almacen}")
                    st.info(f"🗄 Anaquel: {anaquel}")

                with col2:
                    st.success(f"📦 Piso: {piso}")
                    st.success(f"📦 Caja: {caja}")