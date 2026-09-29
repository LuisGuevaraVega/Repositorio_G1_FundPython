# Bitácora de IA – Assignment 2

**Grupo 1 · Temporada 2022 (1 de enero al 31 de mayo)**

**Herramienta usada:** Claude Code (modelo Claude Opus 5.5), dentro de VS Code, con el environment de conda `webscraping`.

**Pedido general que se le hizo a la IA para la Parte 1:**

> "necesito hacer una tarea sobre scraping de lluvias. Quiero que sigas las instrucciones de este issue de un repositorio. Necesto que sigas al pie de la letra sobre lo que dice la parte 1– Scraping de decretos de emergencia, solo quiero que hagas esa parte. Usa el enviroment que tengo guardado en visual studio code como "web scraping".
> link del issue: https://github.com/alexanderquispe/Diplomado_PUCP/issues/1881"

A partir de ese pedido, la IA fue armando el código paso por paso. Abajo se registran los momentos en que lo que propuso estaba **mal, incompleto o no funcionó**, cómo se detectó y cómo se corrigió.

---

## Entrada 1 – Parte 1: pasar de página con el botón "Siguiente"

### 1. ¿Qué le pidieron a la IA?

Dentro del pedido general, la IA tenía que recorrer **todos** los resultados de la búsqueda de gob.pe con Selenium (pasos 2 a 5 del enunciado). Como la página muestra como máximo 25 resultados, la IA propuso una forma de pasar a las páginas siguientes.

### 2. ¿Qué les respondió?

La IA propuso hacer clic en el botón "Siguiente página" hasta que se desactivara, y lo probó con la búsqueda de toda la temporada (29 resultados):

```python
while True:
    bs = d.find_elements(By.CSS_SELECTOR, "button[aria-label='Siguiente página']")
    if not bs or not bs[0].is_enabled(): break
    primero = d.find_element(By.TAG_NAME, "article")
    time.sleep(2)
    bs[0].click()
    w.until(EC.staleness_of(primero))
    w.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
    print("url tras click:", d.current_url)
```

### 3. ¿Qué estaba mal y cómo se dieron cuenta?

Con 29 resultados y 25 por página solo debían existir **2 páginas**. Sin embargo, el código siguió avanzando sin parar. La prueba no terminó en 4 minutos y la URL impresa después de cada clic mostraba esto:

```text
h2: 29 Resultados 25
url tras click: https://www.gob.pe/busquedas?contenido=normas&desde=01-01-2022&hasta=31-05-2022&sheet=2&sort_by=recent&term=estado%20de%20emergencia%20precipitaciones
pag arts: 25
url tras click: https://www.gob.pe/busquedas?contenido=normas&...&sheet=3&...
...
url tras click: https://www.gob.pe/busquedas?contenido=normas&...&sheet=42&...
```

Al comparar esa URL con la original se vieron **dos problemas**:

- Al pasar de página, la URL **pierde el filtro `institucion[]=pcm`**, así que el código estaba recorriendo normas de todas las instituciones del Estado.
- La página siguiente usa el parámetro **`sheet=`**, y el `robots.txt` de gob.pe lo prohíbe expresamente (`Disallow: /*?sheet=` y `Disallow: /*&sheet=`). Es decir, la paginación del buscador es justamente lo que el sitio no quiere que recorran los bots.

### 4. ¿Cómo lo corrigieron?

- Se detuvo el proceso y se descartó por completo la paginación con el botón "Siguiente".
- Se buscó **mes por mes**, como pide el enunciado. En 2022 ningún mes pasa de 8 resultados, así que todo entra en la primera página y nunca se usa `sheet=`.
- La tabla de verificación del paso 6 (`resultados_totales` vs. `resultados_extraidos`) avisaría si algún mes tuviera más de 25 resultados.
- Se explicó en la celda de texto del paso 1 del notebook por qué no se pasa de página.

---

## Entrada 2 – Parte 1: `robotparser` dice que una URL prohibida está permitida

### 1. ¿Qué le pidieron a la IA?

