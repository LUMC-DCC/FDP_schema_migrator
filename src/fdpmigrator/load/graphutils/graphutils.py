"""Utility functions for minor modifications and extractions on a RDFLib Graph

"""

from meta2fdp.graphutils.graphutils import graphutils as BaseGraphUtils
from owlrl import DeductiveClosure, RDFS_Semantics
from rdflib import Graph, URIRef


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
        finding the subject that is described as dcat:Resource"""
        #TODO If in the future we would want to migrate distributions it would have to
        # be manually added, as dcat:Distribution is not a dcat:Distribution
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
    