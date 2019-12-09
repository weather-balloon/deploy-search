# Weather Stations index

## Example searches

Reference: <https://docs.microsoft.com/en-us/azure/search/query-simple-syntax>

Search for all documents:

    *

Search for a Term (`creek`):

    creek

Ok, seriously...

Get a basic listing

    $select=id,site,name,state

Get the record for a specific entry:

    searchFields=id&search=QVUuTlNXMDY4MTAw

Search for the term `creek` in the `name` field and get back the
`site`, `name` & `state` fields:

    searchFields=name&$select=site,name,state_name&search=creek

List all stations (and provide the count) that don't have an end year
(meaning that they are active):

    $count=true&$select=site,state,name,start_year,end_year&$filter=end_year eq null&search=*

Advancing that last one just a little to order the results by `name`, for NSW-based stations:

    $count=true&$select=site,state,name,start_year,end_year&$filter=end_year eq null&$orderby=name asc&searchField=state&search=NSW

### Map searching

The `location` field holds an `Edm.GeographyPoint` such as:

    "location": {
        "type": "Point",
        "coordinates": [
            151.0646,
            -33.8521
        ],
        "crs": {
            "type": "name",
            "properties": {
                "name": "EPSG:4326"
            }
        }
    }

As described in [Supported Types](https://docs.microsoft.com/en-au/rest/api/searchservice/Supported-data-types),
this uses the [GeoJSON "Point" type format](https://tools.ietf.org/html/rfc7946#appendix-A.1)
with a (longitude, latitude) pair. You can put the value
[`-33.8521,151.0646`](https://www.google.com/maps/place/33°51'07.6"S+151°03'52.6"E) into Google
maps and get the point - you just need to provide it as (latitude,longitude).

So, say we're at (`-33.8521,151.0646`) lat/long the following search will find the
weather stations near us:

    $filter=geo.distance(location, geography'POINT(151.0646 -33.8521)') le 1

Where `1` designates a 1km radius. Let's broaden our search:

    $filter=geo.distance(location, geography'POINT(151.0646 -33.8521)') le 5&$select=site,state,name,location

It's then possible to order by the distance:

    $filter=geo.distance(location, geography'POINT(151.0646 -33.8521)') le 5&$select=site,state,name&$orderby=geo.distance(location, geography'POINT(151.0646 -33.8521)')
