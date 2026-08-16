import sys
from datetime import datetime
from typing import Optional

import click

from starseek.config import get_settings
from starseek.models.enums import HouseSystem
from starseek.models.input import BirthData
from starseek.core.chart import build_chart
from starseek.formatters.json_fmt import to_json
from starseek.formatters.markdown_fmt import to_markdown
from starseek.services.storage import (
    init_db, save_chart, load_chart, list_charts, delete_chart,
    cache_location, get_cached_location,
)
from starseek.services.geocoding import (
    geocode_city, search_city,
    GeocodingError, CityNotFoundError, GeoNamesNotConfiguredError,
)


@click.group()
@click.pass_context
def cli(ctx):
    """StarSeek - Astrological birth chart generator."""
    ctx.ensure_object(dict)
    ctx.obj["settings"] = get_settings()


@cli.command()
@click.option("--name", "-n", default=None, help="Name of the person.")
@click.option("--datetime", "dt", required=True, help="Birth date/time (ISO 8601, e.g. '1990-06-15T14:30:00').")
@click.option("--city", "-c", default=None, help="City of birth (triggers geocoding).")
@click.option("--lat", type=float, default=None, help="Birth latitude.")
@click.option("--lng", type=float, default=None, help="Birth longitude.")
@click.option("--tz", default=None, help="IANA timezone (e.g. 'America/New_York').")
@click.option("--houses", type=click.Choice(["placidus", "whole-sign"], case_sensitive=False),
              default=None, help="House system (default from config).")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "markdown"], case_sensitive=False),
              default="json", help="Output format.")
@click.option("--save/--no-save", default=False, help="Save chart to database.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-data output.")
@click.pass_context
def chart(ctx, name, dt, city, lat, lng, tz, houses, fmt, save, quiet):
    """Generate a birth chart."""
    settings = ctx.obj["settings"]

    try:
        birth_dt = datetime.fromisoformat(dt)
    except ValueError:
        click.echo(f"Error: Invalid datetime format '{dt}'. Use ISO 8601 (e.g. 1990-06-15T14:30:00).", err=True)
        sys.exit(1)

    settings = ctx.obj["settings"]
    if houses is None:
        house_system = settings.default_house_system
    elif houses == "whole-sign":
        house_system = HouseSystem.WHOLE_SIGN
    else:
        house_system = HouseSystem.PLACIDUS

    if city:
        resolved = _resolve_city(city, settings.db_path, settings.geonames_username, quiet)
        if resolved is None:
            sys.exit(1)
        lat = resolved.latitude
        lng = resolved.longitude
        tz = resolved.timezone
        location_name = resolved.city_name
    elif lat is not None and lng is not None and tz is not None:
        location_name = None
    else:
        click.echo("Error: Provide either --city or (--lat, --lng, --tz).", err=True)
        sys.exit(1)

    birth_data = BirthData(
        name=name,
        birth_datetime=birth_dt,
        city=location_name if city else None,
        latitude=lat,
        longitude=lng,
        timezone=tz,
        house_system=house_system,
    )

    try:
        result = build_chart(birth_data, ephe_path=settings.ephe_path)
    except Exception as e:
        click.echo(f"Error generating chart: {e}", err=True)
        sys.exit(1)

    if save:
        init_db(settings.db_path, admin_password=settings.admin_password)
        chart_id = save_chart(settings.db_path, result)
        if not quiet:
            click.echo(f"Chart saved with ID {chart_id}.", err=True)

    if fmt == "markdown":
        click.echo(to_markdown(result))
    else:
        click.echo(to_json(result))


