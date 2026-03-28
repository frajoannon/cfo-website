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

    # ── Órdenes limpias — una fila por orden ──────────────────────────────────
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
Listo. Vista disponible en BigQuery:
  • {dataset}.shopify_orders_clean

Conéctate desde Looker Studio a esta vista en vez de a la tabla raw.
""")
