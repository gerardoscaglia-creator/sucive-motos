# 🏍️ SUCIVE Motos · Inteligencia de Mercado

Dashboard online y **100% automático** de empadronamientos de motos (Cat. C) de Uruguay, por **marca × departamento × mes**. Pensado como herramienta de análisis para dueños/vendedores de motos. Cliente foco: **Rosas (Soriano)**.

**Fuente:** SUCIVE (sucive.gub.uy) — publica solo el mes corriente. Este sistema lo captura cada mes y construye la serie histórica hacia adelante.

## ☁️ Arquitectura (sin servidor, independiente de la PC)
- **GitHub Actions** corre un cron el **día 5 de cada mes**: baja el PDF de SUCIVE, lo parsea y commitea los datos nuevos. (También se dispara a mano desde la pestaña *Actions → Run workflow*.)
- **GitHub Pages** sirve el dashboard online (`index.html`) — se actualiza solo cuando entran datos nuevos.
- Todo vive en el repo. No depende de la PC de Zen.

## 📊 Qué muestra
- **Departamentos:** total de motos por departamento + marca líder + concentración.
- **En Vivo:** ranking de marcas del depto, **Índice de Fuerza Local (IFL)**, concentración (HHI/top-3), segmento económico/media/premium/eléctrica.
- **Análisis de Marca:** share país, ranking, penetración geográfica (en cuántos deptos), plazas fuertes y **mapa de oportunidad** (mercados grandes donde la marca está débil o ausente).
- **Histórico:** se construye mes a mes.

**IFL** = share local de la marca ÷ share país. >1 = la marca pega más fuerte ahí (sobreíndice); <1 = débil (oportunidad).

## 🚀 Deploy (una sola vez)
1. Crear repo en GitHub y subir esta carpeta (`git push`).
2. **Settings → Pages →** Source: *Deploy from a branch* → `main` / `/ (root)`. La URL queda `https://<usuario>.github.io/<repo>/`.
3. **Settings → Actions → General →** Workflow permissions: *Read and write*.
4. Listo. El día 5 de cada mes se actualiza solo. Para forzar: *Actions → Scrape SUCIVE mensual → Run workflow*.

## 🖥️ Uso local (opcional)
- `python serve.py` → http://localhost:3140/index.html
- `python update_mensual.py` → baja y reconstruye datos (= capture.py + build_dataset.py)

## Archivos
| Archivo | Rol |
|---|---|
| `capture.py` | baja el PDF de SUCIVE y parsea marca×depto → `data/AAAA-MM.json` + SQLite |
| `build_dataset.py` | consolida + calcula métricas (share, IFL, HHI, penetración, segmento) → `dataset.json` |
| `index.html` | dashboard (lo sirve GitHub Pages) |
| `.github/workflows/monthly.yml` | cron mensual en la nube |
| `serve.py` | server local para preview |
| `data/`, `pdfs/` | snapshots y PDFs archivados por mes |

## Notas
- Arranca limpio en **2026-05**. La serie histórica se acumula desde acá.
- Segmentación de marcas estimada (económica/media/premium/eléctrica).
- Datos públicos de gobierno, sin PII → repo puede ser público (Pages gratis).
