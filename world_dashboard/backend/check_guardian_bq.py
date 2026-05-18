import os
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/patryk/Repos/architektura-python/world_dashboard/backend/gcp_key.json"
client = bigquery.Client()

query = """
SELECT 
  SOURCEURL,
  NumMentions
FROM `gdelt-bq.gdeltv2.events_partitioned`
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND SOURCEURL IS NOT NULL
  AND SOURCEURL LIKE '%theguardian.com%'
LIMIT 5
"""

print("Szukam wpisów theguardian.com z ostatnich 24h...")
try:
    query_job = client.query(query)
    rows = list(query_job.result())
    if not rows:
        print("❌ Brak wpisów dla The Guardian!")
    else:
        print("✅ Sukces! Znaleziono adresy The Guardian w GDELT:")
        for r in rows:
            print(f"- Mentions: {r['NumMentions']} | URL: {r['SOURCEURL']}")
except Exception as e:
    print("❌ Błąd:", e)
