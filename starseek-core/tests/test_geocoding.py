import pytest
import httpx
import respx

from starseek.services.geocoding import (
    search_city, geocode_city,
    GeocodingResult, CityNotFoundError, GeoNamesAPIError, GeoNamesNotConfiguredError,
    GEONAMES_SEARCH_URL, GEONAMES_TIMEZONE_URL,
)


MOCK_USERNAME = "testuser"

MOCK_SEARCH_RESPONSE = {
    "totalResultsCount": 1,
    "geonames": [
        {
            "geonameId": 5128581,
            "name": "New York City",
            "lat": "40.71427",
            "lng": "-74.00597",
            "countryName": "United States",
            "countryCode": "US",
            "adminName1": "New York",
        }
    ],
}

MOCK_TIMEZONE_RESPONSE = {
    "timezoneId": "America/New_York",
    "gmtOffset": -5,
    "dstOffset": -4,
}

MOCK_SEARCH_MULTI = {
    "totalResultsCount": 2,
    "geonames": [
        {
            "geonameId": 2643743,
            "name": "London",
            "lat": "51.50853",
            "lng": "-0.12574",
            "countryName": "United Kingdom",
            "countryCode": "GB",
            "adminName1": "England",
        },
        {
            "geonameId": 4517009,
            "name": "London",
            "lat": "39.88645",
            "lng": "-83.44825",
            "countryName": "United States",
            "countryCode": "US",
            "adminName1": "Ohio",
        },
    ],
}


class TestSearchCity:
    @respx.mock
    def test_successful_search(self):
        respx.get(GEONAMES_SEARCH_URL).mock(
            return_value=httpx.Response(200, json=MOCK_SEARCH_RESPONSE)
        )
        respx.get(GEONAMES_TIMEZONE_URL).mock(
            return_value=httpx.Response(200, json=MOCK_TIMEZONE_RESPONSE)
        )

        results = search_city("New York", MOCK_USERNAME)
        assert len(results) == 1
        assert results[0].latitude == pytest.approx(40.71427)
        assert results[0].longitude == pytest.approx(-74.00597)
        assert results[0].timezone == "America/New_York"
        assert results[0].country_code == "US"
        assert "New York" in results[0].city_name

    @respx.mock
    def test_multiple_results(self):
        respx.get(GEONAMES_SEARCH_URL).mock(
            return_value=httpx.Response(200, json=MOCK_SEARCH_MULTI)
        )
        respx.get(GEONAMES_TIMEZONE_URL).mock(
            return_value=httpx.Response(200, json={"timezoneId": "Europe/London"})
        )

        results = search_city("London", MOCK_USERNAME, max_rows=5)
        assert len(results) == 2
        assert results[0].country_code == "GB"
        assert results[1].country_code == "US"

    @respx.mock
    def test_no_results(self):
        respx.get(GEONAMES_SEARCH_URL).mock(
            return_value=httpx.Response(200, json={"totalResultsCount": 0, "geonames": []})
        )

        with pytest.raises(CityNotFoundError):
            search_city("Nonexistentcityxyz", MOCK_USERNAME)

    def test_no_username(self):
        with pytest.raises(GeoNamesNotConfiguredError):
            search_city("New York", "")

    @respx.mock
    def test_api_error_status(self):
        respx.get(GEONAMES_SEARCH_URL).mock(
            return_value=httpx.Response(200, json={"status": {"message": "limit exceeded", "value": 19}})
        )

        with pytest.raises(GeoNamesAPIError, match="limit exceeded"):
            search_city("New York", MOCK_USERNAME)

    @respx.mock
    def test_api_http_error(self):
        respx.get(GEONAMES_SEARCH_URL).mock(
            return_value=httpx.Response(500)
        )

        with pytest.raises(GeoNamesAPIError, match="HTTP 500"):
            search_city("New York", MOCK_USERNAME)

    @respx.mock
    def test_api_timeout(self):
        respx.get(GEONAMES_SEARCH_URL).mock(
            side_effect=httpx.ReadTimeout("timed out")
        )

        with pytest.raises(GeoNamesAPIError, match="timed out"):
            search_city("New York", MOCK_USERNAME, timeout=1.0)

    @respx.mock
    def test_api_connection_error(self):
        respx.get(GEONAMES_SEARCH_URL).mock(
            side_effect=httpx.ConnectError("connection refused")
        )

        with pytest.raises(GeoNamesAPIError, match="unreachable"):
            search_city("New York", MOCK_USERNAME)


class TestGeocodeCity:
    @respx.mock
    def test_returns_first_result(self):
        respx.get(GEONAMES_SEARCH_URL).mock(
            return_value=httpx.Response(200, json=MOCK_SEARCH_RESPONSE)
        )
        respx.get(GEONAMES_TIMEZONE_URL).mock(
            return_value=httpx.Response(200, json=MOCK_TIMEZONE_RESPONSE)
        )

        result = geocode_city("New York", MOCK_USERNAME)
        assert isinstance(result, GeocodingResult)
        assert result.timezone == "America/New_York"
