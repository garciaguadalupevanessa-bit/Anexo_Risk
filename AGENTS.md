# AGENTS.md

## 1. Identidad del proyecto

**Nombre:** Anexo_Risk

**Propósito:**

Anexo_Risk es una plataforma geoespacial de apoyo a la decisión para organismos y centros de coordinación de emergencias.

El sistema debe ayudar a:

1. detectar y centralizar incidentes;
2. situarlos geográficamente;
3. evaluar impacto y exposición;
4. priorizar incidentes;
5. identificar necesidades;
6. localizar recursos;
7. asignar recursos;
8. realizar seguimiento;
9. apoyar decisiones mediante análisis determinista, ML e IA cuando corresponda.

El producto principal es Anexo_Risk.

El proyecto GeoRisk Finder es una fuente complementaria de ideas, preprocessing, geodata y ML. **No es el producto principal y no debe fusionarse completamente con Anexo_Risk.**

---

# 2. Principio principal

Cada cambio debe responder a esta pregunta:

> **¿Qué problema operacional real resuelve este cambio?**

No añadir una tecnología simplemente porque sea moderna o porque permita afirmar que el proyecto utiliza una determinada herramienta.

Prioridad:

1. datos correctos;
2. seguridad;
3. estabilidad;
4. utilidad operacional;
5. análisis geoespacial;
6. explicabilidad;
7. ML;
8. IA generativa;
9. UX;
10. estética.

---

# 3. Arquitectura principal

Mantener:

### Frontend

* Vanilla JavaScript
* ES Modules
* HTML
* CSS
* Leaflet

### Backend

* Python
* FastAPI
* Pydantic

### Persistencia

* SQLite actualmente.

No migrar a otra base de datos salvo necesidad demostrada.

### Análisis

* NumPy
* pandas
* GeoPandas
* Shapely
* H3
* scikit-learn

Sólo utilizar cada dependencia dentro del módulo donde aporte valor.

---

# 4. Prohibiciones

No hacer:

* migración global a React;
* migración a Vue/Svelte;
* reescritura completa;
* microservicios innecesarios;
* introducir LangChain sin necesidad;
* introducir LLM sin tools reales;
* inventar APIs;
* inventar datos;
* inventar coordenadas;
* inventar severidades;
* inventar población;
* inventar recursos;
* presentar datos sintéticos como reales;
* copiar secretos desde otro repositorio;
* reutilizar autenticación insegura de GeoRisk Finder;
* reutilizar datos financieros sintéticos;
* reutilizar WebSocket stub como si fuera funcional;
* eliminar tests para hacer pasar una fase;
* romper contratos existentes deliberadamente.

---

# 5. Regla de reutilización de GeoRisk Finder

GeoRisk Finder puede aportar:

* preprocessing;
* patrones de adapters;
* USGS;
* IBTrACS;
* volcanes;
* H3;
* PCA;
* clustering;
* scikit-learn;
* MLflow como referencia;
* concepto de Decision Center.

No copiar directamente:

* React;
* Zustand;
* deck.gl;
* autenticación demo;
* secret keys;
* almacenamiento exclusivamente basado en CSV/pickle;
* datos sintéticos;
* componentes no probados;
* deuda técnica conocida.

Todo código reutilizado debe adaptarse a:

* la arquitectura de Anexo_Risk;
* sus contratos;
* su seguridad;
* sus tests.

---

# 6. Modelo operacional

El modelo principal es:

```text
INCIDENTE
    ↓
CONTEXTO
    ↓
EXPOSICIÓN
    ↓
RIESGO
    ↓
PRIORIZACIÓN
    ↓
NECESIDAD
    ↓
RECURSO
    ↓
ASIGNACIÓN
    ↓
SEGUIMIENTO
    ↓
RESOLUCIÓN
```

El usuario principal del sistema es un operador o coordinador de emergencias.

Roles conceptuales:

