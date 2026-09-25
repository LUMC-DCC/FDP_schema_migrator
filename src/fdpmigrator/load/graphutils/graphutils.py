"""Utility functions for minor modifications and extractions on a RDFLib Graph

"""

import re

from meta2fdp.graphutils.graphutils import graphutils as BaseGraphUtils
from owlrl import DeductiveClosure, RDFS_Semantics
from rdflib import DCTERMS, Graph, URIRef


class GraphUtils(BaseGraphUtils):
    def __init__(self):
        super().__init__()

    def add_rdfs_reasoning(self, graph: Graph) -> Graph:
        """Add RDFS reasoning to the graph. This adds dcat:Resource
        to all resource classes."""
        DeductiveClosure(RDFS_Semantics).expand(graph)
        return(graph)

    def get_main_resource(self, graph: Graph) -> URIRef:
        """Get the main resource of the graph. This is done through the 
        finding the subject that is described as dcat:Resource.
        To make sure it is the main resource, it also checks if the subject has more properties than just type. (all other properties are in their own graphs, so if the subject has more properties than just type, it is the main resource of the graph)"""
        #TODO If in the future we would want to migrate distributions it would have to
        # be manually added, as dcat:Distribution is not a dcat:Resource
        result = graph.query("""PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT DISTINCT ?s WHERE {
            ?s a dcat:Resource ;
               ?p ?o .
            FILTER (?p != rdf:type)
        }
        """)
        if result and len(result) > 1:
            raise ValueError("Graph contains multiple main resources")
        if result and len(result) > 0:
            return next(iter(result))[0]
        raise ValueError("Graph does not contain a main resource")

    def get_resource_id(self, graph: Graph, resource_type: URIRef | None = None) -> URIRef:
        """Return the primary subject of a resource graph."""
        for subject, _, _ in graph:
            return subject
        raise ValueError("Graph does not contain any triples")

    def get_title(self, graph: Graph) -> str:
        """Return a sanitized title for a resource graph."""
        for _, _, title in graph.triples((None, DCTERMS.title, None)):
            return re.sub(r"\W+", "", str(title))
        return "resource"

    def get_resource_type(self, graph: Graph, resource_id: URIRef) -> URIRef:
        """
        Obtain the dcat type of a given resource in the graph

        :param graph: A graph
        :type graph: RDFLib Graph
        :param resource_id: The URI of the resource to query
        :type resource_id: RDFLib URIRef
        :return: The dcat type of the resource
        :rtype: RDFLib URIRef
        """
        query = """PREFIX dcat: <http://www.w3.org/ns/dcat#> 
        SELECT ?value WHERE {
        ?url a ?value .
        }"""
        res = graph.query(query, initBindings={'url': resource_id})
        for attribute in res:
            return attribute[0]
    
    def get_resource_parent(self, graph: Graph, resource_id: URIRef) -> URIRef:
        """
        Obtain the parent resource of a given resource in the graph

        :param graph: A graph
        :type graph: RDFLib Graph
        :param resource_id: The URI of the resource to query
        :type resource_id: RDFLib URIRef
        :return: The parent resource of the given resource
        :rtype: RDFLib URIRef
        """
        query = """PREFIX dcat: <http://www.w3.org/ns/dcat#> 
        SELECT ?parent WHERE {
        ?parent ?p ?url .
        FILTER (?p = <http://www.w3.org/ns/ldp#contains>)
        }"""
        res = graph.query(query, initBindings={'url': resource_id})
        for attribute in res:
            return attribute[0]
