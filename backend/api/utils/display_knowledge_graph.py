import os
from langchain_community.graphs import Neo4jGraph

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database='neo4j'
)

cypher = """MATCH (u:User {name: "Tanmay"})-[r]-(connected)
RETURN u, r, connected"""

result = kg.query(cypher)
print(result)