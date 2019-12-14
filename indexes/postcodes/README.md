# Postcodes index

Provides an index of postcodes (as you guessed).

## Example searches

Basic initial search with facet count for the `state_name`

    $count=true&facet=state_name

Add in the `country_code` facet:

    $count=true&facet=state_name&facet=country_code

### Suggester

The `place_name` suggester is a handy way to help guide the user with possible matches:

    https://wb-search-dev.search.windows.net/indexes/postcodes/docs/suggest?api-version=2019-05-06&suggesterName=place_name&search=Melr

The suggester results can be enhanced with extra fields:

    https://wb-search-dev.search.windows.net/indexes/postcodes/docs/suggest?api-version=2019-05-06&suggesterName=place_name&search=Melr&$select=place_name,state_name,postal_code

### Map searching

Say we're at (`-33.8521,151.0646`) lat/long the following search will find the
places (suburbs) no more than 5km from us:

    $count=true&$filter=geo.distance(location, geography'POINT(151.0646 -33.8521)') le 5

Add in some facets to help the user:

    $count=true&$filter=geo.distance(location, geography'POINT(151.0646 -33.8521)') le 5&facet=postal_code&facet=state_code
