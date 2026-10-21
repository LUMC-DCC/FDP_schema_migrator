import sys
from pathlib import Path

import yaml
from meta2fdp.config.fdp.fdpconfig import FDPConfig
from meta2fdp.fdp.fdpclient import FDPClient
from meta2fdp.secrets.environmentprovider import EnvSecretsProvider
from meta2fdp.secrets.keyringprovider import KeyringSecretsProvider
from rdflib import DCAT, DCTERMS, Graph, URIRef, RDF

from fdpmigrator.connector.ttl import TTLconnector
from fdpmigrator.transform.construct_mapper import ConstructMapper

env_secrets_provider = EnvSecretsProvider(Path("tests\\systemttest\\.env.test"))

fdp_config = FDPConfig(
    name="FDPClient",
    fdp_version="v1",
    URL=env_secrets_provider.get_secret("FDP_BASE_URL"),
    environmentprovider=EnvSecretsProvider(Path("tests\\systemttest\\.env.test")),
    keyringprovider=KeyringSecretsProvider(),
)

client = FDPClient(fdp_config)

# Ensure `src` is on sys.path so tests can import the package without installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

with open("config/query_targets_lls.yaml") as target_file:
    query_targets = yaml.safe_load(target_file)["query_targets"]
TTL_connector = TTLconnector(base_path=Path("tests/data/fdp_files/FDP_LUMCFAIRDataPoint/Catalog_LeidenLongevityStudy/"), )

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

#HACK because the current FDP implementation does not allow for updating single triples (patching) and the logic is too complex for a simple fix. We now only link datasets to datasetseries and do not add the inverse property to the datasetseries.
# SPARQL-generated destination IRIs use fdp_config.URL via ConstructMapper.

# read the LLS catalog and use the correct mapping sparql query
with open("tests/data/fdp_files/FDP_LUMCFAIRDataPoint/Catalog_LeidenLongevityStudy/LeidenLongevityStudy.ttl") as catalog_file:
    catalog_graph = Graph().parse(catalog_file)
# define the URI linked to the resource, this filter is usefull only when not building a script like this
catalog_query = {"LLScatalog": str(DCAT.Catalog)}
CONSTRUCT_MAPPER = ConstructMapper(
    graph=catalog_graph,
    query_targets=catalog_query,
    query_folder=Path("SPARQL"),
    fdp_base_iri=fdp_config.URL,
)
catalog_graph = CONSTRUCT_MAPPER.apply()
print("uploading catalog")
catalog_graph.add((URIRef(fdp_config.URL + "/catalog/new"), DCTERMS.isPartOf, URIRef(fdp_config.URL)))
catalog_url = client.post_resource(catalog_graph.serialize(), "catalog")
print(f"LLS catalog URL: {catalog_url}")
updated_catalog_graph = update_URIs(catalog_graph, URIRef(fdp_config.URL + "/catalog/new"), catalog_url)
client.put_resource(catalog_url, updated_catalog_graph.serialize())
client.publish_resource(catalog_url)

# here we map the overarching datasetseries representing the populations and then we map the datasetseries representing the individual studies, we link them to the catalog and then we link the datasets to the datasetseries of populations and the studies.
# Nonagenerians
with open("tests/data/fdp_files/FDP_LUMCFAIRDataPoint/Catalog_LeidenLongevityStudy/Catalog_Nonagenarians/Nonagenarians.ttl") as datasetseries_file:
    nonagenarians_graph = Graph().parse(datasetseries_file)
