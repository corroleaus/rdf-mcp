from mcp import FastMCP
import rdflib

# Specify dependencies for deployment and development
mcp = FastMCP("GraphDemo", dependencies=["rdflib"])

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
    return [str(row[0]).split('#')[-1] for row in results]


@mcp.resource("rdf://describe/{term}")
def get_definition(term: str) -> str:
    """Get the turtle definition of the term"""
    # Construct the full URI for the term
    term_uri = rdflib.Namespace("https://brickschema.org/schema/1.4.3/Brick#")[term]
    return graph.cbd(term_uri).serialize(format="turtle")


if __name__ == "__main__":
    mcp.run()
