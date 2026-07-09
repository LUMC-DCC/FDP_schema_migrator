# FDP_schema_migrator
This is a utility project where I use RDFLib and Construct queries to migrate our Health-RI v1 metadata on the FDP to v2.0.2

The project is constructed in the ETL (Extract Transform Load) process.
The architectural goal is to set up a pipeline that can accept customized mappings (in SPARQL) for specific target resources on a FDP.

## example usecase:

We obtain the metadata stored in the public FDP of the LUMC at: fdp.lumc.nl

We write custom SPARQL queries for the covid v1 Health-RI metadata on the FDP and construct graphs compliant with the [v2.0.2](https://github.com/Health-RI/health-ri-metadata/tree/v2.0.2)

We write the graphs to file so we can upload them to the testing environment FDP.

## Developer Notes

- **How to run tests**
	- From the project root, run with `src` on the Python path (Unix/macOS):

		```bash
		PYTHONPATH=src pytest -q
		```

	- On Windows PowerShell:

		```powershell
		$env:PYTHONPATH = 'src'; pytest -q
		```

	- Or install the package in editable mode and run tests:

		```bash
		pip install -e .
		pytest -q
		```

- **Why**: The project uses a `src/` layout. Tests run from the repository root need the `src` folder on `PYTHONPATH`, or the package must be installed. The internal module import was converted to a relative import to follow package import best-practices.