catalog_datasetseries_query = {"LLSdatasetseriesfromcatalog": str(DCAT.Catalog)}
CONSTRUCT_MAPPER = ConstructMapper(
    graph=nonagenarians_graph,
    query_targets=catalog_datasetseries_query,
    query_folder=Path("SPARQL"),
    fdp_base_iri=fdp_config.URL,
)
nonagenarians_graph = CONSTRUCT_MAPPER.apply()
nonagenarians_graph.add((URIRef(fdp_config.URL + "/datasetseries/new"), DCTERMS.isPartOf, URIRef(catalog_url)))
print("uploading Nonagenarians datasetseries")
nonagenarians_url = client.post_resource(nonagenarians_graph.serialize(), "DatasetSeries")
updated_nonagenarians_graph = update_URIs(nonagenarians_graph, URIRef(fdp_config.URL + "/datasetseries/new"), nonagenarians_url)
client.put_resource(nonagenarians_url, updated_nonagenarians_graph.serialize())
client.publish_resource(nonagenarians_url)

# for every datasetseries in the Nonagenarians folder, we map the datasets and link them to the datasetseries and then we link the datasetseries to the catalog
for datasetseries in TTL_connector.generator(base_path=Path("tests/data/fdp_files/FDP_LUMCFAIRDataPoint/Catalog_LeidenLongevityStudy/Catalog_Nonagenarians/"), resource_type=str(DCAT.DatasetSeries)):
    datasetseries_query = {"LLSdatasetseriesfromdatasetseries": str(DCAT.DatasetSeries)}
    CONSTRUCT_MAPPER = ConstructMapper(
        graph=datasetseries,
        query_targets=datasetseries_query,
        query_folder=Path("SPARQL"),
        fdp_base_iri=fdp_config.URL,
    )
    datasetseries_graph = CONSTRUCT_MAPPER.apply()
    datasetseries_graph.add((URIRef(fdp_config.URL + "/datasetseries/new"), DCTERMS.isPartOf, URIRef(catalog_url)))
    #not sure if we need to refer to the overarching datasetseries representing the populations, but we do it for now
    datasetseries_graph.add((URIRef(fdp_config.URL + "/datasetseries/new"), DCAT.inSeries, URIRef(nonagenarians_url)))
    print(f"uploading {datasetseries_graph.value(predicate=DCTERMS.title)} datasetseries")
    series_url = client.post_resource(datasetseries_graph.serialize(), "DatasetSeries")
    updated_datasetseries_graph = update_URIs(datasetseries_graph, URIRef(fdp_config.URL + "/datasetseries/new"), series_url)
    client.put_resource(series_url, updated_datasetseries_graph.serialize())
    client.publish_resource(series_url)
    datasetseries_path = Path(TTL_connector.file_path)
    for dataset in TTL_connector.generator(base_path=datasetseries_path.parent, resource_type=str(DCAT.Dataset)):
        # datasetseries are datasets, we want to skip the one the datasets are currently under. #HACK this script assumes that there is only one level of datasetseries, if there are nested datasetseries this will not work. 
        if dataset.value(predicate=DCTERMS.title) == datasetseries_graph.value(predicate=DCTERMS.title):
            continue
        dataset_query = {"LLSdataset": str(DCAT.Dataset)}
        CONSTRUCT_MAPPER = ConstructMapper(
            graph=dataset,
            query_targets=dataset_query,
            query_folder=Path("SPARQL"),
            fdp_base_iri=fdp_config.URL,
        )
        dataset = CONSTRUCT_MAPPER.apply()
        dataset.add((URIRef(fdp_config.URL + "/dataset/new"), DCAT.inSeries, URIRef(nonagenarians_url)))
        dataset.add((URIRef(fdp_config.URL + "/dataset/new"), DCAT.inSeries, URIRef(series_url)))
        dataset.add((URIRef(fdp_config.URL + "/dataset/new"), DCTERMS.isPartOf, URIRef(catalog_url)))
        print("uploading dataset")
        dataset_url = client.post_resource(dataset.serialize(), "dataset")
        updated_dataset_graph = update_URIs(dataset, URIRef(fdp_config.URL + "/dataset/new"), dataset_url)
        client.put_resource(dataset_url, updated_dataset_graph.serialize())
        client.publish_resource(dataset_url)
    
