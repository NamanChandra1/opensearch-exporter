from prometheus_client import start_http_server, Gauge
import requests
import time
import os
import re
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL",)
USERNAME = os.getenv("OPENSEARCH_USER", "admin")
PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "admin")
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", 60)) 
index_document_count = Gauge("opensearch_index_document_count", "Document count per index", ["index"])
index_storage_size = Gauge("opensearch_index_storage_size", "Storage size per index in bytes", ["index"])
index_primary_shards = Gauge("opensearch_index_primary_shards", "Primary shards per index", ["index"])
index_replica_shards = Gauge("opensearch_index_replica_shards", "Replica shards per index", ["index"])
def fetch_index_stats():
    """Fetch index stats from OpenSearch."""
    try:
        response = requests.get(f"{OPENSEARCH_URL}/_cat/indices?v&format=json", auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching index stats: {e}")
        return []
def update_metrics():
    """Update Prometheus metrics with the latest index stats."""
    index_stats = fetch_index_stats()
    for index in index_stats:
        index_name = index["index"]
        index_document_count.labels(index=index_name).set(index.get("docs.count", 0))
        index_storage_size.labels(index=index_name).set(parse_size(index.get("store.size", "0b")))
        index_primary_shards.labels(index=index_name).set(index.get("pri", 0))
        index_replica_shards.labels(index=index_name).set(index.get("rep", 0))
def parse_size(size_str):
    """Convert size from OpenSearch format (e.g., '5mb', '23.8k') to gigabytes."""
    size_units = {
        "b": 1 / 1024**3,    # bytes to GB
        "kb": 1 / 1024**2,   
        "mb": 1 / 1024,      
        "gb": 1,             
        "tb": 1024           
    }
    size_str = size_str.lower().strip()
    # Extract the numeric part and unit using regex
    match = re.match(r"([\d.]+)([a-z]+)", size_str)
    if match:
        size_value, unit = match.groups()
        return float(size_value) * size_units.get(unit, 1)  # GB
    return 0
if __name__ == "__main__":
    start_http_server(8000)
    print("Prometheus metrics server started on port 8000")
    while True:
        update_metrics()
        time.sleep(SCRAPE_INTERVAL)
