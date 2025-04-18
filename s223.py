from mcp.server.fastmcp import FastMCP
import json
import sys

print("making mcp", file=sys.stderr)
mcp = FastMCP("GraphDemo", dependencies=["rdflib", "oxrdflib"])
print("mcp made", file=sys.stderr)


from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.term import Variable
from typing import List, Optional
import oxrdflib
import rdflib


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
    #return [str(row[0]).split('#')[-1] for row in results]
    r = [str(row[0]).split('#')[-1] for row in results]
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
    #return [str(row[0]).split('#')[-1] for row in results]
    r = [str(row[0]).split('#')[-1] for row in results]
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
    res = list(
        ontology.query(query, initBindings={"from": S223[term]}).bindings
    )
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

# TODO: add a "most likely class" tool

#@mcp.tool()
#def available_relationships(from_class: str, to_class: str) -> list[str]:
#    """Get the available relationships between two classes"""
#    fromc = rdflib.BRICK[from_class]
#    toc = rdflib.BRICK[to_class]
#    relationships = ontology.available_relationships(fromc, toc)
#    return [str(r).split("#")[-1] for r in relationships]
