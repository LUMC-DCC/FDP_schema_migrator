import os
from pathlib import Path

from rdflib import Graph, URIRef

class TTLExtractor:
    """This class provides methods to extract RDF graphs from TTL files and iterate through folder structures containing TTL files."""
    def __init__(self, base_path: Path = None, file_path: Path = None, resource_type:URIRef = None):
        """
        Initializes the TTLExtractor with the given parameters.
        """
        self.base_path = base_path
        self.file_path = file_path
        self.resource_type = resource_type

    def read_ttl_file(self, file_path=None):
        """
        Reads a TTL file and returns an RDF graph.
        """
        g = Graph()
        g.parse(file_path or self.file_path, format="turtle")
        return g

    def iterate_folder_structure(self, base_path=None):
        """
        Iterates through the folder structure starting from base_path.
        Returns a list of all TTL files found.
        """
        ttl_files = []
        for root, dirs, files in os.walk(base_path or self.base_path):
            for file in files:
                if file.endswith(".ttl"):
                    ttl_files.append(os.path.join(root, file))
        return ttl_files

    def load_full_graph(self, base_path=None):
        """
        Loads all TTL files in the folder structure into a single RDF graph.
        """
        g = Graph()
        ttl_files = self.iterate_folder_structure(base_path)
        for ttl_file in ttl_files:
            g.parse(ttl_file, format="turtle")
        return g

    def generator(self, base_path=None, resource_type=None) -> Graph:
        """
        Generator function that yields RDF graphs for each TTL file in the folder structure.
        If resource_type is specified, only yields graphs containing that resource type.
        """
        if base_path is None:
            base_path = self.base_path
        if resource_type is None:
            resource_type = self.resource_type
        ttl_files = self.iterate_folder_structure(base_path)
        for ttl_file in ttl_files:
            g = Graph()
            g.parse(ttl_file, format="turtle")
            if resource_type:
                query = f"SELECT ?s WHERE {{ ?s a <{resource_type}> . }}"
                qres = g.query(query)
                if len(qres) > 0:
                    yield g
            else:
                yield g
