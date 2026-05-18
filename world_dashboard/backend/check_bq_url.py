import asyncio
from google.cloud import bigquery
import os
import sys

# Ustawiamy ścieżkę do klucza GCP
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/patryk/Repos/architektura-python/world_dashboard/backend/gcp_key.json"

client = bigquery.Client()
target_url = "https://www.aljazeera.com/news/liveblog/2026/5/17/iran-war-live-tehran-eyes-tolls-in-hormuz-trump-warns-of-very-bad-time?update=4578976"

query = f"""
SELECT 
  SOURCEURL,
  NumMentions
FROM `gdelt-bq.gdeltv2.events_partitioned`
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND SOURCEURL = '{target_url}'
"""

print("Odpytuję BigQuery o wskaźniki dla tego konkretnego URL...")
query_job = client.query(query)
results = query_job.result()

rows = list(results)
if not rows:
    print("❌ BigQuery nie zwrócił żadnego rekordu dla tego URL w ciągu ostatnich 24 godzin!")
else:
    print(f"✅ Znaleziono {len(rows)} rekordów w BigQuery:")
    for idx, row in enumerate(rows):
        print(f"Rekord #{idx+1} | NumMentions w GDELT: {row['NumMentions']}")
