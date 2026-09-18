"""
FDP data extraction script (start)
Author: Karolis Cremers https://github.com/KarolisCremers
ORCID: https://orcid.org/0000-0002-1756-3905
Based on: https://github.com/KarolisCremers/FDP-extractor/blob/450f23ca00c02134498a1438088075094d5c3769/FDP_extract_data.py
"""

import os
import re

import requests
from rdflib import Graph, URIRef

# The module-level values are retained for compatibility with older callers.
# New code should use the instance values configured in FDPConnector.__init__.
cwd = os.getcwd()
ignore = ('https://w3id.org/fdp/fdp-o#MetadataService', "http://www.w3.org/ns/dcat#Resource",
                  "http://www.w3.org/ns/dcat#DataService", )

class FDPConnector:
    """Retrieve an FDP resource tree and store its resources as Turtle files.

    An FDP exposes each resource as RDF and links parent resources to their
    children with ``ldp:contains``. (see https://github.com/fdp-specs/fdp-specs.github.io/blob/5e122bf192b431afe5034c71379f8522e1cbb227/src/metadata.md?plain=1#L38-L46)
    The connector follows those links,writes each response to a resource-specific directory, and returns one
    merged graph for callers that also need the complete metadata tree.
    """

    def __init__(self, working_directory=None):
        """Configure where the root FDP directory and its children are stored.

        Keeping the working directory on the instance makes multiple
        connectors usable in the same process without relying on the process
        current directory.
        """
        self.working_directory = working_directory or os.getcwd()
        self.ignore = (
            "https://w3id.org/fdp/fdp-o#MetadataService",
            "http://www.w3.org/ns/dcat#Resource",
            "http://www.w3.org/ns/dcat#DataService",
        )

    def get_title(self, graph, url):
        """Return a resource title sanitized for use as a file name.

        FDP resource titles are stored as ``dcterms:title`` values.  The
        title is used in both directory and file names, so punctuation and
        other non-word characters are removed before it is returned.
        """
        query = """PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT ?o WHERE {
        ?url dcterms:title ?o .
        }"""
        result = graph.query(query, initBindings={"url": url})
        return re.sub(r"\W+", "", str(result.bindings[0]["o"]))

    def write_to_disk(self, graph, url, directory):
        """Write a resource graph to the appropriate Turtle file.

        The directory is selected separately by :meth:`directories`; keeping
        serialization here ensures every resource is persisted before its
        children are traversed.
        """
        filepath = os.path.join(directory, self.get_title(graph, url))
        graph.serialize(destination=f"{filepath}.ttl", format="turtle")

    def directories(self, graph, url, path):
        """Return and create the directory for a resource in the FDP tree.

        The FDP root starts a new ``FDP_<title>`` directory.  For descendants,
        the RDF type becomes the directory prefix, for example
        ``Catalog_<title>``.  MetadataService, dcat:Resource, and
        dcat:DataService are implementation details or shared types rather
        than hierarchy levels, so they are deliberately excluded from paths.
        """
        query = """SELECT ?value WHERE {
        ?url a ?value .
        }"""
        types = graph.query(query, initBindings={"url": url})
        current_path = path
        for attribute in types:
            uri = str(attribute[0])
            if uri == "https://w3id.org/fdp/fdp-o#FAIRDataPoint":
                # The root must be anchored to the configured output folder;
                # descendants are appended to the path supplied by the parent.
                current_path = os.path.join(
                    self.working_directory,
                    "FDP_" + self.get_title(graph, url).rstrip(" ").replace(" ", "_"),
                )
                break
            if uri not in self.ignore:
                # FDP vocabularies use both '#' and '/' to separate the local
                # type name, so support either form when making a directory.
                resource_type = uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
                directory_name = resource_type + "_" + self.get_title(graph, url).replace(" ", "_")
                current_path = os.path.join(path, directory_name)
        os.makedirs(current_path, exist_ok=True)
        return current_path

    def traverse_fdp(self, url, path=None):
        """Recursively retrieve an FDP tree and return its merged graph.

        The FDP endpoint serves Turtle when ``?format=ttl`` is appended.  A
        child in draft state cannot be read through the public endpoint; in
        that case an empty graph is returned so the rest of the tree can
        still be processed.  ``ldp:contains`` is the authoritative child
        relationship, according to the FDP specifications at 
        https://github.com/fdp-specs/fdp-specs.github.io/blob/5e122bf192b431afe5034c71379f8522e1cbb227/src/metadata.md?plain=1#L38-L46 .
        """
        print(f"querying: {url}")
        resource_url = URIRef(url)
        # URIRef keeps RDF URLs distinct from ordinary string literals while
        # still allowing them to be interpolated into the HTTP request URL.
        response = requests.get(f"{resource_url}/?format=ttl")
        if response.text == "You are not allow to view this record in state DRAFT":
            # The API exposes this response as text instead of usable RDF.
            # Skipping it avoids a parse failure and preserves other branches.
            return Graph()

        graph = Graph()
        # Pass the response body through data=; otherwise rdflib may interpret
        # the Turtle text as a local filename.
        graph.parse(data=response.text, format="ttl")
        resource_path = self.directories(graph, resource_url, path or self.working_directory)
        self.write_to_disk(graph, resource_url, resource_path)

        # ldp:contains points to child resources.  A resource with no such
        # triples is a leaf, so the loop naturally handles both cases.
        children = graph.query("""SELECT ?o WHERE {
            ?s <http://www.w3.org/ns/ldp#contains> ?o .
        }""")
        for resource in children:
            # Each child receives the current resource directory as its parent
            # path, while its own type determines the next directory name.
            graph += self.traverse_fdp(resource.o, resource_path)
        return graph

    def get_resource(self, url, destination):
        """Retrieve an FDP tree and write the merged graph to Turtle.

        Individual resource files are written during traversal.  This final
        serialization is an additional single-file export containing all
        triples collected from the tree.
        """
        graph = self.traverse_fdp(url)
        graph.serialize(destination=destination, format="turtle")

if __name__ == '__main__':
    FDPConnector().get_resource('https://fdp.lumc.nl', "lumc-fdp.ttl")