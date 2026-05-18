import os
from google.cloud import bigquery
from datetime import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/patryk/Repos/architektura-python/world_dashboard/backend/gcp_key.json"
client = bigquery.Client()

# Pobieramy dokładnie tak, jak w services.py, sprawdzając co ląduje w wynikach
query = """
SELECT 
  SOURCEURL,
  NumMentions
FROM `gdelt-bq.gdeltv2.events_partitioned`
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND SOURCEURL IS NOT NULL
  AND NumMentions >= 5
  AND (
    SOURCEURL LIKE '%axios.com%' 
    OR SOURCEURL LIKE '%reuters.com%' 
    OR SOURCEURL LIKE '%politico.com%'
  )
ORDER BY NumMentions DESC
LIMIT 50
"""

print("Uruchamiam identyczne zapytanie jak w głównym systemie...")
try:
    query_job = client.query(query)
    rows = list(query_job.result())
    if not rows:
        print("❌ Brak wyników!")
    else:
        print(f"✅ BigQuery zwrócił {len(rows)} rekordów:")
        for idx, row in enumerate(rows):
            print(f"#{idx+1} | Mentions: {row['NumMentions']} | URL: {row['SOURCEURL']}")
except Exception as e:
    print("❌ Błąd:", e)
