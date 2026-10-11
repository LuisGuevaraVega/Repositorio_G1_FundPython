"""Dashboard: ¿el Estado declara emergencia donde más llueve? (lluvias 2022).

Correr en local, desde la carpeta assignment_3/:
    uv run streamlit run app.py
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------- configuracion
st.set_page_config(page_title="Lluvias y emergencias 2022", page_icon="🌧️", layout="wide")

# Rutas a partir de este archivo y no de la carpeta desde donde se ejecuta:
# en Streamlit Cloud la app corre desde la raíz del repo, no desde assignment_3/.
DATOS = Path(__file__).parent / "datos"

COLORES = {"Con declaratoria": "#c0392b", "Sin declaratoria": "#8fa9bf"}
VARIABLES = {
    "Lluvia acumulada (mm)": "lluvia_total_mm",
    "Días con lluvia ≥ 20 mm": "dias_lluvia_fuerte",
}
ETIQUETAS = {
    "lluvia_total_mm": "Lluvia acumulada en la capital, ene–may 2022 (mm)",
    "dias_lluvia_fuerte": "Días con lluvia ≥ 20 mm",
    "departamento": "Departamento",
    "capital": "Capital",
    "declaratoria": "",
    "declaratorias": "Declaratorias",
    "prorrogas": "Prórrogas",
    "puesto_lluvia": "Puesto en lluvia (de 25)",
}


# ------------------------------------------------------------------ carga datos
# @st.cache_data guarda el resultado: sin esto, los archivos se leen otra vez
# cada vez que alguien mueve un filtro.
@st.cache_data
def cargar():
    # ubigeo como texto para no perder el cero a la izquierda ('01' y no 1);
    # utf-8-sig porque el CSV del Assignment 2 se guardó con marca BOM.
    datos = pd.read_csv(DATOS / "dataset.csv", dtype={"ubigeo": str}, encoding="utf-8-sig")
    datos["declaratoria"] = datos["declaratorias"].gt(0).map(
        {True: "Con declaratoria", False: "Sin declaratoria"}
    )
    datos["puesto_lluvia"] = datos["lluvia_total_mm"].rank(ascending=False, method="min").astype(int)

    formas = gpd.read_file(DATOS / "peru_departamental.geojson")
    formas = formas.rename(columns={"FIRST_IDDP": "ubigeo"})[["ubigeo", "geometry"]]
    formas["ubigeo"] = formas["ubigeo"].astype(str)

    # Cruce por ubigeo desde el mapa, para no perder ningún polígono
    mapa = formas.merge(datos, on="ubigeo", how="left", validate="one_to_one", indicator=True)
    no_cruzo = {
        "tabla_sin_mapa": sorted(set(datos["ubigeo"]) - set(formas["ubigeo"])),
        "mapa_sin_tabla": sorted(mapa.loc[mapa["_merge"] != "both", "ubigeo"]),
    }
    mapa = mapa[mapa["_merge"] == "both"].drop(columns="_merge")
    return datos, mapa, no_cruzo


datos, mapa, no_cruzo = cargar()

# Referencias nacionales (los 25 departamentos): no cambian con los filtros
N_TOTAL = len(datos)
N_DECL = int((datos["declaratorias"] > 0).sum())
MED_LLUVIA = datos["lluvia_total_mm"].median()
MED_DIAS = datos["dias_lluvia_fuerte"].median()
PROM_DIAS = datos["dias_lluvia_fuerte"].mean()

# ----------------------------------------------------------------------- filtros
st.sidebar.header("Filtros")

grupo = st.sidebar.selectbox(
    "Declaratoria de emergencia por lluvias",
    ["Todos", "Con declaratoria", "Sin declaratoria"],
)

tope = int(-(-datos["lluvia_total_mm"].max() // 100) * 100)  # máximo redondeado hacia arriba
lluvia_min, lluvia_max = st.sidebar.slider(
    "Lluvia acumulada en la capital (mm)", 0, tope, (0, tope), step=50
)

elegidos = st.sidebar.multiselect(
    "Departamentos (vacío = todos)", sorted(datos["departamento"]),
    placeholder="Elige uno o varios",
)

st.sidebar.divider()
nombre_variable = st.sidebar.selectbox("Variable del mapa", list(VARIABLES))
variable = VARIABLES[nombre_variable]

filtro = datos["lluvia_total_mm"].between(lluvia_min, lluvia_max)
if grupo != "Todos":
    filtro &= datos["declaratoria"] == grupo
if elegidos:
    filtro &= datos["departamento"].isin(elegidos)
filtrado = datos[filtro]

# ------------------------------------------------------------------------ titulo
st.title("🌧️ ¿El Estado declara emergencia donde más llueve?")
st.caption(
    "Temporada de lluvias del 1 de enero al 31 de mayo de 2022, por departamento · "
    "Fuente: Open-Meteo (lluvia diaria en la capital de cada departamento) y gob.pe "
    "(decretos supremos de la PCM). Elaboración propia."
)

# Respuesta con los 25 departamentos; solo se escribe si los datos la confirman
top3 = datos.nsmallest(3, "puesto_lluvia")
lluvia_decl = datos.loc[datos["declaratorias"] > 0, "lluvia_total_mm"]
if (top3["declaratorias"] == 0).all() and (lluvia_decl <= MED_LLUVIA).all():
    a, b, c = top3["departamento"]
    st.info(
        f"**En esta temporada, no.** {a}, {b} y {c} fueron los departamentos más lluviosos y "
        f"ninguno tuvo declaratoria. Los {N_DECL} que sí la tuvieron están en la mediana nacional "
        f"de lluvia ({MED_LLUVIA:,.1f} mm) o por debajo."
    )

if filtrado.empty:
    st.warning("No hay departamentos que cumplan los filtros. Ajusta la selección.")
    st.stop()

con_decl = filtrado[filtrado["declaratorias"] > 0].sort_values("puesto_lluvia")

# ---------------------------------------------------------------------- metricas
med_sel = filtrado["lluvia_total_mm"].median()
prom_dias_sel = filtrado["dias_lluvia_fuerte"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Departamentos", f"{len(filtrado)} de {N_TOTAL}")
# La diferencia con el total del país solo se muestra si hay algún filtro puesto
hay_filtro = len(filtrado) < N_TOTAL
c2.metric(
    "Lluvia mediana (mm)", f"{med_sel:,.1f}",
    delta=f"{med_sel - MED_LLUVIA:+,.1f} vs. los {N_TOTAL}" if hay_filtro else None, delta_color="off",
)
c3.metric(
    "Días de lluvia fuerte (promedio)", f"{prom_dias_sel:.1f}",
    delta=f"{prom_dias_sel - PROM_DIAS:+.1f} vs. los {N_TOTAL}" if hay_filtro else None, delta_color="off",
)
c4.metric("Con declaratoria", f"{len(con_decl)} de {N_DECL}")

st.divider()

# ---------------------------------------------------------------------- graficos
# Los títulos se arman con los datos filtrados, para que digan lo que se ve.
lider = filtrado.loc[filtrado["lluvia_total_mm"].idxmax()]

if con_decl.empty:
    titulo_barras = (
        f"{lider.departamento} es el más lluvioso de la selección "
        f"({lider.lluvia_total_mm:,.1f} mm) y ningún departamento mostrado tuvo declaratoria"
    )
else:
    puestos = ", ".join(f"{r.puesto_lluvia} ({r.departamento})" for r in con_decl.itertuples())
    titulo_barras = (
        f"Con declaratoria (en rojo): puesto{'s' if len(con_decl) > 1 else ''} {puestos} "
        f"de {N_TOTAL} en lluvia acumulada"
    )

if len(filtrado) >= 3 and filtrado["lluvia_total_mm"].std() > 0 and filtrado["dias_lluvia_fuerte"].std() > 0:
    r = filtrado["lluvia_total_mm"].corr(filtrado["dias_lluvia_fuerte"])
    if r > 0.5:
        titulo_disp = f"Donde más llueve hay más días de lluvia fuerte (r = {r:.2f})"
    else:
        titulo_disp = f"En esta selección, la lluvia acumulada y los días de lluvia fuerte van poco juntos (r = {r:.2f})"
else:
    titulo_disp = "Con esta selección no se puede calcular la relación entre las dos medidas de lluvia"

izq, der = st.columns(2)

with izq:
    st.markdown(f"**{titulo_barras}**")
    st.caption("Lluvia acumulada por departamento, de mayor a menor.")
    fig = px.bar(
        filtrado.sort_values("lluvia_total_mm"),
        x="lluvia_total_mm", y="departamento", orientation="h",
        color="declaratoria", color_discrete_map=COLORES,
        text="lluvia_total_mm", hover_name="departamento",
        hover_data={"departamento": False, "capital": True, "dias_lluvia_fuerte": True,
                    "declaratorias": True, "puesto_lluvia": True},
        labels=ETIQUETAS,
    )
    fig.update_traces(texttemplate="%{x:,.1f}", textposition="outside", cliponaxis=False)
    fig.update_yaxes(categoryorder="total ascending", title_text="")
    fig.update_xaxes(range=[0, filtrado["lluvia_total_mm"].max() * 1.15])
    fig.update_layout(
        template="plotly_white", height=max(320, 24 * len(filtrado) + 130),
        margin=dict(l=0, r=10, t=30, b=0),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"),
    )
    st.plotly_chart(fig, width="stretch")

with der:
    st.markdown(f"**{titulo_disp}**")
    st.caption(
        f"Líneas punteadas: medianas de los {N_TOTAL} departamentos "
        f"({MED_LLUVIA:,.1f} mm y {MED_DIAS:.0f} día con lluvia ≥ 20 mm)."
    )
    fig = px.scatter(
        filtrado, x="lluvia_total_mm", y="dias_lluvia_fuerte",
        color="declaratoria", color_discrete_map=COLORES,
        hover_name="departamento",
        hover_data={"capital": True, "declaratorias": True, "declaratoria": False},
        category_orders={"declaratoria": ["Sin declaratoria", "Con declaratoria"]},
        labels=ETIQUETAS,
    )
    fig.update_traces(marker=dict(size=13, line=dict(width=1, color="white")))
    fig.add_vline(x=MED_LLUVIA, line_dash="dot", line_color="gray")
    fig.add_hline(y=MED_DIAS, line_dash="dot", line_color="gray")
    fig.update_layout(
        template="plotly_white", height=max(320, 24 * len(filtrado) + 130),
        margin=dict(l=0, r=10, t=30, b=0),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"),
    )
    st.plotly_chart(fig, width="stretch")

# -------------------------------------------------------------------------- mapa
formas_filtradas = mapa[mapa["ubigeo"].isin(filtrado["ubigeo"])]

lider_nac = datos.loc[datos[variable].idxmax()]
unidad = "mm de lluvia" if variable == "lluvia_total_mm" else "día(s) con lluvia ≥ 20 mm"
if con_decl.empty:
    titulo_mapa = "Ningún departamento de la selección tuvo declaratoria de emergencia por lluvias"
else:
    titulo_mapa = (
        f"Con declaratoria (borde rojo) se llega como máximo a {con_decl[variable].max():,.10g} {unidad}; "
        f"{lider_nac.departamento}, el más alto del país, tuvo {lider_nac[variable]:,.10g}"
    )

st.markdown(f"**{titulo_mapa}**")
st.caption(
    f"{ETIQUETAS[variable]}. Cada departamento se pinta con el dato de una sola ciudad, su capital. "
    "La escala de color es la misma con cualquier filtro."
)

fig = px.choropleth_map(
    formas_filtradas,
    geojson=formas_filtradas.geometry,
    locations=formas_filtradas.index,
    color=variable,
    color_continuous_scale="Blues",
    range_color=(0, datos[variable].max()),
    map_style="carto-positron",
    zoom=4.3,
    center={"lat": -9.2, "lon": -75.0},
    opacity=0.8,
    hover_name="departamento",
    hover_data={"capital": True, "lluvia_total_mm": True, "dias_lluvia_fuerte": True,
                "declaratorias": True, "prorrogas": True},
    labels=ETIQUETAS | {variable: nombre_variable},
    height=600,
)
# Borde rojo y grueso para los departamentos con declaratoria
hay_decl = formas_filtradas["declaratorias"] > 0
fig.update_traces(
    marker_line_color=hay_decl.map({True: COLORES["Con declaratoria"], False: "white"}).tolist(),
    marker_line_width=hay_decl.map({True: 3, False: 0.6}).tolist(),
)
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
# Sin zoom con la rueda del mouse, para que al bajar por la página no se mueva el mapa
st.plotly_chart(fig, width="stretch", config={"scrollZoom": False})

with st.expander("Control del cruce entre la tabla y el mapa"):
    st.write(
        f"El cruce se hace por `ubigeo` leído como texto de 2 dígitos. "
        f"Cruzaron {len(mapa)} de {N_TOTAL} departamentos de la tabla."
    )
    if no_cruzo["tabla_sin_mapa"] or no_cruzo["mapa_sin_tabla"]:
        st.warning(
            f"Ubigeos de la tabla sin polígono: {no_cruzo['tabla_sin_mapa'] or 'ninguno'} · "
            f"Polígonos sin fila en la tabla: {no_cruzo['mapa_sin_tabla'] or 'ninguno'}"
        )
    else:
        st.write("No quedó ningún ubigeo sin cruzar, ni en la tabla ni en el mapa.")

# ------------------------------------------------------------------------- tabla
st.subheader("Datos de los departamentos seleccionados")

columnas = ["puesto_lluvia", "ubigeo", "departamento", "capital", "lluvia_total_mm",
            "dias_lluvia_fuerte", "declaratorias", "prorrogas"]
tabla = filtrado.sort_values("puesto_lluvia")[columnas]

st.dataframe(
    tabla,
    width="stretch",
    hide_index=True,
    column_config={
        "puesto_lluvia": "Puesto en lluvia",
        "ubigeo": "Ubigeo",
        "departamento": "Departamento",
        "capital": "Capital",
        "lluvia_total_mm": st.column_config.NumberColumn("Lluvia acumulada (mm)", format="%.1f"),
        "dias_lluvia_fuerte": "Días con lluvia ≥ 20 mm",
        "declaratorias": "Declaratorias",
        "prorrogas": "Prórrogas",
    },
)

st.download_button(
    "Descargar datos filtrados (CSV)",
    tabla.to_csv(index=False).encode("utf-8-sig"),
    "lluvias_emergencias_filtrado.csv",
    "text/csv",
)

st.caption(
    "Cautela: en la temporada se encontró un solo decreto de lluvias (DS 032-2022-PCM), que cubre a "
    f"{N_DECL} departamentos, y la lluvia es la de una sola ciudad por departamento. El dashboard "
    "describe estos datos; no prueba que el Estado nunca declare emergencia donde más llueve."
)
