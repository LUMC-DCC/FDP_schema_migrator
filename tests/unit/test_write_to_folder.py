import sys
from pathlib import Path

from rdflib import DCAT, DCTERMS, Graph, Literal, RDF, URIRef

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fdpmigrator.load.write_to_folder import write_to_folder


def test_write_to_folder_creates_ttl_file(tmp_path: Path) -> None:
    graph = Graph()
    subject = URIRef("https://example.org/resource")

    graph.add((subject, DCTERMS.title, Literal("My Resource")))
    graph.add((subject, RDF.type, DCAT.Dataset))

    write_to_folder([graph], base_path=str(tmp_path))

    assert any(path.suffix == ".ttl" for path in tmp_path.rglob("*.ttl"))
