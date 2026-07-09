"""Utility functions for minor modifications and extractions on a RDFLib Graph

"""
import re

from fdpmigrator.load.graphutils.graphinteractor import GraphInteractor
from rdflib import Graph, Literal, URIRef, DCTERMS, XSD


class graphutils(GraphInteractor):


    def subject_replace(self, PURL, node_id, dcat_type, graph) -> None:
        """
        Build a SPARQL CONSTRUCT query that replaces the object with the given
        DCAT type and run it on the given graph.

        :param PURL: new subject URI
        :type PURL: string
        :param node_id: original uri of object
        :type node_id: string
        :param dcat_type: RDFlib DCAT uri of the resource used as a tag on what object to replace
        :type dcat_type: RDFLib URIRef
        :param graph: graph to replace the main object from
        :type graph: RDFLib Graph
        """
        # this query should be able to work only with the node_id variable as a filter
        firstpart = """
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>

        CONSTRUCT {
        ?newResource ?p ?property .
        }
        WHERE {
        ?resource a <""" 
        middle = """> ;
                    ?p ?property .
        BIND(<"""
        lastpart = """> AS ?newResource)
        }
        """
        q = firstpart + str(dcat_type) + middle + str(PURL) + lastpart
        qres = graph.query(q)
        for s, p, o in qres:
            graph.add((s,p,o))
        graph.remove((node_id, None, None))

    def merge_desc(self, dataset, graph):
        """
        Merge all collected descriptions into a single string (xsd:string) required Health-RI v1 model.  

        :param dataset: dataset node id 
        :type dataset: str
        :param graph: graph containing dataset information
        :type graph: Graph
        """
        #TODO this function blindly merges strings, this could result in duplicate paragraphs in the FDP resource descriptions.
        #  either the SOP for Mica has to change so dataset descriptions are fully autominous or 
        # we have to figure out a way to only select relevant descriptions.
        triples = graph.triples((dataset, DCTERMS.description, None)) # query graph for all descriptions associated to the new resource
        descriptions = ""
        for s, p, o in triples:
            descriptions = descriptions + "\n" + o
            graph.remove((s,p,o))
        graph.add((dataset, DCTERMS.description, Literal(descriptions, datatype=XSD.string))) #HACK Health-RI has currently forced descriptions to be xsd string value type
        
    def get_dataset_nodes(self, graph: Graph) -> list:
        """
        Obtain blank node id's inside the graph

        :param graph: A graph
        :type graph: RDFLib Graph
        :return: list of blank node URIs with dcat:Dataset type found in the graph
        :rtype: list
        """
        query = """PREFIX dcat: <http://www.w3.org/ns/dcat#> 
        SELECT ?s WHERE {
        ?s a dcat:Dataset
        }"""
        res = graph.query(query)
        return [id for id in res]

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