* operador;
* coordinador de recursos;
* analista;
* administrador.

Clientes institucionales potenciales:

* ayuntamiento;
* centro de coordinación;
* Protección Civil;
* organismo autonómico;
* servicios de emergencias;
* otras organizaciones de respuesta.

---

# 7. Modelo de datos

Cuando sea necesario crear nuevas entidades, preferir modelos explícitos.

Entidades clave:

* Incident
* Alert
* Need
* Resource
* Organization
* OperationalUser
* Assignment
* RiskAssessment
* SpatialCell
* ModelVersion
* Prediction
* TimelineEvent

Cada entidad debe tener identificadores estables y timestamps adecuados.

---

# 8. Fuentes de datos

Fuentes actualmente integradas o planificadas:

* GDACS
* NASA FIRMS
* AEMET
* Open-Meteo
* USGS
* IBTrACS
* Smithsonian/GVP
* Copernicus/EFFIS
* fuentes de exposición que sean realmente accesibles.

Cada fuente debe tener adapter propio.

Preferir:

```text
Fuente
 ↓
Adapter
 ↓
Normalización
 ↓
Dominio
 ↓
Persistencia/cache
 ↓
API
 ↓
Frontend
```

No hacer que componentes del frontend conozcan directamente el formato de proveedores externos.

---

# 9. Datos reales frente a datos derivados

Distinguir siempre:

### Dato externo

Procede directamente de una fuente.

### Dato normalizado

Transformación semántica del dato externo.

### Dato calculado

Derivado mediante reglas o análisis geoespacial.

### Predicción ML

Salida del modelo.

### Generación IA

Texto generado usando datos consultados.

Cada categoría debe poder distinguirse internamente.

---

# 10. Risk Engine

El Risk Engine determinista es obligatorio como baseline.

Debe ser:

* explicable;
* reproducible;
* versionado;
* trazable.

No llamar "predicción" a un score que proviene únicamente de reglas.

Preferir:

> índice de prioridad operacional.

El resultado debe incluir:

```text
score
level
methodology_version
generated_at
factors
```

---

# 11. Machine Learning

El ML debe ser real y evaluado.

Actualmente existe un GradientBoostingClassifier.

Cualquier evolución debe comprobar:

* dataset;
* target;
* features;
* train/test split;
* leakage;
* balance de clases;
* baseline;
* métricas;
* reproducibilidad;
* versión del modelo.

IMPORTANTE:

Si el target está generado por las reglas del Risk Engine, reconocer que el modelo está aprendiendo el scoring etiquetado y NO presentarlo como predicción validada de resultados reales.

Cuando exista suficiente histórico, priorizar targets observados:

* escalada;
* resolución;
* aparición de necesidades;
* impacto observado;
* etc.

---

# 12. ML explainability

Toda predicción debe tener una explicación.

No mostrar únicamente:

> 0.86

Mostrar:

> Riesgo alto
> Principales factores: necesidades abiertas, densidad de eventos y magnitud.

La explicación nunca debe exagerar causalidad.

Feature importance no implica causalidad.

---

# 13. IA generativa

La IA generativa se utiliza sólo para:

* consultar;
* resumir;
* explicar;
* navegar información existente.

Antes de introducir un agente LLM deben existir tools backend estables:

* get_alerts;
* get_incidents;
* get_needs;
* get_resources;
* get_nearby_resources;
* get_weather;
* get_exposure;
* get_risk;
* get_timeline.

La IA nunca puede inventar información operacional.

---

# 14. LangChain

No es obligatorio.

Sólo introducir LangChain/LangGraph si existe una necesidad real de:

* orquestación;
* RAG;
* múltiples tools;
* workflows complejos;
* memoria controlada;
* observabilidad.

Si tool calling directo es suficiente:

**No utilizar LangChain.**

---

# 15. Geospatial

GeoPandas y Shapely se utilizarán para:

