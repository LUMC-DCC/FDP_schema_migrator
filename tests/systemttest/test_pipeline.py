import sys
from pathlib import Path

import yaml

# Ensure `src` is on sys.path so tests can import the package without installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from meta2fdp.config.fdp.fdpconfig import FDPConfig
from meta2fdp.fdp.fdpclient import FDPClient
from meta2fdp.secrets.environmentprovider import EnvSecretsProvider
from meta2fdp.secrets.keyringprovider import KeyringSecretsProvider
from rdflib import DCAT, DCTERMS, Graph, URIRef

from fdpmigrator.connector.ttl import TTLconnector
from fdpmigrator.transform.construct_mapper import ConstructMapper


def update_URIs(graph: Graph, old_base_uri: str, new_base_uri: str) -> Graph:
    """
    Updates the URIs in the given RDF graph by replacing the old base URI with the new base URI.

    :param graph: The RDF graph to update.
    :param old_base_uri: The old base URI to replace.
    :param new_base_uri: The new base URI to use.
    :return: The updated RDF graph.
    """
    updated_graph = Graph()
    for s, p, o in graph:
        if isinstance(s, URIRef) and str(s).startswith(old_base_uri):
            s = URIRef(str(s).replace(old_base_uri, new_base_uri))
        if isinstance(o, URIRef) and str(o).startswith(old_base_uri):
            o = URIRef(str(o).replace(old_base_uri, new_base_uri))
        updated_graph.add((s, p, o))
    return updated_graph

env_secrets_provider = EnvSecretsProvider(Path("tests\\systemttest\\.env.test"))

fdp_config = FDPConfig(
    name="FDPClient",
    fdp_version="v1",
    URL=env_secrets_provider.get_info("FDP_BASE_URL"),
    environmentprovider=env_secrets_provider,
    keyringprovider=KeyringSecretsProvider(),
)
client = FDPClient(fdp_config)

with open("config/query_targets_covid.yaml") as target_file:
    query_targets = yaml.safe_load(target_file)["query_targets"]

covid_catalogs = ["tests/data/fdp_files/FDP_LUMCFAIRDataPoint/Catalog_COMODULATECOVIDINFLUENZAcohortLUMC", "tests/data/fdp_files/FDP_LUMCFAIRDataPoint/Catalog_BEATCOVIDcohortLUMC"]

for covid_catalog in covid_catalogs:
    Graph_connector = TTLconnector(base_path=Path(covid_catalog), resource_type=str(DCAT.Catalog), )

    for catalog_graph in Graph_connector.generator():
        print(f"Found graph file: {catalog_graph}")
        CONSTRUCT_MAPPER = ConstructMapper(graph=catalog_graph, query_targets=query_targets, query_folder=Path("SPARQL"), fdp_base_iri=fdp_config.URL)
        mapped_catalog = CONSTRUCT_MAPPER.apply()
        print("uploading catalog")
        mapped_catalog.add((URIRef(fdp_config.URL + "/catalog/new"), DCTERMS.isPartOf, URIRef(fdp_config.URL)))
        catalog_url = client.post_resource(mapped_catalog.serialize(), "catalog")
        updated_catalog_graph = update_URIs(mapped_catalog, URIRef(fdp_config.URL + "/catalog/new"), catalog_url)
        client.put_resource(catalog_url, updated_catalog_graph.serialize())
        print(f"covid catalog URL: {catalog_url}")
        client.publish_resource(catalog_url)
    
        catalog_path = Path(Graph_connector.file_path)
        for dataset_graph in Graph_connector.generator(base_path=catalog_path.parent, resource_type=str(DCAT.Dataset)):
            print(f"Found graph file: {dataset_graph}")
            CONSTRUCT_MAPPER = ConstructMapper(graph=dataset_graph, query_targets=query_targets, query_folder=Path("SPARQL"), fdp_base_iri=fdp_config.URL)
            mapped_dataset = CONSTRUCT_MAPPER.apply()
            mapped_dataset.add((URIRef(fdp_config.URL + "/dataset/new"), DCTERMS.isPartOf, URIRef(catalog_url)))
            print("uploading dataset")
            dataset_url = client.post_resource(mapped_dataset.serialize(), "dataset")
            updated_catalog_graph = update_URIs(updated_catalog_graph, URIRef(fdp_config.URL + "/dataset/new"), dataset_url)
            client.put_resource(dataset_url, updated_catalog_graph.serialize())
            print(f"covid dataset URL: {dataset_url}")
            client.publish_resource(dataset_url)


