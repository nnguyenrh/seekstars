from dataclasses import dataclass

import httpx


GEONAMES_SEARCH_URL = "http://api.geonames.org/searchJSON"
GEONAMES_TIMEZONE_URL = "http://api.geonames.org/timezoneJSON"

DEFAULT_TIMEOUT = 10.0


class GeocodingError(Exception):
    pass


class CityNotFoundError(GeocodingError):
    pass


class GeoNamesAPIError(GeocodingError):
    pass


class GeoNamesNotConfiguredError(GeocodingError):
    pass


@dataclass
class GeocodingResult:
    city_name: str
    country: str
    country_code: str
    latitude: float
    longitude: float
    timezone: str


def search_city(
    city: str,
    username: str,
    max_rows: int = 5,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[GeocodingResult]:
    if not username:
        raise GeoNamesNotConfiguredError(
            "GeoNames username not configured. "
            "Set GEONAMES_USERNAME in .env or register at https://www.geonames.org/login"
        )

    try:
        response = httpx.get(
            GEONAMES_SEARCH_URL,
            params={
                "q": city,
                "maxRows": max_rows,
                "username": username,
                "style": "MEDIUM",
                "featureClass": "P",
            },
            timeout=timeout,
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        raise GeoNamesAPIError(f"GeoNames API timed out after {timeout}s")
    except httpx.HTTPStatusError as e:
        raise GeoNamesAPIError(f"GeoNames API returned HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        raise GeoNamesAPIError(f"GeoNames API unreachable: {e}")

    data = response.json()

    if "status" in data:
        raise GeoNamesAPIError(f"GeoNames error: {data['status'].get('message', 'Unknown error')}")

    geonames = data.get("geonames", [])
    if not geonames:
        raise CityNotFoundError(f"No results found for '{city}'")

    results = []
    for entry in geonames:
        lat = float(entry["lat"])
        lng = float(entry["lng"])

        tz = _lookup_timezone(lat, lng, username, timeout)

        country_name = entry.get("countryName", "")
        country_code = entry.get("countryCode", "")
        name = entry.get("name", city)

        display_parts = [name]
        admin1 = entry.get("adminName1", "")
        if admin1 and admin1 != name:
            display_parts.append(admin1)
        if country_name:
            display_parts.append(country_name)
        display_name = ", ".join(display_parts)

        results.append(GeocodingResult(
            city_name=display_name,
            country=country_name,
            country_code=country_code,
            latitude=lat,
            longitude=lng,
            timezone=tz,
        ))

    return results


def _lookup_timezone(
    lat: float,
    lng: float,
    username: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    try:
        response = httpx.get(
            GEONAMES_TIMEZONE_URL,
            params={
                "lat": lat,
                "lng": lng,
                "username": username,
            },
            timeout=timeout,
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        raise GeoNamesAPIError(f"GeoNames timezone API timed out after {timeout}s")
    except httpx.HTTPStatusError as e:
        raise GeoNamesAPIError(f"GeoNames timezone API returned HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        raise GeoNamesAPIError(f"GeoNames timezone API unreachable: {e}")

    data = response.json()

    if "status" in data:
        raise GeoNamesAPIError(f"GeoNames timezone error: {data['status'].get('message', 'Unknown error')}")

    tz_id = data.get("timezoneId")
    if not tz_id:
        raise GeoNamesAPIError(f"No timezone found for coordinates ({lat}, {lng})")

    return tz_id


def geocode_city(
    city: str,
    username: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> GeocodingResult:
    results = search_city(city, username, max_rows=1, timeout=timeout)
    return results[0]
