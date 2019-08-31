# Azure Search configuration for GeoNames postcodes

[![Build Status](https://dev.azure.com/weatherballoon/Weather%20Balloon/_apis/build/status/weather-balloon.deploy-search?branchName=master)](https://dev.azure.com/weatherballoon/Weather%20Balloon/_build/latest?definitionId=13&branchName=master)

## Background

Login:

    az login

Check for locations with:

    az account list-locations

Get a list of roles relating to search:

    az role definition list --query "[].{Name: name, Description: description, Role_Name: roleName}[?contains(Role_Name, 'Search')]" -o table

You'll need to setup a service principal and store its details in a Key Vault:

```bash
SP_NAME=wb-search-configurator
AZURE_KEYVAULT_RG=wb-management
AZURE_KEYVAULT_LOCATION=centralus
AZURE_KEYVAULT_NAME=wb-key-vault
AZURE_SEARCH_NAME=wb-search-test
AZURE_SEARCH_RG=wb-search

# Check to see if KV exists, create if not
az keyvault show --name $AZURE_KEYVAULT_NAME --resource-group $AZURE_KEYVAULT_RG || \
    az keyvault create --name $AZURE_KEYVAULT_NAME \
                    --resource-group $AZURE_KEYVAULT_RG \
                    --location $AZURE_KEYVAULT_LOCATION \
                    --tags environment=management service=wb-management

# Generate the SP and store the password in KV
az keyvault secret set \
    --vault-name $AZURE_KEYVAULT_NAME \
    --name $SP_NAME-password \
    --value $(az ad sp create-for-rbac \
                    --name "https://$SP_NAME" \
                    --scopes $(az search service show --name $AZURE_SEARCH_NAME --resource-group $AZURE_SEARCH_RG --query id --output tsv) \
                    --role "Search Service Contributor" \
                    --query password \
                    --output tsv)

# Add the SP username to KV
az keyvault secret set \
    --vault-name $AZURE_KEYVAULT_NAME \
    --name $SP_NAME-user \
    --value $SP_NAME
```

To find the service principal:

    az ad sp list --spn http://$SP_NAME


## References

* The data format is describe in https://download.geonames.org/export/zip/readme.txt
* [Create an Azure service principal with Azure CLI](https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli)
* Azure Search REST API:
  * [Index operations](https://docs.microsoft.com/en-au/rest/api/searchservice/index-operations)
  * [Indexer operations](https://docs.microsoft.com/en-au/rest/api/searchservice/indexer-operations)
* [Azure Search - index CSV Blobs](https://docs.microsoft.com/en-au/azure/search/search-howto-index-csv-blobs)
* [Azure REST API auth](https://docs.microsoft.com/en-us/rest/api/azure/#create-the-request)
  * [Calling Azure REST API via curl](https://medium.com/@mauridb/calling-azure-rest-api-via-curl-eb10a06127)
