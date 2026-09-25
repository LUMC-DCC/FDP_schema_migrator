"""This module contains the function to write the transformed RDF graphs to a specified folder.
It follows the standard FDP structure and creates subfolders for each resource type.
The function takes a list of RDF graphs and a base path as input, and writes each graph to a separate TTL file in the appropriate subfolder based on its resource type and parent resource."""

import os

from rdflib import Graph

from fdpmigrator.load.graphutils.graphutils import GraphUtils

utils = GraphUtils()

def identify_main_resource(graph: Graph, context: str) -> str:
    """loads in the context from the config folder,
    merges it with the graph, and identifies the main resource of the graph based on the context.
    """
    with open(context, "r", encoding="utf-8") as f:
        context_graph = Graph().parse(f, format="turtle")
        reasonable_graph = utils.add_rdfs_reasoning(graph + context_graph)
    return utils.get_main_resource(reasonable_graph)

def write_to_folder(graphs: list[Graph], base_path: str):
    """
    Writes the given RDF graphs to the specified base path following the standard FDP structure.
    Each graph is written to a separate TTL file in the appropriate subfolder based on its resource type and parent resource.

    Parameters:
        graphs (list): A list of RDF graphs to be written to disk.
        base_path (str): The base path where the graphs will be written.
    """
    
    combined_graph = Graph()
    for graph in graphs:
        # Determine the resource type and parent resource from the graph
        resource_id = identify_main_resource(graph, "config/context.ttl")
        resource_type = utils.get_resource_type(graph, resource_id).removeprefix("http://www.w3.org/ns/dcat#")
        combined_graph += graph
        parent_resource_uri = utils.get_resource_parent(graph, resource_id)
        parent_resource = utils.get_title(combined_graph.cbd(parent_resource_uri))

        # Create the appropriate subfolder based on the resource type and parent resource
        subfolder_path = os.path.join(base_path, f"{resource_type}_{parent_resource}")
        os.makedirs(subfolder_path, exist_ok=True)
        
        # Write the graph to a TTL file in the subfolder
        ttl_file_path = os.path.join(subfolder_path, f"{utils.get_title(graph)}.ttl")
        graph.serialize(destination=ttl_file_path, format="turtle")

def write_to_folder_stupid(graphs: list[Graph], base_path: str):
    """Use the assumption that graphs list is ordered based on the
    hiearchical structure of the input and assume that any time we encounter
    a catalog we should write a new folder on the level of the FDP.

    :param graphs: A list of RDF Graphs with catalog, catalog_child, catalog_child, catalog, catalog_child pattern
    :type graphs: list[Graph]
    :param base_path: Folder that represents the FDP level in hiearchy
    :type base_path: str
    """
    combined_graph = Graph()
    current_path = base_path
    catalog_count = 0
    resource_count = 0
    for graph in graphs:
        resource_id = identify_main_resource(graph, "config/context.ttl")
        resource_type = utils.get_resource_type(graph, resource_id).removeprefix("http://www.w3.org/ns/dcat#")
        combined_graph += graph

        if resource_type.lower() == "catalog":
            catalog_count += 1
            current_path = os.path.join(base_path, f"{utils.get_title(graph).split(" ")[0]}_catalog{catalog_count}") 
            os.makedirs(current_path, exist_ok=True)
            graph.serialize(destination=current_path + ".ttl", format="turtle")
            resource_count = 0

        else:
            # Write any resource under the current graph
            resource_count += 1
            ttl_file_path = os.path.join(current_path, f"{resource_type}{resource_count}.ttl")
            graph.serialize(destination=ttl_file_path, format="turtle")
