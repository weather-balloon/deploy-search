import json
import sys

from collections import namedtuple

import configargparse

from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import ServicePrincipalCredentials

from . import (IndexExistsException, AzureSearchService)

CliResult = namedtuple(
    'CliResult', ['result', 'error'])


def get_sp_credentials(app_id: str, app_password: str, tenant: str) -> ServicePrincipalCredentials:

    credentials = ServicePrincipalCredentials(
        client_id=app_id,
        secret=app_password,
        tenant=tenant
    )
    return credentials


def handle_indexer_command(searchService, args):
    if args.function == 'list':
        listing = searchService.list_indexers()
        print(listing)
        return
    elif args.function == 'get':
        if not args.name:
            print('Error: no indexer name provided', file=sys.stderr)
            sys.exit(1)
        else:
            listing = searchService.get_indexer(args.name)
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


def create_index_command(parser_index):

    def list_index_handler(searchService, args) -> CliResult:
        result, err = searchService.list_indexes()
        return CliResult(result, err)

    def get_index_handler(searchService, args) -> CliResult:
        result, err = searchService.get_index(args.name)
        return CliResult(result, err)

    def del_index_handler(searchService, args) -> CliResult:
        result, err = searchService.delete_index(args.name)
        return CliResult(result, err)

    def create_index_handler(searchService, args) -> CliResult:
        result = err = None

        with open(args.file, 'r') as f:
            result, err = searchService.create_index(f.read(), args.force)
        return CliResult(result, err)

    def update_index_handler(searchService, args) -> CliResult:
        result = err = None
        with open(args.file, 'r') as f:
            result, err = searchService.update_index(f.read())
        return CliResult(result, err)

    index_cmd = parser_index.add_subparsers(
        help='Search index commands',
        required=True
    )

    index_cmd.add_parser('list', help='List all indexes').set_defaults(
        func=list_index_handler)

    get_index = index_cmd.add_parser('get', help='Get an index')
    get_index.add_argument(
        'name', help='The index name')
    get_index.set_defaults(func=get_index_handler)

    del_index = index_cmd.add_parser('delete', help='Delete an index')
    del_index.add_argument(
        'name', help='The index name')
    del_index.set_defaults(func=del_index_handler)

    create_index = index_cmd.add_parser('create', help='Create an index')
    create_index.add_argument('--update',
                              action='store_true',
                              help="Will attempt an update if the index exists")
    create_index.add_argument('--force',
                              action='store_true',
                              help="Will force an existing index to be dropped and re-created if it can't be updated")
    create_index.add_argument('--file', required=True,
                              help='The index definition')
    create_index.set_defaults(func=create_index_handler)

    update_index = index_cmd.add_parser('update', help='Update an index')
    update_index.add_argument('--file', required=True,
                              help='The index definition')
    update_index.set_defaults(func=update_index_handler)

    return parser_index


def create_datasource_command(parser_datasource):
    def list_datasource_handler(searchService, args) -> CliResult:
        result, err = searchService.list_datasources()
        return CliResult(result, err)

    def get_datasource_handler(searchService, args) -> CliResult:
        result, err = searchService.get_datasource(args.name)
        return CliResult(result, err)

    def del_datasource_handler(searchService, args) -> CliResult:
        result, err = searchService.delete_datasource(args.name)
        return CliResult(result, err)

    def prepare_datasource_config(config_file: str, connectionString: str):
        with open(config_file, 'r') as f:
            ds_base = json.load(f)

        ds_base['credentials'] = {
            'connectionString': connectionString
        }
        return json.dumps(ds_base)

    def create_datasource_handler(searchService, args) -> CliResult:
        result = err = None

        result, err = searchService.create_datasource(
            prepare_datasource_config(args.file, args.connectionString),
            update=args.update)
        return CliResult(result, err)

    def update_datasource_handler(searchService, args) -> CliResult:
        result = err = None

        result, err = searchService.update_datasource(
            prepare_datasource_config(
                args.file, args.connectionString))
        return CliResult(result, err)

    datasource_cmd = parser_datasource.add_subparsers(
        help='Search datasource commands',
        required=True
    )

    datasource_cmd.add_parser('list', help='List all datasources').set_defaults(
        func=list_datasource_handler)

    get_datasource = datasource_cmd.add_parser('get', help='Get a datasource')
    get_datasource.add_argument(
        'name', help='The datasource name')
    get_datasource.set_defaults(func=get_datasource_handler)

    del_datasource = datasource_cmd.add_parser(
        'delete', help='Delete a datasource')
    del_datasource.add_argument(
        'name', help='The datasource name')
    del_datasource.set_defaults(func=del_datasource_handler)

    create_datasource = datasource_cmd.add_parser(
        'create', help='Create a datasource')
    create_datasource.add_argument('--file', required=True,
                                   help='The datasource definition')
    create_datasource.add_argument('--update',
                                   action='store_true',
                                   help="Will attempt an update if the datasource exists")
    create_datasource.add_argument('--connectionString', required=True,
                                   env_var='connectionString',
                                   help='The Connection String used by the datasource')
    create_datasource.set_defaults(func=create_datasource_handler)

    update_datasource = datasource_cmd.add_parser(
        'update', help='Update a datasource')
    update_datasource.add_argument('--file', required=True,
                                   help='The datasource definition')
    update_datasource.add_argument('--connectionString', required=True,
                                   env_var='connectionString',
                                   help='The Connection String used by the datasource')
    update_datasource.set_defaults(func=update_datasource_handler)

    return parser_datasource


