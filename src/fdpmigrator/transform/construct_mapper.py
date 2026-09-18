from rdflib import RDF, Graph
import yaml
from pathlib import Path

query_targets = yaml.safe_load(open("config/query_targets_lls.yaml"))["query_targets"]
query_folder = Path("SPARQL")

class ConstructMapper:
    def __init__(self, graph:Graph, construct_query:str = None, query_targets:dict = None, query_folder:Path = query_folder):
        self.graph = graph
        self.construct_query = construct_query
        self.query_targets = query_targets
        self.query_folder = query_folder

    def get_query(self, query_name:str):
        with open(self.query_folder / f"{query_name}.rq", "r") as f:
            return f.read()

    def apply(self):
        """
        Applies the SPARQL CONSTRUCT query to the given RDF graph and returns the resulting graph.
        If no CONSTRUCT query is provided, it will attempt to determine the appropriate query based on the subjects in the graph.
        This is done by checking if any of the subjects in the graph match dcat types specified in the query_targets dictionary. If a match is found, the corresponding SPARQL query is loaded and applied to the graph.
        The key in the query_targets dictionary corresponds to the name of the SPARQL query file (without the .rq extension) that should be used for the CONSTRUCT operation.
        The value in the query_targets dictionary is a list of URIs that are associated with that specific query.
        If a match is found, the corresponding SPARQL query is loaded from the SPARQL folder and applied to the graph. If no match is found, the original graph is returned unchanged.
        """
        result_graph = Graph()
        if self.construct_query is None:
            subjects = self.graph.subjects()
            for subject in subjects:
                subjectypes = self.graph.value(subject=subject, predicate=RDF.type, object=None)
                for query_name, types in self.query_targets.items():
                    if str(subjectypes) in types:
                        self.construct_query = self.get_query(query_name)
                        break
                if self.construct_query is not None:
                    break
        result_graph += self.graph.query(self.construct_query)
        return result_graph

