# Librerías del frontend (copias locales)

Se guardan en el repositorio para que el observatorio funcione sin internet y sin Node.js.
Cada paquete se bajó del registro oficial de npm y se verificó contra la integridad
`sha512` que publica el propio registro antes de extraer los archivos.

| Paquete | Versión | Archivos | Licencia | Integridad del paquete (npm) |
|---|---|---|---|---|
| vue | 3.5.40 | `vue.esm-browser.prod.js` | MIT (`LICENSE-vue.txt`) | `sha512-+8PJ4SJXdn/cHGImF4CKdxlWHIN5Dkt7DoufRREM6h6uVCx2m7QxgcEQmmzyOK8A9mcafg7sFbJFYsdFVubTig==` |
| echarts | 5.6.0 | `echarts.min.js` | Apache-2.0 (`LICENSE-echarts.txt`, `NOTICE-echarts.txt`) | `sha512-oTbVTsXfKuEhxftHqL5xprgLoc0k7uScAwtryCgWF6hPYFLRwOUHiFmHGCBKP5NPFNkDVopOieyUqYGH8Fa3kA==` |
| leaflet | 1.9.4 | `leaflet/leaflet.js`, `leaflet/leaflet.css`, `leaflet/images/` | BSD-2-Clause (`LICENSE-leaflet.txt`) | `sha512-nxS1ynzJOmOlHp+iL3FyWqK89GtNL8U8rvlMOsQdTTssxZwCXh8N2NB3GDQOL+YR3XnWyZAxwQixURb+FA74PA==` |

Origen de cada paquete: `https://registry.npmjs.org/<paquete>/-/<paquete>-<versión>.tgz`.

Lo único que el navegador pide a internet son los mosaicos del mapa base
(`tile.openstreetmap.org`, sin clave; se muestran en grises con un filtro CSS). Sin
conexión, el mapa sigue mostrando los puntos de las AGEB y de los establecimientos; el
mapa base se puede apagar desde la propia página. Los servidores de OpenStreetMap son
para uso ligero: si el observatorio se publicara con mucho tráfico, habría que usar un
proveedor de mosaicos propio o con clave.