Paso 1 del enunciado: descargar el `robots.txt` de gob.pe, explicar qué prohíbe y comprobar si la página de búsquedas (`/busquedas`) está permitida.

### 2. ¿Qué les respondió?

La IA usó el lector de `robots.txt` de la librería estándar de Python (`urllib.robotparser`) para comprobar los permisos:

```python
rp = robotparser.RobotFileParser()
rp.parse(t.splitlines())
print(rp.can_fetch('*', u),                            # búsqueda normal
      rp.can_fetch('*', 'https://www.gob.pe/admin/'),  # /admin/
      rp.can_fetch('*', u + '&sheet=2'),               # búsqueda con sheet=
      ...)
```

Resultado:

```text
True False True False 5 2 None
```

### 3. ¿Qué estaba mal y cómo se dieron cuenta?

El tercer valor dice `True`, es decir, que una URL con `&sheet=2` **está permitida**. Pero el `robots.txt` impreso dice claramente `Disallow: /*&sheet=`. Al comparar el resultado con el texto del archivo se vio la contradicción. La causa es que `urllib.robotparser` **no entiende el comodín `*` dentro de las rutas**: solo revisa si la URL empieza con la ruta escrita, y toma el `*` como un carácter literal. Por eso esa regla nunca se aplica.

Si se hubiera confiado solo en `robotparser`, la conclusión del paso 1 habría estado mal y se habría usado la paginación prohibida (ver Entrada 1).

### 4. ¿Cómo lo corrigieron?

- En el notebook se sigue usando `robotparser` solo para lo que sí resuelve bien: `/busquedas` permitido, `/admin/` prohibido y los `Crawl-delay` de GPTBot (5) y OAI-SearchBot (2).
- La regla de `sheet=` se revisa **a mano**, con `"sheet=" in url_ejemplo`.
- En la celda de texto del paso 1 se aclara que `robotparser` no entiende el comodín `*`.

---

## Entrada 3 – Parte 1: la espera de Selenium falla cuando no hay resultados

### 1. ¿Qué le pidieron a la IA?

Paso 2 del enunciado: abrir la búsqueda con Selenium usando `WebDriverWait` (no solo `time.sleep()`). Después, para comprobar que el resultado del paso 11 no era un error, se usó la misma función para buscar otros términos (`precipitaciones` y `lluvias`).

### 2. ¿Qué les respondió?

La primera versión de la función esperaba siempre a que apareciera el contador "N Resultados":

```python
def abrir_busqueda(desde, hasta, url_base=URL_BASE):
    url = url_base + f"&desde={desde}&hasta={hasta}"
    driver.get(url)
    # Esperamos hasta que el contador "N Resultados" aparezca en la página
    espera.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "h2[role='status']"), "Resultado"))
    if leer_total() > 0:
        espera.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
    return url


def leer_total():
    texto = driver.find_element(By.CSS_SELECTOR, "h2[role='status'] span").text
    return int(re.sub(r"\D", "", texto))
```

### 3. ¿Qué estaba mal y cómo se dieron cuenta?

Al ejecutar el notebook completo, la celda que busca `lluvias` se detuvo con este error después de 30 segundos:

```text
ERROR TimeoutException Message:
Stacktrace:
	msedgedriver!GetHandleVerifier [0x7ff70d76fd45+4c15]
	...
```

Al abrir esa página se vio que, cuando una búsqueda **no tiene resultados**, gob.pe no muestra el contador "0 Resultados". En su lugar muestra otro título, `<h2>No se encontraron resultados para "lluvias"</h2>`, sin `role="status"`. La función esperaba algo que nunca iba a aparecer.

Además, el error no afectaba solo a esa celda: si algún mes de la temporada no tuviera ningún decreto, el recorrido mes por mes (paso 5) también se habría caído. En 2022 no pasó porque todos los meses tienen resultados, pero en otra temporada sí podría pasar.

### 4. ¿Cómo lo corrigieron?

