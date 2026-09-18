import sys
from pathlib import Path

import yaml

# Ensure `src` is on sys.path so tests can import the package without installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fdpmigrator.connector.ttl import TTLconnector
from fdpmigrator.load.write_to_folder import write_to_folder_lls
from fdpmigrator.transform.construct_mapper import ConstructMapper

with open("config/query_targets_lls.yaml") as target_file:
    query_targets = yaml.safe_load(target_file)["query_targets"]
TTL_connector = TTLconnector(base_path=Path("tests/data/fdp_files/FDP_LUMCFAIRDataPoint/Catalog_LeidenLongevityStudy/"), )

mapped_graphs = []

for graph in TTL_connector.generator():
    CONSTRUCT_MAPPER = ConstructMapper(graph=graph, query_targets=query_targets, query_folder=Path("SPARQL"))
    result_graph = CONSTRUCT_MAPPER.apply()
    print(result_graph.serialize(format="turtle"))
    mapped_graphs.append(result_graph)

write_to_folder_lls(mapped_graphs, base_path="tests/data/output/FDP_LUMCFAIRDataPoint/lls/mapped")

