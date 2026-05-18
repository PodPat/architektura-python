import os
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/patryk/Repos/architektura-python/world_dashboard/backend/gcp_key.json"
client = bigquery.Client()

# Zapytanie z LOWER() i testem dla Reuters / Politico
query = """
SELECT 
  'axios.com' as domain,
  COUNT(*) as count
FROM `gdelt-bq.gdeltv2.events_partitioned`
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND LOWER(SOURCEURL) LIKE '%axios.com%'

UNION ALL

SELECT 
  'reuters.com' as domain,
  COUNT(*) as count
FROM `gdelt-bq.gdeltv2.events_partitioned`
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND LOWER(SOURCEURL) LIKE '%reuters.com%'

UNION ALL

SELECT 
  'politico.com' as domain,
  COUNT(*) as count
FROM `gdelt-bq.gdeltv2.events_partitioned`
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND LOWER(SOURCEURL) LIKE '%politico.com%'
"""

print("Sprawdzam statystyki domen w BigQuery...")
try:
    query_job = client.query(query)
    rows = list(query_job.result())
    for row in rows:
        print(f"Domena: {row['domain']} | Liczba zdarzeń w GDELT (ostatnie 24h): {row['count']}")
except Exception as e:
    print("❌ Błąd:", e)
