import os
import socket
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv(".env")

uri = os.getenv("NEO4J_URI", "")
username = os.getenv("NEO4J_USERNAME", "")
password = os.getenv("NEO4J_PASSWORD", "")
database = os.getenv("NEO4J_DATABASE", "")

print("NexusTrace Neo4j diagnostics")
print("-" * 30)
print(f"URI set: {bool(uri)}")
print(f"Username set: {bool(username)}")
print(f"Password set: {bool(password)}")
print(f"Database set: {bool(database)}")

if username and username != "neo4j":
    print("FAIL: NEO4J_USERNAME should normally be 'neo4j', not the Aura instance ID.")
    sys.exit(2)

if database and database != "neo4j":
    print("FAIL: NEO4J_DATABASE should normally be 'neo4j', not the Aura instance ID.")
    sys.exit(2)

if not uri or uri.startswith("replace-"):
    print("FAIL: NEO4J_URI is missing or still a placeholder")
    sys.exit(2)

parsed = urlparse(uri)
host = parsed.hostname
if not host:
    print("FAIL: NEO4J_URI does not contain a valid hostname")
    sys.exit(2)

print(f"URI scheme: {uri.split(':', 1)[0]}")
print(f"Hostname resolves: {bool(host)}")

try:
    address = socket.gethostbyname(host)
    print(f"DNS resolved to: {address}")
except OSError as exc:
    print(f"FAIL: DNS resolution failed: {exc}")
    sys.exit(2)

try:
    connection = socket.create_connection((host, 7687), timeout=8)
    connection.close()
    print("TCP port 7687: reachable")
except OSError as exc:
    print(f"FAIL: TCP port 7687 is blocked or unreachable: {exc}")
    print("Check VPN, proxy, antivirus, Windows Firewall, and network policy.")
    sys.exit(3)

if not password:
    print("FAIL: NEO4J_PASSWORD is missing")
    sys.exit(2)

try:
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    with driver.session(database=database or "neo4j") as session:
        session.run("RETURN 1 AS ok").single()
    driver.close()
    print("PASS: Aura connectivity and authentication succeeded")
except Exception as exc:
    error = type(exc).__name__
    print(f"FAIL: Aura connection failed ({error})")
    print(f"Driver message: {str(exc)}")
    sys.exit(4)
