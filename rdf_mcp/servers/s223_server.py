from mcp.server.fastmcp import FastMCP
import sys
import logging
from rdflib import Graph, Namespace
from rdflib.term import Variable
from rdflib.namespace import RDFS, XSD, SH
from typing import Dict

# Set up logging to stderr for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("GraphDemo")

logger.info("making mcp")
mcp = FastMCP("GraphDemo", dependencies=["rdflib", "oxrdflib"])
logger.info("mcp made")


S223 = Namespace("http://data.ashrae.org/standard223#")
ontology = Graph().parse("https://open223.info/223p.ttl")


@mcp.tool()
def get_terms() -> list[str]:
    """Get all terms in the 223P ontology graph"""
    query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX s223: <http://data.ashrae.org/standard223#>
    SELECT ?class WHERE {
        ?class a s223:Class .
    }"""
    results = ontology.query(query)
    # return [str(row[0]).split('#')[-1] for row in results]
    r = [str(row[0]).split("#")[-1] for row in results]
    return r


@mcp.tool()
def get_properties() -> list[str]:
    """Get all properties in the 223P ontology graph"""
    query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX s223: <http://data.ashrae.org/standard223#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT ?class WHERE {
        ?class a rdf:Property .
    }"""
    results = ontology.query(query)
    # return [str(row[0]).split('#')[-1] for row in results]
    r = [str(row[0]).split("#")[-1] for row in results]
    return r


