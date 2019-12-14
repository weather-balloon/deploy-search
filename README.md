# Azure Search configuration

[![Build Status](https://dev.azure.com/weatherballoon/Weather%20Balloon/_apis/build/status/weather-balloon.deploy-search?branchName=master)](https://dev.azure.com/weatherballoon/Weather%20Balloon/_build/latest?definitionId=13&branchName=master)

Script and index definitions for deploying Azure Search indexes.

An Azure search service can be deployed with `azuredeploy.json`. The `azure-pipelines.yml`
definition automates deployment using Azure Pipelines. Note that the default Azure Search SKU
is `free` and this has limits that will prevent all of the data being indexed.

The `indexes/` folder contains the index, datasource and indexer definitions:

- [`postcodes`](indexes/postcodes/) indexes the postcodes in the CSV file held in Blob storage.
See the [fn-ps-format-postcodes](https://github.com/weather-balloon/fn-ps-format-postcodes)
project for the PowerShell-based Function used to prep the data
- [`stations`](indexes/stations) indexes the weather station data in an Azure Storage Table.
See the [fn-process-weather-stations](https://github.com/weather-balloon/fn-process-weather-stations)
project for the Python-based Function used to prep the data

## The challenge

Azure Search always seems a little out of step with many of its Azure colleagues. The
setup of indexes is rather manual and requires either Portal- or API-based config
(i.e. no CLI). Further to this is the limited ability to udpate indexes and their related
datasources and indexers. This make it all a bit tricky in CD pipelines - it's almost
like they need an Azure Search DACPAC...

So I wrote a little Python script to try and do some of the basics:

- Create an index if it doesn't exist
- Update an index if possible or drop/re-create if needed (forced)
- Create/update an indexer
- Run an indexer and check its status
- Create/update a datasource
- Delete an index/indexer/datasource

## Running

The `configure_search` script provides a number of functions for setting up Azure Search. You can
check out the command with:

    pipenv run ./configure_search -h

The [ConfigArgParse](https://pypi.org/project/ConfigArgParse/) library is used so that
you can set parameters in a file or environment variables. The `azsearchconfig.empty` file
provides a template - just copy it to `.azsearchconfig` and add your settings,

_Note_: The script can read the `$servicePrincipalId`, `$servicePrincipalKey` and `$tenantId`
environment variables or accept them as parameters. These were selected to match the
[Azure CLI task's](https://docs.microsoft.com/en-us/azure/devops/pipelines/tasks/deploy/azure-cli?view=azure-devops)
`addSpnToEnvironment` parameter.

When setting up a datasource you can pass in the connection string via the command line
or an environment variable:

    export connectionString="<CONNECTION STRING>"

You can see the deployment script in `deploy/deploy-indexes.sh` for an example
of using the `configure_search` tool.


## References

* The data format is describe in https://download.geonames.org/export/zip/readme.txt
* [Create an Azure service principal with Azure CLI](https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli)
* Azure Search REST API:
  * [Index operations](https://docs.microsoft.com/en-au/rest/api/searchservice/index-operations)
  * [Indexer operations](https://docs.microsoft.com/en-au/rest/api/searchservice/indexer-operations)
* [Azure Search - index CSV Blobs](https://docs.microsoft.com/en-au/azure/search/search-howto-index-csv-blobs)
* [Azure REST API auth](https://docs.microsoft.com/en-us/rest/api/azure/#create-the-request)
  * [Calling Azure REST API via curl](https://medium.com/@mauridb/calling-azure-rest-api-via-curl-eb10a06127)
* [Service limits in Azure Search](https://docs.microsoft.com/en-au/azure/search/search-limits-quotas-capacity)
