# Assignment 3 – Lluvias y declaratorias de emergencia (2022)

Trabajo del Grupo 1 del curso Fundamentos de Python (Diplomatura QLAB – PUCP).

**Dashboard público:** PENDIENTE – pegar aquí el enlace de Streamlit Cloud (`https://....streamlit.app`)

El dashboard muestra, para los 25 departamentos del Perú, cuánto llovió en la temporada de lluvias de 2022 y cuáles tuvieron declaratoria de emergencia por lluvias. Tiene filtros en la barra lateral (con o sin declaratoria, rango de lluvia y departamentos), cuatro métricas, un gráfico de barras, uno de dispersión, un mapa y la tabla de datos; todo cambia con los filtros.

## 1. ¿Qué pregunta responde?

**¿El Estado declara emergencia donde más llueve?** Es la misma pregunta del Assignment 2. Se compara la lluvia de cada departamento entre el 1 de enero y el 31 de mayo de 2022 con las declaratorias de estado de emergencia por lluvias que dio la PCM en ese periodo.

## 2. ¿De dónde vienen los datos?

`datos/dataset.csv` es la `tabla_final.csv` del Assignment 2, copiada sin cambios (opción B del enunciado). Tiene una fila por departamento (25) y se armó así:

- **Lluvia:** [Open-Meteo, Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api). Lluvia diaria en la ciudad capital de cada departamento. De ahí salen `lluvia_total_mm` (lluvia acumulada) y `dias_lluvia_fuerte` (días con 20 mm o más).
- **Declaratorias:** decretos supremos de la PCM publicados en [gob.pe](https://www.gob.pe/busquedas?contenido=normas), recogidos con scraping. De ahí salen `declaratorias` y `prorrogas`.
- **Cruce:** las dos fuentes se unieron por `ubigeo` del INEI, leído como texto de 2 dígitos (`'01'`, no `1`).
- **Mapa:** `datos/peru_departamental.geojson`, tomado de [juaneladio/peru-geojson](https://github.com/juaneladio/peru-geojson). Cruza con la tabla en 25 de 25 departamentos.

## 3. Dos hallazgos

1. **Los departamentos más lluviosos no tuvieron declaratoria.** Loreto (1,581.8 mm), Ucayali (1,288.8 mm) y Áncash (975.3 mm) encabezan la lluvia acumulada y ninguno tuvo declaratoria. Los 3 que sí la tuvieron quedan en los puestos 13 (Ayacucho, 485.1 mm), 15 (Amazonas, 436.5 mm) y 20 (Piura, 89.2 mm) de 25.
2. **El resultado no depende de cómo se mida la lluvia.** La lluvia acumulada y los días de lluvia fuerte van juntos (r = 0.79), y los departamentos con declaratoria no superan la mediana nacional en ninguna de las dos medidas (485.1 mm y 1 día). En el mapa, lo más lluvioso forma un bloque en la selva (Loreto, Ucayali, Madre de Dios), mientras que las 3 declaratorias están separadas entre sí y fuera de ese bloque.

## 4. Limitaciones

- **Un solo decreto.** En la temporada se encontró un único decreto de lluvias (DS 032-2022-PCM), que cubre a los 3 departamentos. Con 3 casos la comparación es frágil: los datos describen esta temporada y no prueban que el Estado nunca declare emergencia donde más llueve.
- **Una ciudad por departamento.** La lluvia es la de la capital, no la de todo el territorio. Iquitos representa a todo Loreto y Chachapoyas a todo Amazonas; con otra medida (por ejemplo, el promedio de varios puntos del departamento) el orden puede cambiar.
- **Lluvia de un modelo.** Open-Meteo entrega datos de reanálisis, no mediciones de estaciones del SENAMHI.
- **No se miden daños ni vulnerabilidad.** Una declaratoria puede responder a daños, población expuesta o pronósticos, y nada de eso está en la tabla.
- **Geometrías de un repositorio de terceros**, cuya licencia no se verificó.

## Archivos

| Archivo | Contenido |
|---|---|
| `visualizacion.ipynb` | Parte 1: tres gráficos de Plotly y verificación de valores extremos |
| `mapas.ipynb` | Parte 2: cruce por ubigeo, mapas estáticos con Geopandas y mapa Folium |
| `app.py` | Parte 3: dashboard de Streamlit |
| `requirements.txt` | Librerías que necesita el dashboard |
| `grafico.html` | Gráfico de barras exportado en la Parte 1 |
| `datos/` | `dataset.csv` y `peru_departamental.geojson` |

## Correr el dashboard en local

Desde la carpeta `assignment_3/`:

```bash
uv run --with-requirements requirements.txt streamlit run app.py
```

o, con pip:

```bash
pip install -r requirements.txt
streamlit run app.py
```
