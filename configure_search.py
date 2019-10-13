#!/usr/bin/env python3

import os
import sys
import argparse
import requests
import json
from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.search.operations import ServicesOperations


def get_sp_credentials(app_id: str, app_password: str, tenant: str) -> ServicePrincipalCredentials:

    credentials = ServicePrincipalCredentials(
        client_id=app_id,
        secret=app_password,
        tenant=tenant
    )
    return credentials


class AzureSearchService:

    def __init__(self, credentials: ServicePrincipalCredentials, search_service_name: str, resource_group: str, subscription: str, api_version: str = '2019-05-06'):
        self.credentials = credentials
        self.search_service_name = search_service_name
        self.resource_group = resource_group
        self.subscription = subscription
        self.admin_key = self._get_admin_key()
        self.api_version = api_version

    def _get_admin_key(self) -> str:

        client = SearchManagementClient(
            self.credentials, self.subscription)

        keys = client.admin_keys.get(
            self.resource_group, self.search_service_name)

        return keys.primary_key

    def submit_request(self, function: str, payload: str = "", method: str = "GET"):
        request_headers = {
            'api-key': self.admin_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        request_parameters = {
            'api-version': self.api_version
        }

        request_url = f"https://{self.search_service_name}.search.windows.net/{function}"

        if method == "POST":
            response = requests.post(
                request_url, params=request_parameters, headers=request_headers, data=payload)
        elif method == "DELETE":
            response = requests.delete(
                request_url, params=request_parameters, headers=request_headers)
        else:
            response = requests.get(
                request_url, params=request_parameters, headers=request_headers)

        if not response.ok:
            raise requests.exceptions.HTTPError(
                f"The call to Azure Search failed with a response of {response.status_code}: {response.text}")

        return response

    def create_index(self, index_definition: str):
        return self.submit_request(function='indexes', payload=index_definition, method="POST").json()

    def list_indexes(self):
        result = self.submit_request(function='indexes').json()['value']
        return result

    def delete_index(self, name: str):
        return self.submit_request(function=f'indexes/{name}', method="DELETE")

    def list_datasources(self):
        return self.submit_request(function='datasources').json()['value']

    def create_datasource(self, datasource_definition: str):
        return self.submit_request(function='datasources', payload=datasource_definition, method="POST").json()

    def delete_datasource(self, name: str):
        return self.submit_request(function=f"datasources/{name}", method="DELETE")

    def list_indexers(self):
        return self.submit_request(function='indexers').json()['value']

    def create_indexer(self, indexer_definition: str):
        return self.submit_request(function='indexers', payload=indexer_definition, method="POST").json()

    def delete_indexer(self, name: str):
        return self.submit_request(function=f'indexers/{name}', method="DELETE")


def get_cred_vars():
    return {
        'tenantId': os.environ.get('tenantId'),
        'servicePrincipalId': os.environ.get('servicePrincipalId'),
        'servicePrincipalKey': os.environ.get('servicePrincipalKey')
    }


def handle_index_command(searchService, args):
    if args.function == 'list':
        listing = searchService.list_indexes()
        print(listing)
        return
    elif args.function == 'create':
        if not args.file:
            print('Error: no definition file provided', file=sys.stderr)
            sys.exit(1)
        else:
            with open(args.file, 'r') as f:
                result = searchService.create_index(f.read())
            print(result)
            return
    elif args.function == 'delete':
        if not args.name:
            print('Error: no index name provided', file=sys.stderr)
            sys.exit(1)
        else:
            result = searchService.delete_index(args.name)
            print(result)
            return


def handle_datasource_command(searchService, args):
    if args.function == 'list':
        listing = searchService.list_datasources()
        print(listing)
        return
    elif args.function == 'create':
        if not args.file:
            print('Error: no definition file provided', file=sys.stderr)
            sys.exit(1)
        elif not args.connectionString:
            print('Error: no connection string provided', file=sys.stderr)
            sys.exit(1)
        else:
            with open(args.file, 'r') as f:
                ds_base = json.load(f)
            ds_base['credentials'] = {
                'connectionString': args.connectionString
            }
            ds_defintion = json.dumps(ds_base)
            result = searchService.create_datasource(ds_defintion)
            print(result)
            return
    elif args.function == 'delete':
        if not args.name:
            print('Error: no indexer name provided', file=sys.stderr)
            sys.exit(1)
        else:
            result = searchService.delete_indexer(args.name)
            print(result)
            return


def handle_indexer_command(searchService, args):
    if args.function == 'list':
        listing = searchService.list_indexers()
        print(listing)
        return
    elif args.function == 'create':
        if not args.file:
            print('Error: no definition file provided', file=sys.stderr)
            sys.exit(1)
        else:
            with open(args.file, 'r') as f:
                result = searchService.create_indexer(f.read())
            print(result)
            return
    elif args.function == 'delete':
        if not args.name:
            print('Error: no indexer name provided', file=sys.stderr)
            sys.exit(1)
        else:
            result = searchService.delete_indexer(args.name)
            print(result)
            return


if __name__ == "__main__":

    parent_parser = argparse.ArgumentParser(add_help=False)

    parent_parser.add_argument('--tenantId',
                               help='The tenant ID')

    parent_parser.add_argument('--servicePrincipalId',
                               help='The client (service principal) ID')

    parent_parser.add_argument('--servicePrincipalKey',
                               help='The client (service principal) password')

    parent_parser.add_argument('subscription',
                               help='The subscription housing the search service')

    parent_parser.add_argument('resourceGroup',
                               help='The resource group housing the search service')

    parent_parser.add_argument('searchServiceName',
                               help='The name of the search service')

    parser = argparse.ArgumentParser(
        description='Configure an Azure Search index.',
        parents=[parent_parser]
    )

    subparsers = parser.add_subparsers(help='Sub command help')

    parser_index = subparsers.add_parser('index', help='Index configuration')

    parser_index.add_argument('function',
                              choices=['list', 'create', 'delete'])

    parser_index.add_argument('--name',
                              help='The index name (required for delete)')

    parser_index.add_argument('--file',
                              help='The index definition (required for create)')

    parser_index.set_defaults(func=handle_index_command)

    parser_datasource = subparsers.add_parser(
        'datasource', help='Datasource configuration')

    parser_datasource.add_argument('function',
                                   choices=['list', 'create', 'delete'])

    parser_datasource.add_argument('--name',
                                   help='The datasource name (required for delete)')

    parser_datasource.add_argument('--file',
                                   help='The datasource definition (required for create)')

    parser_datasource.add_argument('--connectionString',
                                   help='The datasource connection string (required for create)')

    parser_datasource.set_defaults(func=handle_datasource_command)

    parser_indexer = subparsers.add_parser(
        'indexer', help='Indexer configuration')

    parser_indexer.add_argument('function',
                                choices=['list', 'create', 'delete'])

    parser_indexer.add_argument('--name',
                                help='The indexer name (required for delete)')

    parser_indexer.add_argument('--file',
                                help='The indexer definition (required for create)')

    parser_indexer.set_defaults(func=handle_indexer_command)

    args = parser.parse_args()

    cred_params = get_cred_vars()

    if args.tenantId:
        cred_params['tenantId'] = args.tenantId

    if not cred_params['tenantId']:
        print('Error: no tenantId provided', file=sys.stderr)
        sys.exit(1)

    if args.servicePrincipalId:
        cred_params['servicePrincipalId'] = args.servicePrincipalId

    if not cred_params['servicePrincipalId']:
        print('Error: no servicePrincipalId provided', file=sys.stderr)
        sys.exit(1)

    if args.servicePrincipalKey:
        cred_params['servicePrincipalKey'] = args.servicePrincipalKey

    if not cred_params['servicePrincipalKey']:
        print('Error: no servicePrincipalKey provided', file=sys.stderr)
        sys.exit(1)

    credentials = get_sp_credentials(
        tenant=cred_params['tenantId'],
        app_id=cred_params['servicePrincipalId'],
        app_password=cred_params['servicePrincipalKey']
    )

    searchService = AzureSearchService(
        credentials=credentials,
        subscription=args.subscription,
        resource_group=args.resourceGroup,
        search_service_name=args.searchServiceName
    )

    args.func(searchService, args)
    sys.exit(0)