Ahora la espera acepta cualquiera de los dos casos, y `leer_total()` devuelve 0 cuando no hay contador:

```python
espera.until(EC.any_of(
    EC.text_to_be_present_in_element((By.CSS_SELECTOR, "h2[role='status']"), "Resultado"),
    EC.text_to_be_present_in_element((By.CSS_SELECTOR, "main h2"), "No se encontraron"),
))


def leer_total():
    contador = driver.find_elements(By.CSS_SELECTOR, "h2[role='status'] span")
    if not contador:   # la página dice "No se encontraron resultados"
        return 0
    return int(re.sub(r"\D", "", contador[0].text))
```

Con esta corrección el notebook volvió a correr de principio a fin, y la verificación mostró `term='lluvias': 0 resultado(s)`.

---

## Entrada 4 – Parte 1: la verificación de departamentos salió vacía

### 1. ¿Qué le pidieron a la IA?

Paso 12 del enunciado: identificar qué departamentos menciona cada decreto y "explicar **con un ejemplo de su temporada** cómo evitaron contar mal" (el problema de `ica` dentro de `huancavelica` y de Ica como provincia y como departamento).

### 2. ¿Qué les respondió?

La IA escribió una celda que compara el método correcto (`re.search(r"\b" + departamento + r"\b", titulo)`) con el método ingenuo (`departamento.lower() in titulo.lower()`), pero **solo sobre los decretos de lluvias**:

```python
diferencias = []
for _, fila in lluvias.iterrows():
    ingenuo = departamentos_ingenuo(fila["titulo"])
    sobran = [d for d in ingenuo if d not in fila["departamentos"]]
    ...
pd.DataFrame(diferencias)
```

Resultado:

```text
Empty DataFrame
Columns: []
Index: []
```

### 3. ¿Qué estaba mal y cómo se dieron cuenta?

La tabla salió **vacía**. En 2022 solo hay **un** decreto de lluvias, el DS 032-2022-PCM, que menciona Amazonas, Ayacucho y Piura una vez cada uno y no tiene ninguna trampa. Así, la celda no mostraba ningún ejemplo, y el enunciado pide explícitamente un ejemplo de la temporada. La respuesta de la IA estaba **incompleta**: el código funcionaba, pero no cumplía lo que se pedía.

### 4. ¿Cómo lo corrigieron?

La misma comparación se aplicó a **las 29 normas de la PCM de la temporada** (no solo a las de lluvias), y ahí sí aparecieron casos reales de 2022:

- **DS 013-2022-PCM:** con el método ingenuo aparece **Ica**, porque `"ica"` está dentro de "Huancavel**ica**". Además, "Cusco" aparece **dos veces** en el título y se cuenta una sola vez.
- **DS 002, 005, 010, 011, 015 y 030-2022-PCM:** con el método ingenuo aparece **Ica** porque `"ica"` está dentro de "modif**ica**". En la resolución 003-2022-PCM/SGP pasa lo mismo con "Públ**ica**".
- **DS 006 y 055-2022-PCM:** "Madre de Dios" aparece como **distrito** y como **departamento**, igual que el caso de "provincia de Ica del departamento de Ica". Se cuenta una sola vez.

Con esos ejemplos se escribió la explicación del paso 12 en el notebook. Además se agregó una prueba directa con la frase `"provincia de Ica del departamento de Ica"`, que devuelve `['Ica']` una sola vez.

---

## Entrada 5 – Parte 2: API de lluvias

> **PENDIENTE:** completar cuando se haga la Parte 2 (`api_lluvias.ipynb`). El enunciado exige al menos **una entrada de la Parte 2**. Debe describir un error real que haya ocurrido al trabajar con la IA en esa parte.

### 1. ¿Qué le pidieron a la IA?

_(completar)_

### 2. ¿Qué les respondió?

_(completar: copiar la parte relevante del código o de la respuesta)_

### 3. ¿Qué estaba mal y cómo se dieron cuenta?

_(completar)_

### 4. ¿Cómo lo corrigieron?

_(completar)_