@cli.command("list")
@click.option("--name", "-n", default=None, help="Filter by name.")
@click.option("--limit", "-l", default=20, help="Max results.")
@click.option("--offset", "-o", default=0, help="Result offset.")
@click.pass_context
def list_cmd(ctx, name, limit, offset):
    """List saved charts."""
    settings = ctx.obj["settings"]
    init_db(settings.db_path, admin_password=settings.admin_password)

    items, total = list_charts(settings.db_path, limit=limit, offset=offset, name_filter=name)

    if total == 0:
        click.echo("No charts found.")
        return

    click.echo(f"Charts ({total} total):")
    click.echo(f"{'ID':>4}  {'Name':<25} {'Date/Time':<22} {'Location':<30} {'System':<12}")
    click.echo("-" * 95)
    for item in items:
        display_name = item.name or "(unnamed)"
        click.echo(
            f"{item.id:>4}  {display_name:<25} {item.birth_datetime:<22} "
            f"{item.birth_location:<30} {item.house_system:<12}"
        )


@cli.command()
@click.argument("chart_id", type=int)
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "markdown"], case_sensitive=False),
              default="json", help="Output format.")
@click.pass_context
def show(ctx, chart_id, fmt):
    """Show a saved chart by ID."""
    settings = ctx.obj["settings"]
    init_db(settings.db_path, admin_password=settings.admin_password)

    result = load_chart(settings.db_path, chart_id)
    if result is None:
        click.echo(f"Error: Chart {chart_id} not found.", err=True)
        sys.exit(1)

    if fmt == "markdown":
        click.echo(to_markdown(result))
    else:
        click.echo(to_json(result))


@cli.command()
@click.argument("chart_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@click.pass_context
def delete(ctx, chart_id, yes):
    """Delete a saved chart by ID."""
    settings = ctx.obj["settings"]
    init_db(settings.db_path, admin_password=settings.admin_password)

    if not yes:
        result = load_chart(settings.db_path, chart_id)
        if result is None:
            click.echo(f"Error: Chart {chart_id} not found.", err=True)
            sys.exit(1)
        name = result.name or "(unnamed)"
        if not click.confirm(f"Delete chart {chart_id} ({name})?"):
            click.echo("Cancelled.")
            return

    deleted = delete_chart(settings.db_path, chart_id)
    if deleted:
        click.echo(f"Chart {chart_id} deleted.")
    else:
        click.echo(f"Error: Chart {chart_id} not found.", err=True)
        sys.exit(1)


@cli.command()
@click.argument("city")
@click.option("--max-rows", "-n", default=5, help="Max results to return.")
@click.pass_context
def geocode(ctx, city, max_rows):
    """Look up coordinates and timezone for a city."""
    settings = ctx.obj["settings"]

    if not settings.geonames_username:
        click.echo("Error: GEONAMES_USERNAME not configured. Set it in .env.", err=True)
        sys.exit(1)

    try:
        results = search_city(city, settings.geonames_username, max_rows=max_rows)
    except GeocodingError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    click.echo(f"Results for '{city}':")
    click.echo(f"{'#':>2}  {'City':<40} {'Lat':>9} {'Lng':>10}  {'Timezone':<25}")
    click.echo("-" * 90)
    for i, r in enumerate(results, 1):
        click.echo(
            f"{i:>2}  {r.city_name:<40} {r.latitude:>9.4f} {r.longitude:>10.4f}  {r.timezone:<25}"
        )


def _resolve_city(city, db_path, username, quiet):
    init_db(db_path)
    cached = get_cached_location(db_path, city)
    if cached is not None:
        if not quiet:
            click.echo(f"Using cached location: {cached.city_name}", err=True)
        return cached

    if not username:
        click.echo(
            "Error: GEONAMES_USERNAME not configured and city not in cache. "
            "Set it in .env or use --lat/--lng/--tz.",
            err=True,
        )
        return None

    try:
        result = geocode_city(city, username)
    except CityNotFoundError:
        click.echo(f"Error: City '{city}' not found.", err=True)
        return None
    except GeocodingError as e:
        click.echo(f"Error resolving city: {e}", err=True)
        return None

    cache_location(db_path, city, result)
    if not quiet:
        click.echo(f"Resolved: {result.city_name} ({result.latitude:.4f}, {result.longitude:.4f})", err=True)

    return result
