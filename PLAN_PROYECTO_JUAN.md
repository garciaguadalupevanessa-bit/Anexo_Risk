# Hoja de Ruta — Persona 4 (Juan)

## 📦 Fase 1: Entorno
- [x] Crear estructura de carpetas `georisk-finder/`
- [x] Verificar paquetes Python instalados

## 📥 Fase 2: Ingesta de muestras reales (4 fuentes)
- [ ] USGS: descargar `all_month.csv` → extraer mag, depth, lat, lon
- [ ] IBTrACS: descargar nrows=5000 → extraer wind, pres, category
- [ ] Smithsonian: WFS → extraer elevation, volcano_type, VEI
- [ ] IGN: descargar catálogo España → extraer mag, depth local
- [ ] Merge en DataFrame unificado (7 columnas físicas)

## 🔬 Fase 3: Preprocesamiento
- [ ] Celda Markdown: justificación de outliers como señal
- [ ] Celda Markdown: justificación de StandardScaler
- [ ] Análisis de skewness con `df.skew()`
- [ ] `np.log1p()` en variables asimétricas
- [ ] `pd.get_dummies()` en categóricas
- [ ] `StandardScaler().fit_transform()`

## 📉 Fase 4: PCA
- [ ] Aplicar PCA sobre matriz escalada
- [ ] Gráfico: varianza explicada acumulada + línea 80-90%
- [ ] Scatter PC1 vs PC2 coloreado
- [ ] Celda Markdown: justificación técnica de PCA

## 🧩 Fase 5: Módulo reutilizable
- [ ] Crear `src/preprocessing.py`
- [ ] Función `pipeline_preprocesamiento_pca()`
- [ ] Verificar que el módulo se ejecuta sin errores

## 🧪 Fase 6: Tests
- [ ] Tests unitarios de log1p, scaler, PCA
- [ ] Test end-to-end del pipeline
- [ ] `pytest tests/ -v` pasa verde

## 🎨 Fase 7: Visualización
- [ ] `src/visualization.py` con gráficos profesionales
- [ ] Plot varianza acumulada guardado en `notebooks/`
- [ ] Scatter PC1 vs PC2 guardado en `notebooks/`
