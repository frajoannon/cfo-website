"""
Crea vistas SQL en BigQuery para análisis financiero.
Estas vistas limpian y estructuran los datos raw para conectar desde Power BI.
"""

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-credentials.json"

from dotenv import load_dotenv
load_dotenv()

from google.cloud import bigquery

project = os.environ["GCP_PROJECT_ID"]
dataset = os.environ["BQ_DATASET_ID"]

client = bigquery.Client(project=project)

VIEWS = {

    # ── 1. Órdenes limpias ────────────────────────────────────────────────────
    "shopify_orders_clean": f"""
        SELECT
            id,
            DATETIME(created_at, "America/Santiago")            AS fecha,
            DATE(DATETIME(created_at, "America/Santiago"))      AS dia,
            FORMAT_DATETIME("%Y-%m", DATETIME(created_at, "America/Santiago")) AS mes,
            financial_status                                    AS estado_pago,
            fulfillment_status                                  AS estado_envio,
            CAST(total_price AS FLOAT64)                        AS ingreso_bruto,
            CAST(total_discounts AS FLOAT64)                    AS descuentos,
            CAST(total_price AS FLOAT64)
                - CAST(total_discounts AS FLOAT64)              AS ingreso_neto,
            CAST(total_tax AS FLOAT64)                          AS impuestos,
            currency                                            AS moneda,
            customer_email
        FROM `{project}.{dataset}.shopify_orders`
        WHERE financial_status IN ('paid', 'partially_refunded', 'refunded')
    """,

    # ── 2. Ventas diarias ─────────────────────────────────────────────────────
    "shopify_daily_sales": f"""
        SELECT
            dia,
            mes,
            COUNT(*)                        AS num_ordenes,
            SUM(ingreso_bruto)              AS ingreso_bruto,
            SUM(descuentos)                 AS descuentos,
            SUM(ingreso_neto)               AS ingreso_neto,
            AVG(ingreso_neto)               AS ticket_promedio,
            COUNTIF(estado_pago = 'refunded') AS num_devoluciones
        FROM `{project}.{dataset}.shopify_orders_clean`
        GROUP BY dia, mes
        ORDER BY dia DESC
    """,

    # ── 3. Resumen mensual ────────────────────────────────────────────────────
    "shopify_monthly_summary": f"""
        SELECT
            mes,
            COUNT(*)                            AS num_ordenes,
            COUNT(DISTINCT customer_email)      AS clientes_unicos,
            SUM(ingreso_bruto)                  AS ingreso_bruto,
            SUM(descuentos)                     AS descuentos,
            SUM(ingreso_neto)                   AS ingreso_neto,
            AVG(ingreso_neto)                   AS ticket_promedio,
            SUM(ingreso_neto)
                / NULLIF(COUNT(DISTINCT customer_email), 0) AS ingreso_por_cliente,
            COUNTIF(estado_pago = 'refunded')   AS num_devoluciones,
            SUM(CASE WHEN estado_pago = 'refunded'
                THEN ingreso_neto ELSE 0 END)   AS monto_devuelto
        FROM `{project}.{dataset}.shopify_orders_clean`
        GROUP BY mes
        ORDER BY mes DESC
    """,
}


def create_view(name: str, query: str):
    view_ref = f"{project}.{dataset}.{name}"
    view = bigquery.Table(view_ref)
    view.view_query = query.strip()
    try:
        client.delete_table(view_ref, not_found_ok=True)
        client.create_table(view)
        print(f"  ✓ Vista creada: {name}")
    except Exception as e:
        print(f"  ✗ Error en {name}: {e}")


print(f"Creando vistas en {project}.{dataset}...\n")
for name, query in VIEWS.items():
    create_view(name, query)

print(f"""
Listo. Vistas disponibles en BigQuery:
  • {dataset}.shopify_orders_clean
  • {dataset}.shopify_daily_sales
  • {dataset}.shopify_monthly_summary

Conéctate desde Power BI a estas vistas en vez de a las tablas raw.
""")
