import yaml
from neo4j import GraphDatabase
from contextlib import contextmanager

_CONFIG_PATH = "./config.yaml"

def _load_creds():
    with open(_CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg["credentials"]

def get_driver():
    """Return an authenticated Neo4j driver for the Aura instance."""
    creds = _load_creds()
    return GraphDatabase.driver(
        creds["uri"],
        auth=(creds["user"], creds["password"])
    )

@contextmanager
def session(database=None):
    """Context manager yielding a Neo4j session. Closes driver on exit."""
    creds = _load_creds()
    driver = get_driver()
    try:
        db = database or creds.get("database", "neo4j")
        with driver.session(database=db) as s:
            yield s
    finally:
        driver.close()

def verify_connection():
    """Return True and print server info if the connection succeeds."""
    try:
        driver = get_driver()
        info = driver.get_server_info()
        print(f"Connected: {info.address}  (agent: {info.agent})")
        driver.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    verify_connection()
