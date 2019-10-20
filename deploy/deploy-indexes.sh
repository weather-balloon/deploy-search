#!/bin/bash -xe

export subscription=$(az account show --query id --output tsv)

export datalakeKey=$(az storage account keys list --account-name ${datalakeAccountName} --resource-group ${datalakeResourceGroup} --query [0].value --output tsv)

export connectionString="DefaultEndpointsProtocol=https;AccountName=${datalakeAccountName};AccountKey=${datalakeKey};EndpointSuffix=core.windows.net"

touch .azsearchconfig

pipenv run ./configure_search index create \
    --file indexes/postcodes/postcodes-index.json \
    --update --force

pipenv run ./configure_search datasource create \
    --file indexes/postcodes/postcodes-datasource.json \
    --update

pipenv run ./configure_search indexer create \
    --file indexes/postcodes/postcodes-csvindexer.json \
    --update

pipenv run ./configure_search index create \
    --file indexes/stations/stations-index.json \
    --update --force

pipenv run ./configure_search datasource create \
    --file indexes/stations/stations-datasource.json \
    --update

pipenv run ./configure_search indexer create \
    --file indexes/stations/stations-tableindexer.json \
    --update

export connectionString=
export datalakeKey=
export subscription=
