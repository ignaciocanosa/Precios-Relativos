import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

# --- Diccionario base de series ---
SERIES_META = {
    543: {"nombre": "Vacas C. Gtía. Preñez", "unidad": "por bulto"},
    531: {"nombre": "Vaquillonas C. Gtía. Preñez", "unidad": "por bulto"},
    32: {"nombre": "Novillos EyB 431/460 (MAG)", "unidad": "por kg"},
    47: {"nombre": "Vacas Conserva Buena (MAG)", "unidad": "por kg"},
    45: {"nombre": "Vacas Buenas (MAG)", "unidad": "por kg"},
    477: {"nombre": "Terneros 160-180 Kg", "unidad": "por kg"},
    313: {"nombre": "Terneras 150-170 Kg", "unidad": "por kg"},
    1861: {"nombre": "Alambre Nº17 x Kilo", "unidad": "por kg"},
    10931: {"nombre": "Urea Granulada", "unidad": "por kg"},
    10921: {"nombre": "Fosfato Diamónico", "unidad": "por kg"},
    7201: {"nombre": "Toyota Hilux CD", "unidad": "por unidad"},
    22028: {"nombre": "Unidad de Trabajo Agrícola (UTA)", "unidad": "por unidad"},
}
API_KEY = "#oCxIK1ENG$Ym86*cA=RUO(F)HrpfV!+-27&iTwPj^vy"

st.set_page_config(page_title="Comparador de Precios Relativos", layout="centered")
st.title("📈 Comparador de Precios Relativos - HereIsData")

# --- Agregar nueva serie manualmente ---
st.sidebar.header("➕ Agregar nueva serie")
nueva_id = st.sidebar.text_input("ID de la serie")
nuevo_nombre = st.sidebar.text_input("Nombre legible")
nueva_unidad = st.sidebar.selectbox("Unidad", ["por kg", "por bulto", "por unidad"])
if st.sidebar.button("Agregar serie"):
    try:
        nueva_id = int(nueva_id)
        if nueva_id and nuevo_nombre:
            SERIES_META[nueva_id] = {"nombre": nuevo_nombre, "unidad": nueva_unidad}
            st.sidebar.success(f"Serie agregada: {nuevo_nombre} ({nueva_unidad})")
    except:
        st.sidebar.error("ID inválido")

# --- Listado y selección ---
nombre_id_map = {f"{v['nombre']} ({v['unidad']})": k for k, v in SERIES_META.items()}
series_nombres = list(nombre_id_map.keys())

serie_a_nombre = st.selectbox("Serie A (numerador)", series_nombres, index=0)
serie_b_nombre = st.selectbox("Serie B (denominador)", series_nombres, index=1)
fecha_desde = st.date_input("Desde", value=date(2025, 7, 16))
fecha_hasta = st.date_input("Hasta", value=date(2025, 8, 16))

# --- Funciones ---
def obtener_datos(series_ids, fecha_inicio, fecha_fin):
    url = "https://hereisdata.com/api/serie/listMeasurementsForMultipleSeries"
    params = {
        "seriesIds": ",".join(map(str, series_ids)),
        "dateFrom": str(fecha_inicio),
        "dateTo": str(fecha_fin)
    }
    headers = {"X-Api-Key": API_KEY}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

def preparar_dataframe(data, series_ids):
    dfs = []
    for i, serie in enumerate(data):
        serie_id = series_ids[i]
        meta = SERIES_META[serie_id]
        nombre = f"{meta['nombre']} ({meta['unidad']})"
        df = pd.DataFrame(serie["measurements"])
        df["date"] = pd.to_datetime(df["date"])
        df = df.rename(columns={"value": nombre})
        dfs.append(df.set_index("date")[nombre])
    return pd.concat(dfs, axis=1).dropna()

def graficar_relacion(df, nombre_a, nombre_b):
    df_rel = df[[nombre_a, nombre_b]].dropna().copy()
    df_rel["precio_relativo"] = df_rel[nombre_a] / df_rel[nombre_b]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_rel.index, df_rel["precio_relativo"], label=f"{nombre_a} / {nombre_b}", color="darkblue")
    ax.axhline(1, linestyle="--", color="gray", linewidth=1)
    ax.set_title("Evolución del Precio Relativo")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Relación de precios")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
    return df_rel

# --- Acción principal ---
if serie_a_nombre != serie_b_nombre:
    ids = [nombre_id_map[serie_a_nombre], nombre_id_map[serie_b_nombre]]
    with st.spinner("Consultando datos..."):
        try:
            datos = obtener_datos(ids, fecha_desde, fecha_hasta)
            df = preparar_dataframe(datos, ids)
            st.subheader(f"{serie_a_nombre} / {serie_b_nombre}")
            df_rel = graficar_relacion(df, serie_a_nombre, serie_b_nombre)
            st.dataframe(df_rel, use_container_width=True)
            st.download_button("📥 Descargar CSV", df_rel.to_csv().encode("utf-8"), file_name="precio_relativo.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Error al consultar o procesar datos: {e}")
else:
    st.warning("Seleccioná dos series distintas para comparar.")
