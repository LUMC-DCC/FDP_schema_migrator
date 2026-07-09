import sys
from pathlib import Path
import yaml

# Ensure `src` is on sys.path so tests can import the package without installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fdpmigrator.extract.TTL_extract_data import TTLExtractor
from fdpmigrator.transform.construct_mapper import ConstructMapper
from fdpmigrator.load.write_to_folder import write_to_folder

query_targets = yaml.safe_load(open("config/query_targets.yaml"))["query_targets"]
TTL_EXTRACTOR = TTLExtractor(base_path=Path("tests/data/fdp_files/FDP_LUMCFAIRDataPoint/Catalog_COMODULATECOVIDINFLUENZAcohortLUMC"), )

mapped_graphs = []

for graph in TTL_EXTRACTOR.generator():
    print(f"Found TTL file: {graph}")
    CONSTRUCT_MAPPER = ConstructMapper(graph=graph, query_targets=query_targets, query_folder=Path("SPARQL"))
    result_graph = CONSTRUCT_MAPPER.apply()
    print(result_graph.serialize(format="turtle"))
    mapped_graphs.append(result_graph)

write_to_folder(mapped_graphs, base_path="tests/data/output/FDP_LUMCFAIRDataPoint/Catalog_COMODULATECOVIDINFLUENZAcohortLUMC/mapped")