* spatial joins;
* proximidad;
* buffers;
* intersección;
* exposición;
* análisis territorial.

H3 puede utilizarse para:

* agregación;
* ranking;
* densidad;
* comparación espacial;
* clustering.

No obligar a toda la aplicación a trabajar exclusivamente con H3.

---

# 16. Copernicus

Copernicus sólo puede incorporarse mediante servicios o datasets realmente accesibles.

Prioridad:

1. EFFIS;
2. exposure;
3. otros servicios sólo cuando estén técnicamente justificados.

No inventar endpoints.

Documentar restricciones de acceso.

Preferir servicios estándar como WMS/WFS cuando sean adecuados.

---

# 17. Offline

Offline significa:

> trabajar con el último estado conocido.

No significa que APIs externas continúen funcionando sin conexión.

La aplicación debe poder indicar:

* online;
* offline;
* stale;
* syncing;
* sync error.

La última sincronización debe ser visible.

---

# 18. Seguridad

No aceptar:

* XSS;
* SQL injection;
* path traversal;
* secret leakage;
* errores con información sensible;
* SSRF;
* coordenadas inválidas;
* parámetros sin límites.

Todo input externo debe considerarse no confiable.

Todo secreto debe permanecer fuera del repositorio.

---

# 19. Tests

No considerar una fase terminada sólo porque el código compila.

Debe existir:

* test unitario;
* test de integración cuando corresponda;
* test de API;
* test de seguridad para riesgos relevantes;
* test de frontend cuando exista comportamiento nuevo.

No eliminar tests para resolver regresiones.

---

# 20. Cambios de base de datos

Todas las migraciones deben ser:

* ordenadas;
* idempotentes;
* reversibles cuando sea razonable;
* compatibles con datos existentes.

Después de una migración:

1. base limpia;
2. base existente;
3. tests;
4. endpoints.

---

# 21. Observabilidad

Los adapters externos deben tener:

* timeout;
* manejo de errores;
* logging útil;
* cache cuando proceda;
* timestamp;
* estado de fuente.

No ocultar fallos.

---

# 22. Frontend

El frontend debe consumir el dominio normalizado.

No duplicar lógica de negocio entre componentes.

El mapa debe ser el centro operativo.

No cargar todas las capas simultáneamente si perjudica la UX.

Usar progressive disclosure.

---

# 23. Definition of Done

Una funcionalidad sólo está terminada cuando:

1. existe implementación;
2. está integrada;
3. tiene tests;
4. no rompe contratos;
5. tiene manejo de errores;
6. tiene documentación;
7. puede demostrarse;
8. no introduce datos ficticios;
9. tiene una explicación de por qué existe.

---

# 24. Prioridad del producto

La principal vertical slice es:

```text
EVENTO REAL
 ↓
MAPA
 ↓
DECISION CENTER
 ↓
EXPOSICIÓN
 ↓
RISK SCORE
 ↓
EXPLICACIÓN
 ↓
NECESIDAD
 ↓
RECURSO
 ↓
ASIGNACIÓN
 ↓
SEGUIMIENTO
```

Toda nueva funcionalidad debe mejorar esta vertical slice o una capacidad claramente necesaria para ella.

---

# 25. Regla contra sobreingeniería

Antes de añadir una tecnología:

1. identificar problema;
2. comprobar si la arquitectura actual lo resuelve;
3. evaluar coste;
4. evaluar dependencia;
5. evaluar mantenimiento;
6. justificar beneficio.

Si no existe un beneficio claro:

**no añadir la tecnología.**

---

# 26. Comunicación del agente

Cuando termine una fase debe informar:

* qué cambió;
* qué archivos;
* qué tests;
* qué limitaciones;
* qué quedó pendiente.

No afirmar "production ready" si quedan problemas importantes.

Usar:

> MVP funcional
> Ready for demo
> Known limitations

cuando corresponda.

# FIN DE AGENTS.md
