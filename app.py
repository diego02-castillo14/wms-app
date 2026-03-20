import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="WMS Buscador", layout="centered")

# -------------------------
# SESSION STATE
# -------------------------
if "busqueda" not in st.session_state:
    st.session_state.busqueda = ""

# -------------------------
# LOGO CENTRADO
# -------------------------
col_logo1, col_logo2, col_logo3 = st.columns([1,2,1])
with col_logo2:
    st.image("logo.jpg", width=220)

st.title("🔎 WMS Buscador de Ubicaciones")

# -------------------------
# INTERPRETAR UBICACIÓN
# -------------------------
def interpretar_ubicacion(codigo):
    partes = str(codigo).strip().upper().split("-")

    almacen_map = {"A": "Álamos", "B": "Balboa"}
    almacen = almacen_map.get(partes[0], partes[0])

    anaquel_raw = partes[1] if len(partes) > 1 else ""
    if anaquel_raw == "AR":
        anaquel = "Sin anaquel"
    elif anaquel_raw.startswith("A"):
        anaquel = f"Anaquel {anaquel_raw[1:]}"
    elif anaquel_raw.startswith("P"):
        anaquel = f"Panel {anaquel_raw[1:]}"
    else:
        anaquel = anaquel_raw

    piso_raw = partes[2] if len(partes) > 2 else ""
    if piso_raw == "AR":
        piso = "Arriba"
    elif piso_raw == "00":
        piso = "Sin piso"
    elif piso_raw.startswith("P"):
        piso = f"Piso {piso_raw[1:]}"
    else:
        piso = piso_raw

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
# CARGA DE DATOS
# -------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_excel("inventario.xlsx")
    df.columns = df.columns.str.strip()

    df["Clave"] = df["Clave"].astype(str).str.strip().str.upper()
    df["Descripción"] = df["Descripción"].astype(str).str.strip()
    df["Ubicación"] = df["Ubicación"].astype(str).str.strip()

    df[["Almacén", "Anaquel", "Piso", "Caja"]] = df["Ubicación"].apply(
        lambda x: pd.Series(interpretar_ubicacion(x))
    )

    return df

df = cargar_datos()

# -------------------------
# BOTÓN RECARGAR
# -------------------------
if st.button("🔄 Recargar datos"):
    st.cache_data.clear()
    st.rerun()

# -------------------------
# FILTROS
# -------------------------
st.subheader("🎛️ Filtros")

colf1, colf2 = st.columns(2)

with colf1:
    filtro_almacen = st.selectbox("Almacén", ["Todos"] + sorted(df["Almacén"].unique()))
    filtro_anaquel = st.selectbox("Anaquel", ["Todos"] + sorted(df["Anaquel"].unique()))

with colf2:
    filtro_piso = st.selectbox("Piso", ["Todos"] + sorted(df["Piso"].unique()))
    filtro_caja = st.selectbox("Caja / Gaveta", ["Todos"] + sorted(df["Caja"].unique()))

# -------------------------
# BUSCADOR + ESCÁNER
# -------------------------
col1, col2 = st.columns([4,1])

with col1:
    query = st.text_input("🔍 Buscar producto", key="busqueda")

with col2:
    activar_scan = st.button("📷")

# -------------------------
# ESCÁNER WEB (FUNCIONAL)
# -------------------------
if activar_scan:
    components.html("""
    <div id="reader" style="width:100%"></div>

    <script src="https://unpkg.com/html5-qrcode"></script>

    <script>
    function onScanSuccess(decodedText) {

        // Vibración (Android)
        if (navigator.vibrate) {
            navigator.vibrate([100,50,100]);
        }

        const input = window.parent.document.querySelector('input[type="text"]');

        if (input) {
            input.value = decodedText;

            input.dispatchEvent(new Event("input", { bubbles: true }));

            // 🔥 RECARGA PARA EJECUTAR BÚSQUEDA
            setTimeout(() => {
                window.parent.location.reload();
            }, 300);
        }
    }

    const html5QrcodeScanner = new Html5Qrcode("reader");

    html5QrcodeScanner.start(
        { facingMode: "environment" },
        {
            fps: 25,
            qrbox: { width: 300, height: 150 }
        },
        onScanSuccess
    );
    </script>
    """, height=320)

# -------------------------
# FILTRADO
# -------------------------
df_filtrado = df.copy()

if filtro_almacen != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Almacén"] == filtro_almacen]

if filtro_anaquel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Anaquel"] == filtro_anaquel]

if filtro_piso != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Piso"] == filtro_piso]

if filtro_caja != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Caja"] == filtro_caja]

# -------------------------
# BÚSQUEDA
# -------------------------
query = st.session_state.get("busqueda", "")

if query and len(query) >= 2:
    query_low = query.lower()

    df_filtrado = df_filtrado[
        df_filtrado["Clave"].str.lower().str.contains(query_low, na=False) |
        df_filtrado["Descripción"].str.lower().str.contains(query_low, na=False)
    ]

# -------------------------
# LIMITAR RESULTADOS
# -------------------------
df_filtrado = df_filtrado.head(50)

# -------------------------
# RESULTADOS
# -------------------------
if not df_filtrado.empty:
    st.success(f"Resultados: {len(df_filtrado)}")

    for row in df_filtrado.itertuples():
        st.markdown("---")

        st.markdown(f"### 🔩 {row.Clave}")
        st.write(row.Descripción)

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"📍 {row.Almacén}")
            st.info(f"🗄 {row.Anaquel}")

        with col2:
            st.success(f"📦 {row.Piso}")
            st.success(f"📦 {row.Caja}")

else:
    st.warning("Sin resultados")
