"""Descarga los microdatos del INEGI que usan los notebooks.

Es el mismo código de la primera celda de los notebooks, como script independiente.
Deja los .zip y las carpetas descomprimidas en data/raw/, que no se versiona
(son ~175 MB comprimidos). Si un archivo ya existe, no lo vuelve a bajar.

Uso, desde cualquier directorio:

    python etl/descargar_datos.py
"""

from pathlib import Path
import shutil
import urllib.request
import zipfile

# Raíz del repo: este script vive en etl/, así que subimos un nivel.
BASE = Path(__file__).resolve().parent.parent
RAW = BASE / 'data' / 'raw'

FUENTES = {
    'denue_09': 'https://www.inegi.org.mx/contenidos/masiva/denue/denue_09_csv.zip',
    'censo_ageb_09': 'https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/ageb_manzana/ageb_mza_urbana_09_cpv2020_csv.zip',
    'enut_2024': 'https://www.inegi.org.mx/contenidos/programas/enut/2024/datosabiertos/conjunto_de_datos_enut_2024_csv.zip',
    'enasic_2022': 'https://www.inegi.org.mx/contenidos/programas/enasic/2022/datosabiertos/conjunto_de_datos_enasic_2022_csv.zip',
}


def descargar(nombre, url):
    """Descarga y descomprime una fuente solo si no existe ya en data/raw."""
    zpath, dpath = RAW / f'{nombre}.zip', RAW / nombre
    if not zpath.exists():
        print(f'Descargando {nombre}...')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r, open(zpath, 'wb') as f:
            shutil.copyfileobj(r, f)
    if not dpath.exists():
        with zipfile.ZipFile(zpath) as z:
            z.extractall(dpath)
    return dpath


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for nombre, url in FUENTES.items():
        dpath = descargar(nombre, url)
        mb = (RAW / f'{nombre}.zip').stat().st_size / 1e6
        print(f'  {nombre:16} {mb:7.1f} MB  ->  {dpath.relative_to(BASE)}')
    print(f'\nListo. Fuentes en {RAW.relative_to(BASE)}/')


if __name__ == '__main__':
    main()
