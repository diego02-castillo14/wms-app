import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="WMS Buscador", layout="centered")

# -------------------------
# LOGO
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
# DATA
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
# BUSCADOR
# -------------------------
col1, col2 = st.columns([4,1])

with col1:
    query = st.text_input("🔍 Buscar producto")

with col2:
    activar_scan = st.button("📷 Escanear")

# -------------------------
# ESCÁNER (FIX REAL)
# -------------------------
if activar_scan:
    components.html("""
    <div style="text-align:center;">
        <video id="video" style="width:100%; max-width:400px;"></video>
        <p>📷 Apunta al código de barras</p>
    </div>

    <script src="https://unpkg.com/@zxing/library@latest"></script>

    <script>
    const codeReader = new ZXing.BrowserMultiFormatReader();

    async function start() {
        try {
            await codeReader.decodeFromConstraints(
                {
                    video: {
                        facingMode: "environment"
                    }
                },
                'video',
                (result, err) => {
                    if (result) {
                        const code = result.text;

                        // 🔥 ESCRIBIR EN INPUT STREAMLIT
                        const input = window.parent.document.querySelector('input');

                        if (input) {
                            input.value = code;
                            input.dispatchEvent(new Event("input", { bubbles: true }));
                        }

                        // vibración
                        if (navigator.vibrate) navigator.vibrate(200);

                        codeReader.reset();
                    }
                }
            );
        } catch (e) {
            document.body.innerHTML += "<p style='color:red;'>Error cámara: " + e + "</p>";
        }
    }

    start();
    </script>
    """, height=500)

# -------------------------
# FILTRADO
# -------------------------
df_filtrado = df.copy()

if query:
    query = query.lower()

    df_filtrado = df_filtrado[
        df_filtrado["Clave"].str.lower().str.contains(query, na=False) |
        df_filtrado["Descripción"].str.lower().str.contains(query, na=False)
    ]

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

        c1, c2 = st.columns(2)
        with c1:
            st.info(f"📍 {row.Almacén}")
            st.info(f"🗄 {row.Anaquel}")
        with c2:
            st.success(f"📦 {row.Piso}")
            st.success(f"📦 {row.Caja}")

else:
    st.warning("Sin resultados")
