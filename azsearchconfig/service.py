
import json
import requests
import logging
from collections import namedtuple
from typing import Tuple
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.search import SearchManagementClient


class IndexExistsException(Exception):
    pass


AzureSearchServiceApiResult = namedtuple(
    'AzureSearchServiceApiResult', ['result', 'error'])

AzureSearchServiceResult = namedtuple(
    'AzureSearchServiceResult', ['result', 'error'])


AzureSearchServiceRequestError = namedtuple('AzureSearchServiceRequestError', [
                                            'url', 'status_code', 'message'])


class AzureSearchService:

    def __init__(self, credentials: ServicePrincipalCredentials, search_service_name: str, resource_group: str, subscription: str, api_version: str = '2019-05-06', logger=None):
        self.credentials = credentials
        self.search_service_name = search_service_name
        self.resource_group = resource_group
        self.subscription = subscription
        self.admin_key = self._get_admin_key()
        self.api_version = api_version
        self.logger = logger or logging.getLogger(__name__)

    def _get_admin_key(self) -> str:

        client = SearchManagementClient(
            self.credentials, self.subscription)

        keys = client.admin_keys.get(
            self.resource_group, self.search_service_name)

        return keys.primary_key

    def submit_request(self, function: str, payload: str = "", method: str = "GET") -> AzureSearchServiceApiResult:
        request_headers = {
            'api-key': self.admin_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        request_parameters = {
            'api-version': self.api_version
        }

        request_url = f"https://{self.search_service_name}.search.windows.net/{function}"
        self.logger.debug(request_url)

        response = None

        if method == "POST":
            response = requests.post(
                request_url, params=request_parameters, headers=request_headers, data=payload)
        elif method == "DELETE":
            response = requests.delete(
                request_url, params=request_parameters, headers=request_headers)
        else:
            response = requests.get(
                request_url, params=request_parameters, headers=request_headers)

        self.logger.debug(response.text)

        err = None
        if not response.ok:
            err = AzureSearchServiceRequestError(
                request_url, response.status_code, json.loads(response.text))

        return AzureSearchServiceResult(result=response, error=err)

    def list_indexes(self) -> AzureSearchServiceResult:
        result, err = self.submit_request(function='indexes')
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json()['value'], None)

    def get_index(self, name: str) -> AzureSearchServiceResult:
        result, err = self.submit_request(
            function=f'indexes/{name}')
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)

    def delete_index(self, name: str) -> AzureSearchServiceResult:
        _, err = self.submit_request(
            function=f'indexes/{name}', method="DELETE")
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult({}, None)

    def update_index(self, index_definition: str) -> AzureSearchServiceResult:
        new_index = json.loads(index_definition)
        index_name = new_index['name']

        result, err = self.submit_request(
            function=f'indexes/{index_name}', payload=index_definition, method="PUT")
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)

    def create_index(self, index_definition: str, update: bool = False, force: bool = False) -> AzureSearchServiceResult:
        new_index = json.loads(index_definition)
        index_name = new_index['name']

        result = None
        err = None

        current_index, _ = self.get_index(index_name)

        if not current_index:
            result, err = self.submit_request(
                function='indexes', payload=index_definition, method="POST")

        elif update:
            # Try to perform an update
            result, err = self.update_index(index_definition)
            if not err:
                return AzureSearchServiceResult(result, None)
            elif err and force:
                # Didn't work so drop and recreate if allowed
                self.delete_index(index_name)
                result, err = self.submit_request(
                    function='indexes', payload=index_definition, method="POST")
        else:
            err = AzureSearchServiceRequestError(
                "", 400, "The index already exists")

        if not err:
            return AzureSearchServiceResult(result.json(), None)
        else:
            return AzureSearchServiceResult(None, err)

    def list_datasources(self) -> AzureSearchServiceResult:
        result, err = self.submit_request(
            function='datasources')
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)

    def get_datasource(self, name: str) -> AzureSearchServiceResult:
        result, err = self.submit_request(
            function=f'datasources/{name}')
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)

    def delete_datasource(self, name: str) -> AzureSearchServiceResult:
        _, err = self.submit_request(
            function=f'datasources/{name}', method="DELETE")
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult({}, None)

    def create_datasource(self, datasource_definition: str, update: bool = False) -> AzureSearchServiceResult:
        ds_name = None
        ds = None

        if update:
            ds_name = json.loads(datasource_definition)['name']
            ds, _ = self.get_datasource(ds_name)
            if ds:
                return self.update_datasource(datasource_definition, ds_name)

        result, err = self.submit_request(
            function='datasources', payload=datasource_definition, method="POST")
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)

    def update_datasource(self, datasource_definition: str, name: str = None) -> AzureSearchServiceResult:
        if name:
            ds_name = name
        else:
            ds_name = json.loads(datasource_definition)['name']

        result, err = self.submit_request(
            function=f'datasources/{ds_name}', payload=datasource_definition, method="PUT")
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)

    def list_indexers(self) -> AzureSearchServiceResult:
        result, err = self.submit_request(
            function='indexers')
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)

    def get_indexer(self, name: str) -> AzureSearchServiceResult:
        result, err = self.submit_request(
            function=f'indexers/{name}')
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)

    def delete_indexer(self, name: str) -> AzureSearchServiceResult:
        _, err = self.submit_request(
            function=f'indexers/{name}', method="DELETE")
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult({}, None)

    def create_indexer(self, indexer_definition: str, update: bool = False) -> AzureSearchServiceResult:
        ixr_name = None

        if update:
            ixr_name = json.loads(indexer_definition)['name']
            ixr, _ = self.get_indexer(ixr_name)
            if ixr:
                return self.update_indexer(indexer_definition, ixr_name)

        result, err = self.submit_request(
            function='indexers', payload=indexer_definition, method="POST")
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)

    def update_indexer(self, indexer_definition: str, name: str = None) -> AzureSearchServiceResult:

        if name:
            ixr_name = name
        else:
            ixr_name = json.loads(indexer_definition)['name']

        result, err = self.submit_request(
            function=f'indexers/{ixr_name}', payload=indexer_definition, method="PUT")
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)

    def run_indexer(self, name: str = None) -> AzureSearchServiceResult:
        _, err = self.submit_request(
            function=f'indexers/{name}/run', method="POST")
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult({}, None)

    def status_indexer(self, name: str = None) -> AzureSearchServiceResult:
        result, err = self.submit_request(
            function=f'indexers/{name}/status', method="GET")
        if err:
            return AzureSearchServiceResult(None, err)
        else:
            return AzureSearchServiceResult(result.json(), None)