def create_indexer_command(parser_indexer):

    def list_indexer_handler(searchService, args) -> CliResult:
        result, err = searchService.list_indexers()
        return CliResult(result, err)

    def get_indexer_handler(searchService, args) -> CliResult:
        result, err = searchService.get_indexer(args.name)
        return CliResult(result, err)

    def del_indexer_handler(searchService, args) -> CliResult:
        result, err = searchService.delete_indexer(args.name)
        return CliResult(result, err)

    def run_indexer_handler(searchService, args) -> CliResult:
        result, err = searchService.run_indexer(args.name)
        return CliResult(result, err)

    def status_indexer_handler(searchService, args) -> CliResult:
        result, err = searchService.status_indexer(args.name)
        return CliResult(result, err)

    def create_indexer_handler(searchService, args) -> CliResult:
        result = err = None

        with open(args.file, 'r') as f:
            result, err = searchService.create_indexer(
                f.read(), update=args.update)
        return CliResult(result, err)

    def update_indexer_handler(searchService, args) -> CliResult:
        result = err = None
        with open(args.file, 'r') as f:
            result, err = searchService.update_indexer(f.read())
        return CliResult(result, err)

    indexer_cmd = parser_indexer.add_subparsers(
        help='Search indexer commands',
        required=True
    )

    indexer_cmd.add_parser('list', help='List all indexeres').set_defaults(
        func=list_indexer_handler)

    get_indexer = indexer_cmd.add_parser('get', help='Get an indexer')
    get_indexer.add_argument(
        'name', help='The indexer name')
    get_indexer.set_defaults(func=get_indexer_handler)

    run_indexer = indexer_cmd.add_parser('run', help='Run an indexer')
    run_indexer.add_argument(
        'name', help='The indexer name')
    run_indexer.set_defaults(func=run_indexer_handler)

    status_indexer = indexer_cmd.add_parser(
        'status', help='Get the status of an indexer')
    status_indexer.add_argument(
        'name', help='The indexer name')
    status_indexer.set_defaults(func=status_indexer_handler)

    del_indexer = indexer_cmd.add_parser('delete', help='Delete an indexer')
    del_indexer.add_argument(
        'name', help='The indexer name')
    del_indexer.set_defaults(func=del_indexer_handler)

    create_indexer = indexer_cmd.add_parser('create', help='Create an indexer')
    create_indexer.add_argument('--update',
                                action='store_true',
                                help="Will attempt an update if the indexer exists")
    create_indexer.add_argument('--file', required=True,
                                help='The indexer definition')
    create_indexer.set_defaults(func=create_indexer_handler)

    update_indexer = indexer_cmd.add_parser('update', help='Update an indexer')
    update_indexer.add_argument('--file', required=True,
                                help='The indexer definition')
    update_indexer.set_defaults(func=update_indexer_handler)

    return parser_indexer


def create_parent_parser():
    parent_parser = configargparse.ArgumentParser(add_help=False)

    parent_parser.add('-c', '--config',
                      required=False,
                      is_config_file=True,
                      default='.azsearchconfig',
                      help='config file path')

    parent_parser.add_argument('--tenantId',
                               required=True,
                               env_var='tenantId',
                               help='The tenant ID')

    parent_parser.add_argument('--servicePrincipalId',
                               required=True,
                               env_var='servicePrincipalId',
                               help='The client (service principal) ID')

    parent_parser.add_argument('--servicePrincipalKey',
                               required=True,
                               env_var='servicePrincipalKey',
                               help='The client (service principal) password')

    parent_parser.add_argument('--subscription',
                               required=True,
                               env_var='subscription',
                               help='The subscription housing the search service')

    parent_parser.add_argument('--resourceGroup',
                               required=True,
                               env_var='resourceGroup',
                               help='The resource group housing the search service')

    parent_parser.add_argument('--searchServiceName',
                               required=True,
                               env_var='searchServiceName',
                               help='The name of the search service')

    return parent_parser


def create_parser():

    parser = configargparse.ArgumentParser(
        description='Configure an Azure Search index.',
        parents=[create_parent_parser()],
        formatter_class=configargparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = parser.add_subparsers(
        required=True,
        parser_class=configargparse.ArgumentParser,
        dest='sub_command',
        help='Sub command help')

    create_index_command(subparsers.add_parser(
        'index', help='Index configuration'))

    create_datasource_command(subparsers.add_parser(
        'datasource', help='Datasource configuration'))

    create_indexer_command(subparsers.add_parser(
        'indexer', help='Indexer configuration'))

    return parser


def cli():
    parser = create_parser()

    args = parser.parse_args()

    credentials = get_sp_credentials(
        tenant=args.tenantId,
        app_id=args.servicePrincipalId,
        app_password=args.servicePrincipalKey
    )

    searchService = AzureSearchService(
        credentials=credentials,
        subscription=args.subscription,
        resource_group=args.resourceGroup,
        search_service_name=args.searchServiceName
    )

    result, err = args.func(searchService, args)

    if err:
        print(json.dumps(err._asdict()), file=sys.stderr)
        sys.exit(1)
    else:
        print(json.dumps(result))
        sys.exit(0)
