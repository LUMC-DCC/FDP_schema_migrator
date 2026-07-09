"""This module contains the function to write the transformed RDF graphs to a specified folder.
It follows the standard FDP structure and creates subfolders for each resource type.
The function takes a list of RDF graphs and a base path as input, and writes each graph to a separate TTL file in the appropriate subfolder based on its resource type and parent resource."""

import os
from typing import List
from rdflib import Graph
from fdpmigrator.load.graphutils.graphutils import graphutils


def write_to_folder(graphs: List[Graph], base_path: str):
    """
    Writes the given RDF graphs to the specified base path following the standard FDP structure.
    Each graph is written to a separate TTL file in the appropriate subfolder based on its resource type and parent resource.
    
    Parameters:
        graphs (list): A list of RDF graphs to be written to disk.
        base_path (str): The base path where the graphs will be written.
    """
    utils = graphutils()

    for graph in graphs:
        # Determine the resource type and parent resource from the graph
        resource_id = utils.get_resource_id(graph)
        resource_type = utils.get_resource_type(graph, resource_id)
        parent_resource = utils.get_resource_parent(graph, resource_id)

        # Create the appropriate subfolder based on the resource type and parent resource
        #FIXME now tries to attach an uri to the folder name, which is not allowed. Need to sanitize the uri to a valid folder name or obtain the title of the parent resource instead
        subfolder_path = os.path.join(base_path, f"{resource_type}_{parent_resource}")
        os.makedirs(subfolder_path, exist_ok=True)
        
        # Write the graph to a TTL file in the subfolder
        ttl_file_path = os.path.join(subfolder_path, f"{utils.get_title(graph)}.ttl")
        graph.serialize(destination=ttl_file_path, format="turtle")
    