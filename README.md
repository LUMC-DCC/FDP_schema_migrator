# AI use disclaimer
AI use disclaimer: This project is a research project and is not intended for production use. The code is provided "as is" without any warranties or guarantees. Users are responsible for evaluating the suitability of the code for their own purposes and should exercise caution when using it in any critical applications.
The project has been developed with the assistance of AI tools, and while the authors have manually reviewed and edited generated sections and effort has been made to ensure the accuracy and reliability of the code, it may contain errors or limitations. Users should review and test the code thoroughly before using it in any production environment. The authors are not liable for any damages or losses that may arise from the use of this code.

List of AI assistance:
- SPARQL queries were generated with the assistance of Microsoft Copilot and manually reviewed and edited by the authors until function and correctness were achieved.
- Documentation and README.md were partially written with the assistance of Github Copilot and manually reviewed and edited by the authors to convey intended logic, reasoning, and functionality. 
- Copilot autocomplete suggestions were used to generate code snippets and boilerplate code, which were then manually reviewed and edited by the authors to ensure correctness and functionality.

# FDP_schema_migrator
This is a utility project where I use RDFLib and SPARQL Construct queries to migrate our Health-RI v1 metadata on the [lumc FDP](https://fdp.lumc.nl) to v2.0.2

The project is constructed in the ETL (Extract Transform Load) process.
The architectural goal is to set up a pipeline that can accept customized mappings (in SPARQL) for specific target resources on a FDP.
Ideally, this type of migration/mapping/pipeline will be integrated into the meta2fdp package in the future. 
To improve future ease of integration we import the meta2fdp package in this project and use its modules where possible.

## example usecase:

We obtain the metadata stored in the public FDP of the LUMC at: fdp.lumc.nl

We write custom SPARQL queries for the covid v1 Health-RI metadata on the FDP and construct graphs compliant with the [v2.0.2](https://github.com/Health-RI/health-ri-metadata/tree/v2.0.2)

We write the graphs to file so we can upload them to the testing environment FDP.

The LLS metadata in particular is a good example usecase for this type of migration. The LLS resources are in a process of being redefined. This calls for the need to have resources be mapped to other resource schemas (catalogs becoming datasetseries). This also requires a different hiearchy of resources as relationships beteen datasetseries, catalogs and datasets are not equally expressed.

## Developer Notes

Warning! current implementation is a work in progress and unittest are not yet implemented. The code is not yet production ready.
Currently, the code is structured in a way that it can be run as a script, but it is not yet structured as a package. The code is not yet modular and is not yet tested.
- **How to run tests**
	The tests can be run with `pytest` from the repository root. The tests require the `src` folder to be on `PYTHONPATH`, or the package must be installed. You can run the tests with the following command:

	```bash
	uv sync
	python -m pytest tests
	```
	To install the package in development mode, run:

	```bash

