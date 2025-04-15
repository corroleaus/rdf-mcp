from mcp.server.fastmcp import FastMCP
import json
import rdflib
import sys

mcp = FastMCP("GraphDemo")

graph = rdflib.Graph()
graph.parse("https://brickschema.org/schema/1.4.3/Brick.ttl", format="turtle")
print(len(graph))


@mcp.resource("rdf://list_terms")
def get_terms() -> list[str]:
    """Get all terms in the graph"""
    query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?class WHERE {
        ?class a owl:Class .
    }"""
    results = graph.query(query)
    #return [str(row[0]).split('#')[-1] for row in results]
    r = [str(row[0]).split('#')[-1] for row in results]
    return r


@mcp.resource("rdf://describe/{term}")
def get_definition(term: str) -> str:
    """Get the turtle definition of the term"""
    return graph.cbd(rdflib.BRICK[term]).serialize(format="turtle")