@mcp.tool()
def get_possible_properties(term: str):
    """Get the possible properties for a class in the 223P ontology graph"""
    query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX s223: <http://data.ashrae.org/standard223#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT ?path WHERE {
        ?from rdfs:subClassOf* ?fromp .
        { ?shape sh:targetClass ?fromp }
        UNION
        { ?fromp a sh:NodeShape . BIND(?fromp as ?shape) }
        ?shape sh:property ?prop .
        ?prop sh:path ?path .
         FILTER (!isBlank(?path))
    }
    """
    res = list(ontology.query(query, initBindings={"from": S223[term]}).bindings)
    paths = set([r[Variable("path")] for r in res])
    return list(paths)


@mcp.resource("rdf://describe/{term}")
def get_definition(term: str) -> str:
    """Get the definition of cyber-physical concepts like sensors from the 223P ontology."""
    return ontology.cbd(S223[term]).serialize(format="turtle")


@mcp.tool()
def get_definition_223p(term: str) -> str:
    """Get the definition of cyber-physical concepts like sensors from the 223P ontology."""
    return ontology.cbd(S223[term]).serialize(format="turtle")


@mcp.tool()
def get_constraints(term: str) -> list[dict]:
    """Get SHACL constraints for a class or property in the S223P ontology"""
    try:
        # Construct the query using SPARQL with rdflib namespace references
        query = f"""
        PREFIX sh: <{SH}>
        PREFIX rdfs: <{RDFS}>
        PREFIX s223: <{S223}>
        PREFIX xsd: <{XSD}>
        SELECT ?comment ?message ?minCount ?maxCount ?path ?qualifiedMinCount ?qualifiedMaxCount
               ?qualifiedValueShape ?class ?nestedPath ?nestedClass
        WHERE {{
            s223:{term} a sh:NodeShape ;
                sh:property ?prop .
            OPTIONAL {{ ?prop rdfs:comment ?comment }}
            OPTIONAL {{ ?prop sh:message ?message }}
            OPTIONAL {{ ?prop sh:minCount ?minCount }}
            OPTIONAL {{ ?prop sh:maxCount ?maxCount }}
            OPTIONAL {{ ?prop sh:path ?path }}
            OPTIONAL {{ ?prop sh:qualifiedMinCount ?qualifiedMinCount }}
            OPTIONAL {{ ?prop sh:qualifiedMaxCount ?qualifiedMaxCount }}
            OPTIONAL {{
                ?prop sh:qualifiedValueShape ?qualifiedValueShape .
                OPTIONAL {{ ?qualifiedValueShape sh:class ?class }}
                OPTIONAL {{
                    ?qualifiedValueShape sh:node ?node .
                    ?node sh:property ?nestedProp .
                    ?nestedProp sh:path ?nestedPath .
                    OPTIONAL {{ ?nestedProp sh:class ?nestedClass }}
                }}
            }}
        }}
        """

        results = ontology.query(query)
        constraints = []
        for row in results:
            logger.info(f"Row: {row}")

        # Define Variable objects for each field
        comment_var = Variable("comment")
        message_var = Variable("message")
        min_count_var = Variable("minCount")
        max_count_var = Variable("maxCount")
        path_var = Variable("path")
        qualified_min_count_var = Variable("qualifiedMinCount")
        qualified_max_count_var = Variable("qualifiedMaxCount")
        # qualified_value_shape_var = Variable("qualifiedValueShape")
        class_var = Variable("class")
        nested_path_var = Variable("nestedPath")
        nested_class_var = Variable("nestedClass")

        for row in results.bindings:
            constraint: Dict[str, any] = {}

            # Add the human-readable description if available
            if comment_var in row and row[comment_var]:
                constraint["description"] = str(row[comment_var])
            elif message_var in row and row[message_var]:
                constraint["description"] = str(row[message_var])

            # Add constraint details
            if path_var in row and row[path_var]:
                constraint["path"] = str(row[path_var]).split("#")[-1]

            # Add cardinality constraints
            if min_count_var in row and row[min_count_var]:
                constraint["minCount"] = int(row[min_count_var])
            if max_count_var in row and row[max_count_var]:
                constraint["maxCount"] = int(row[max_count_var])

            # Add qualified cardinality constraints
            if qualified_min_count_var in row and row[qualified_min_count_var]:
                constraint["qualifiedMinCount"] = int(row[qualified_min_count_var])
            if qualified_max_count_var in row and row[qualified_max_count_var]:
                constraint["qualifiedMaxCount"] = int(row[qualified_max_count_var])

            if class_var in row and row[class_var]:
                constraint["class"] = str(row[class_var]).split("#")[-1]

            # Add nested constraints if available
            if (
                nested_path_var in row
                and nested_class_var in row
                and row[nested_path_var]
                and row[nested_class_var]
            ):
                constraint["nested"] = {
                    "path": str(row[nested_path_var]).split("#")[-1],
                    "class": str(row[nested_class_var]).split("#")[-1],
                }

            if constraint:  # Only add if we have some content
                constraints.append(constraint)

        if not constraints:
            # Try to get other useful information about the term
            comment_query = f"""
            PREFIX rdfs: <{RDFS}>
            PREFIX s223: <{S223}>

            SELECT ?comment ?label WHERE {{
                s223:{term} rdfs:comment ?comment .
                OPTIONAL {{ s223:{term} rdfs:label ?label }}
            }}
            """

            comment_results = ontology.query(comment_query)
            comment_var = Variable("comment")

            for row in comment_results.bindings:
                if comment_var in row and row[comment_var]:
                    constraints.append(
                        {"description": str(row[comment_var]), "type": "comment"}
                    )

        return constraints
    except Exception as e:
        logger.error(f"Error in get_constraints: {e}")
        return [{"error": f"Failed to retrieve constraints for {term}: {str(e)}"}]


# TODO: add a "most likely class" tool

# @mcp.tool()
# def available_relationships(from_class: str, to_class: str) -> list[str]:
#    """Get the available relationships between two classes"""
#    fromc = rdflib.BRICK[from_class]
#    toc = rdflib.BRICK[to_class]
#    relationships = ontology.available_relationships(fromc, toc)
#    return [str(r).split("#")[-1] for r in relationships]


def main():
    print("s223 MCP server starting...", file=sys.stderr)
    mcp.run()


if __name__ == "__main__":
    main()
