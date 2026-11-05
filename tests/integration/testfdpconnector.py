from fdpmigrator.connector.fdp import FDPConnector

FDPconnector = FDPConnector(working_directory="tests/data/fdp_files/FDP_LUCID")
FDPconnector.get_resource("https://fdp.lucid.lumc.nl", "LUCID_FDP.ttl")
