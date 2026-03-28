# Guía de Conexiones a Fuentes de Datos

Referencia para integrar nuevos clientes al pipeline ETL.
Cada sección explica qué credenciales se necesitan, dónde obtenerlas y cómo configurarlas.

---

## 1. Shopify

### Qué extrae
- Órdenes (`shopify_orders`)
- Productos (`shopify_products`)

### Credenciales necesarias
| Variable | Descripción | Ejemplo |
|---|---|---|
| `SHOPIFY_SHOP_DOMAIN` | Dominio de la tienda | `mi-tienda.myshopify.com` |
| `SHOPIFY_ACCESS_TOKEN` | Token de acceso privado | `shpat_xxxxxxxxxxxx` |

### Cómo obtener las credenciales

1. Entra al panel de administración de Shopify → **Settings** → **Apps and sales channels**
2. Click en **Build apps in dev dashboard**
3. Click en **Create an app** → ponle un nombre (ej: `CFO Pipeline`)
4. Ve a **Configuration** → **Admin API integration** → **Configure**
5. Activa los permisos:
   - `read_orders`
   - `read_products`
   - `read_customers`
6. Click **Save**
7. Ve a la pestaña **API credentials** → click en **Install app** → confirmar
8. Copia el **Admin API access token** (`shpat_...`) — solo se muestra una vez
9. El dominio está en la barra del navegador: `tu-tienda.myshopify.com`

### Autenticación
La API usa el token directamente en el header de cada request:
```
X-Shopify-Access-Token: {SHOPIFY_ACCESS_TOKEN}
```

### Paginación
Shopify usa **cursor-based pagination**. Cada respuesta incluye un header `Link` con la URL de la página siguiente. El extractor sigue automáticamente hasta agotar los registros.

### Notas
- La carga histórica trae todas las órdenes desde el inicio de la tienda
- Las cargas diarias traen solo las órdenes nuevas desde la última ejecución
- El campo `raw_json` guarda el JSON completo original por si se necesitan campos adicionales en el futuro

---

## 2. Chipax

### Qué extrae
| Tabla | Descripción |
|---|---|
| `chipax_compras` | Facturas de compra |
| `chipax_dtes` | Documentos tributarios electrónicos |
| `chipax_gastos` | Gastos registrados |
| `chipax_remuneraciones` | Liquidaciones de sueldo |
| `chipax_honorarios` | Boletas de honorarios |
| `chipax_cuentas` | Cuentas contables |
| `chipax_cuentas_corrientes` | Cuentas bancarias |
| `chipax_movimientos` | Movimientos bancarios |

### Credenciales necesarias
| Variable | Descripción |
|---|---|
| `CHIPAX_APP_ID` | ID de la aplicación |
| `CHIPAX_SECRET_KEY` | Clave secreta |

### Cómo obtener las credenciales

1. Inicia sesión en `https://app.chipax.com`
2. Ve a **Configuración** → **API** (o directo a `https://app.chipax.com/secret_keys`)
3. Genera nuevas credenciales — se obtienen `app_id` y `secret_key`
4. **Importante:** se necesita perfil de administrador para acceder a esta sección

### Autenticación
Chipax usa autenticación JWT en dos pasos:

**Paso 1** — Obtener el token haciendo POST a `/login`:
```
POST https://api.chipax.com/v2/login
Body: { "app_id": "...", "secret_key": "..." }
Respuesta: { "token": "eyJ...", "tokenExpiration": "..." }
```

**Paso 2** — Usar el token en cada request:
```
Authorization: JWT {token}
```

### Paginación
Chipax usa **offset pagination**. Cada respuesta incluye:
```json
{
  "items": [...],
  "paginationAttributes": {
    "count": 1472,
    "totalPages": 30,
    "currentPage": 1
  }
}
```
El extractor itera automáticamente todas las páginas y deduplica por `id` al final.

### Notas
- El token JWT expira — el extractor lo renueva automáticamente en cada ejecución
- La deduplicación por `id` evita registros repetidos cuando la API rellena la última página
- `chipax_cartolas` puede estar vacía si no hay movimientos en el período consultado

---

## Cómo agregar un nuevo cliente

1. **Obtener credenciales** siguiendo esta guía
2. **Agregar al `.env`** local:
```
SHOPIFY_SHOP_DOMAIN=nueva-tienda.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_...
CHIPAX_APP_ID=...
CHIPAX_SECRET_KEY=...
BQ_DATASET_ID=raw_nombrecliente
GCP_PROJECT_ID=cfo-as-a-service-490915
```
3. **Agregar los secrets en GitHub Actions** con los mismos nombres
4. **Correr el pipeline** manualmente la primera vez para cargar el historial
5. **Verificar** con la query de conteo en BigQuery

---

*Última actualización: Marzo 2026*
