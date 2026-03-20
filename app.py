import streamlit as st
import pandas as pd
from PIL import Image

# Scanner
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
from pyzbar import pyzbar

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="WMS Santuzi", layout="wide")

# =========================
# LOGO CENTRADO
# =========================
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("logo.jpg", width=220)

st.title("🔍 Buscador de Ubicaciones")

# =========================
# CARGA OPTIMIZADA
# =========================
@st.cache_data
def cargar_datos():
    df = pd.read_excel("inventario.xlsx")
    df.columns = df.columns.str.strip()
    df["Clave"] = df["Clave"].astype(str).str.upper()
    df["Descripción"] = df["Descripción"].astype(str)
    df["Ubicación"] = df["Ubicación"].astype(str).str.upper()
    df["Almacén"] = df["Almacén"].astype(str).str.upper()
    return df

df = cargar_datos()

# =========================
# INTERPRETAR UBICACIÓN
# =========================
def interpretar_ubicacion(ubicacion):
    try:
        partes = ubicacion.split("-")

        almacen = "Álamos" if partes[0] == "A" else "Balboa"

        anaquel_raw = partes[1]
        piso_raw = partes[2]
        caja_raw = partes[3] if len(partes) > 3 else "00"

        # ANAQUEL
        if anaquel_raw == "AR":
            anaquel = "Sin anaquel"
        elif anaquel_raw.startswith("A"):
            anaquel = f"Anaquel {anaquel_raw[1:]}"
        elif anaquel_raw.startswith("P"):
            anaquel = f"Panel {anaquel_raw[1:]}"
        else:
            anaquel = anaquel_raw

        # PISO
        if piso_raw == "AR":
            piso = "Arriba"
        elif piso_raw == "00":
            piso = "Sin piso"
        else:
            piso = f"Piso {piso_raw[1:]}"

        # CAJA
        if caja_raw == "00":
            caja = "Sin caja"
        elif caja_raw.startswith("C"):
            caja = f"Caja {caja_raw[1:]}"
        elif caja_raw.startswith("G"):
            caja = f"Gaveta {caja_raw[1:]}"
        elif caja_raw.startswith("MG"):
            caja = f"Mini Gaveta {caja_raw[2:]}"
        elif caja_raw.startswith("GM"):
            caja = f"Gaveta Mediana {caja_raw[2:]}"
        elif caja_raw.startswith("CM"):
            caja = f"Caja Mediana {caja_raw[2:]}"
        else:
            caja = caja_raw

        return almacen, anaquel, piso, caja

    except:
        return "-", "-", "-", "-"

# =========================
# FILTROS
# =========================
colf1, colf2 = st.columns(2)

with colf1:
    filtro_almacen = st.selectbox("Filtrar por almacén", ["Todos"] + list(df["Almacén"].unique()))

with colf2:
    filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos", "Anaquel", "Panel", "Gaveta", "Caja"])

# =========================
# BUSCADOR
# =========================
busqueda = st.text_input("Buscar producto, ubicación o escanear código", key="busqueda")

# =========================
# SCANNER MEJORADO
# =========================
class Scanner(VideoTransformerBase):
    def __init__(self):
        self.last_code = ""

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        barcodes = pyzbar.decode(img)

        for barcode in barcodes:
            x, y, w, h = barcode.rect
            cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)

            code = barcode.data.decode("utf-8")

            if code != self.last_code:
                self.last_code = code
                st.session_state["busqueda"] = code

            cv2.putText(img, code, (x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0,255,0), 2)

        return img

if st.button("📷 Escanear"):
    webrtc_streamer(
        key="scanner",
        video_processor_factory=Scanner,
        media_stream_constraints={
            "video": {"facingMode": {"ideal": "environment"}},
            "audio": False,
        },
    )

# =========================
# FILTRAR DATOS
# =========================
if busqueda:
    df_filtrado = df[
        df.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)
    ]
else:
    df_filtrado = df

# filtro almacén
if filtro_almacen != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Almacén"] == filtro_almacen]

# =========================
# RESULTADOS
# =========================
st.markdown(f"### Resultados: {len(df_filtrado)}")

# =========================
# TARJETAS BONITAS
# =========================
for _, row in df_filtrado.iterrows():

    almacen, anaquel, piso, caja = interpretar_ubicacion(row["Ubicación"])

    st.markdown(f"""
    <div style="
        background-color:#1e1e1e;
        padding:15px;
        border-radius:15px;
        margin-bottom:10px;
        border:1px solid #333;
    ">
        <h4 style="margin:0; color:white;">🔩 {row['Clave']}</h4>
        <p style="margin:0; color:#ccc;">{row['Descripción']}</p>
        <hr>
        <p style="margin:0;">📍 <b>{almacen}</b></p>
        <p style="margin:0;">🗄 {anaquel}</p>
        <p style="margin:0;">📦 {piso}</p>
        <p style="margin:0;">📦 {caja}</p>
    </div>
    """, unsafe_allow_html=True)
