import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="WMS Buscador", layout="centered")

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
# INTERPRETAR UBICACIÓN
# -------------------------
def interpretar_ubicacion(codigo):
    partes = str(codigo).strip().upper().split("-")

    almacen_map = {"A": "Álamos", "B": "Balboa"}
    almacen = almacen_map.get(partes[0], partes[0])

    # ANAQUEL
    anaquel_raw = partes[1] if len(partes) > 1 else ""
    if anaquel_raw == "AR":
        anaquel = "Sin anaquel (Arriba)"
    elif anaquel_raw.startswith("A"):
        anaquel = f"Anaquel {anaquel_raw[1:]}"
    else:
        anaquel = anaquel_raw

    # PISO
    piso_raw = partes[2] if len(partes) > 2 else ""
    if piso_raw == "AR":
        piso = "Arriba"
    elif piso_raw == "00":
        piso = "Sin piso"
    elif piso_raw.startswith("P"):
        piso = f"Piso {piso_raw[1:]}"
    else:
        piso = piso_raw

    # CAJA
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
        caja = caja_raw.capitalize()

    return almacen, anaquel, piso, caja

# -------------------------
# BUSCAR
# -------------------------
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
# UI
# -------------------------
st.title("🔎 WMS Buscador de Ubicaciones")

# 🔍 BARRA + BOTÓN
col1, col2 = st.columns([4,1])

with col1:
    query = st.text_input("🔍 Buscar producto", key="busqueda")

with col2:
    activar_scan = st.button("📷")

# -------------------------
# ESCÁNER (SOLO SI SE ACTIVA)
# -------------------------
if activar_scan:
    components.html("""
    <div id="reader" style="width:100%"></div>

    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    function onScanSuccess(decodedText) {
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if (inputs.length > 0) {
            inputs[0].value = decodedText;
            inputs[0].dispatchEvent(new Event("input", { bubbles: true }));
        }
    }

    const config = {
        fps: 10,
        qrbox: {width: 250, height: 150},
        videoConstraints: {
            facingMode: "environment" // 🔥 cámara trasera
        }
    };

    const html5QrcodeScanner = new Html5Qrcode("reader");

    html5QrcodeScanner.start(
        { facingMode: "environment" },
        config,
        onScanSuccess
    );
    </script>
    """, height=300)

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
