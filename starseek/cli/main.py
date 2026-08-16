import os
import sys
from datetime import datetime
from typing import Optional

import click

from starseek.config import get_settings, reset_settings
from starseek.models.enums import HouseSystem
from starseek.models.input import BirthData
from starseek.core.chart import build_chart
from starseek.core.transits import calculate_transits
from starseek.core.synastry import calculate_synastry
from starseek.formatters.json_fmt import to_json, transit_to_json, synastry_to_json
from starseek.formatters.markdown_fmt import to_markdown, transit_to_markdown, synastry_to_markdown
from starseek.services.storage import (
    init_db, save_chart, load_chart, list_charts, delete_chart,
    save_synastry, load_synastry, list_synastries, delete_synastry,
    cache_location, get_cached_location,
)
from starseek.services.geocoding import (
    geocode_city, search_city,
    GeocodingError, CityNotFoundError, GeoNamesNotConfiguredError,
)


def _parse_birth_datetime(date_str: str, time_str: str) -> datetime:
    try:
        return datetime.fromisoformat(f"{date_str}T{time_str}:00")
    except ValueError:
        raise click.BadParameter(
            f"Invalid date '{date_str}' or time '{time_str}'. "
            "Use YYYY-MM-DD for date and HH:MM (24-hour) for time."
        )


def _ensure_geonames_username(settings) -> str:
    if settings.geonames_username:
        return settings.geonames_username

    username = click.prompt(
        "GeoNames username not configured.\n"
        "Register free at https://www.geonames.org/login\n"
        "Enter your GeoNames username",
        err=True,
    )

    if not username:
        click.echo("Error: GeoNames username is required for city lookup.", err=True)
        sys.exit(1)

    click.echo(f"Saving username to .env for future use...", err=True)
    _save_geonames_to_env(username)

    settings.geonames_username = username
    return username


def _save_geonames_to_env(username: str) -> None:
    from pathlib import Path
    from starseek.config import _PROJECT_ROOT

    env_path = _PROJECT_ROOT / ".env"

    if env_path.exists():
        content = env_path.read_text()
        if "GEONAMES_USERNAME=" in content:
            lines = content.splitlines()
            new_lines = []
            for line in lines:
                if line.strip().startswith("GEONAMES_USERNAME=") or line.strip().startswith("# GEONAMES_USERNAME="):
                    new_lines.append(f"GEONAMES_USERNAME={username}")
                else:
                    new_lines.append(line)
            env_path.write_text("\n".join(new_lines) + "\n")
            return

    with open(env_path, "a") as f:
        f.write(f"\nGEONAMES_USERNAME={username}\n")


@click.group()
@click.pass_context
def cli(ctx):
    """StarSeek - Astrological birth chart generator."""
    ctx.ensure_object(dict)
    ctx.obj["settings"] = get_settings()


@cli.command()
@click.option("--name", "-n", default=None, help="Name of the person.")
@click.option("--date", "-d", "date_str", required=True, help="Birth date (YYYY-MM-DD).")
@click.option("--time", "-t", "time_str", required=True, help="Birth time in 24-hour format (HH:MM).")
@click.option("--city", "-c", required=True, help="City of birth (e.g. 'New York, NY, US').")
@click.option("--houses", type=click.Choice(["placidus", "whole-sign"], case_sensitive=False),
              default=None, help="House system (default from config).")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "markdown"], case_sensitive=False),
              default="json", help="Output format.")
@click.option("--save/--no-save", default=False, help="Save chart to database.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-data output.")
@click.pass_context
def chart(ctx, name, date_str, time_str, city, houses, fmt, save, quiet):
    """Generate a birth chart from a city and birth date/time."""
    settings = ctx.obj["settings"]

    birth_dt = _parse_birth_datetime(date_str, time_str)

    if houses is None:
        house_system = settings.default_house_system
    elif houses == "whole-sign":
        house_system = HouseSystem.WHOLE_SIGN
    else:
        house_system = HouseSystem.PLACIDUS

    username = _ensure_geonames_username(settings)
    resolved = _resolve_city(city, settings.db_path, username, quiet)
    if resolved is None:
        sys.exit(1)

    birth_data = BirthData(
        name=name,
        birth_datetime=birth_dt,
        city=resolved.city_name,
        latitude=resolved.latitude,
        longitude=resolved.longitude,
        timezone=resolved.timezone,
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


@cli.command("chart-manual")
@click.option("--name", "-n", default=None, help="Name of the person.")
@click.option("--datetime", "dt", required=True, help="Birth date/time (ISO 8601).")
@click.option("--lat", type=float, required=True, help="Birth latitude.")
@click.option("--lng", type=float, required=True, help="Birth longitude.")
@click.option("--tz", required=True, help="IANA timezone (e.g. 'America/New_York').")
@click.option("--houses", type=click.Choice(["placidus", "whole-sign"], case_sensitive=False),
              default=None, help="House system (default from config).")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "markdown"], case_sensitive=False),
              default="json", help="Output format.")
@click.option("--save/--no-save", default=False, help="Save chart to database.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-data output.")
@click.pass_context
def chart_manual(ctx, name, dt, lat, lng, tz, houses, fmt, save, quiet):
    """Generate a birth chart from manual coordinates (advanced)."""
    settings = ctx.obj["settings"]

    try:
        birth_dt = datetime.fromisoformat(dt)
    except ValueError:
        click.echo(f"Error: Invalid datetime format '{dt}'.", err=True)
        sys.exit(1)

    if houses is None:
        house_system = settings.default_house_system
    elif houses == "whole-sign":
        house_system = HouseSystem.WHOLE_SIGN
    else:
        house_system = HouseSystem.PLACIDUS

    birth_data = BirthData(
        name=name,
        birth_datetime=birth_dt,
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

    username = _ensure_geonames_username(settings)

    try:
        results = search_city(city, username, max_rows=max_rows)
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


@cli.command()
@click.argument("chart_id", type=int)
@click.option("--date", "-d", "date_str", default=None, help="Transit date (YYYY-MM-DD). Defaults to today.")
@click.option("--time", "-t", "time_str", default=None, help="Transit time in 24-hour format (HH:MM). Defaults to now.")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "markdown"], case_sensitive=False),
              default="json", help="Output format.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-data output.")
@click.pass_context
def transits(ctx, chart_id, date_str, time_str, fmt, quiet):
    """Show current transits for a saved natal chart."""
    settings = ctx.obj["settings"]
    init_db(settings.db_path, admin_password=settings.admin_password)

    natal = load_chart(settings.db_path, chart_id)
    if natal is None:
        click.echo(f"Error: Chart {chart_id} not found.", err=True)
        sys.exit(1)

    if date_str or time_str:
        d = date_str or datetime.now().strftime("%Y-%m-%d")
        t = time_str or "12:00"
        transit_dt = _parse_birth_datetime(d, t)
    else:
        transit_dt = None

    try:
        report = calculate_transits(
            natal, transit_dt=transit_dt, ephe_path=settings.ephe_path
        )
    except Exception as e:
        click.echo(f"Error calculating transits: {e}", err=True)
        sys.exit(1)

    if not quiet and transit_dt is None:
        click.echo("Calculating transits for current time...", err=True)

    if fmt == "markdown":
        click.echo(transit_to_markdown(report))
    else:
        click.echo(transit_to_json(report))


@cli.command()
@click.argument("chart_id_a", type=int)
@click.argument("chart_id_b", type=int)
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "markdown"], case_sensitive=False),
              default="json", help="Output format.")
@click.option("--save/--no-save", default=False, help="Save synastry report to database.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-data output.")
@click.pass_context
def synastry(ctx, chart_id_a, chart_id_b, fmt, save, quiet):
    """Compare two saved charts (synastry)."""
    settings = ctx.obj["settings"]
    init_db(settings.db_path, admin_password=settings.admin_password)

    chart_a = load_chart(settings.db_path, chart_id_a)
    if chart_a is None:
        click.echo(f"Error: Chart {chart_id_a} not found.", err=True)
        sys.exit(1)

    chart_b = load_chart(settings.db_path, chart_id_b)
    if chart_b is None:
        click.echo(f"Error: Chart {chart_id_b} not found.", err=True)
        sys.exit(1)

    try:
        report = calculate_synastry(chart_a, chart_b)
    except Exception as e:
        click.echo(f"Error calculating synastry: {e}", err=True)
        sys.exit(1)

    if save:
        report_id = save_synastry(settings.db_path, report)
        if not quiet:
            click.echo(f"Synastry report saved with ID {report_id}.", err=True)

    if not quiet:
        name_a = chart_a.name or f"Chart {chart_id_a}"
        name_b = chart_b.name or f"Chart {chart_id_b}"
        click.echo(f"Comparing {name_a} with {name_b}...", err=True)

    if fmt == "markdown":
        click.echo(synastry_to_markdown(report))
    else:
        click.echo(synastry_to_json(report))


@cli.command("list-synastry")
@click.option("--limit", "-l", default=20, help="Max results.")
@click.option("--offset", "-o", default=0, help="Result offset.")
@click.pass_context
def list_synastry_cmd(ctx, limit, offset):
    """List saved synastry reports."""
    settings = ctx.obj["settings"]
    init_db(settings.db_path, admin_password=settings.admin_password)

    items, total = list_synastries(settings.db_path, limit=limit, offset=offset)

    if total == 0:
        click.echo("No synastry reports found.")
        return

    click.echo(f"Synastry Reports ({total} total):")
    click.echo(f"{'ID':>4}  {'Person A':<20} {'Person B':<20} {'Chart A':>7} {'Chart B':>7}  {'Created':<20}")
    click.echo("-" * 85)
    for item in items:
        name_a = item.name_a or "(unnamed)"
        name_b = item.name_b or "(unnamed)"
        click.echo(
            f"{item.id:>4}  {name_a:<20} {name_b:<20} "
            f"{item.chart_a_id:>7} {item.chart_b_id:>7}  {item.created_at:<20}"
        )


@cli.command("show-synastry")
@click.argument("report_id", type=int)
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "markdown"], case_sensitive=False),
              default="json", help="Output format.")
@click.pass_context
def show_synastry_cmd(ctx, report_id, fmt):
    """Show a saved synastry report by ID."""
    settings = ctx.obj["settings"]
    init_db(settings.db_path, admin_password=settings.admin_password)

    report = load_synastry(settings.db_path, report_id)
    if report is None:
        click.echo(f"Error: Synastry report {report_id} not found.", err=True)
        sys.exit(1)

    if fmt == "markdown":
        click.echo(synastry_to_markdown(report))
    else:
        click.echo(synastry_to_json(report))


@cli.command("delete-synastry")
@click.argument("report_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@click.pass_context
def delete_synastry_cmd(ctx, report_id, yes):
    """Delete a saved synastry report by ID."""
    settings = ctx.obj["settings"]
    init_db(settings.db_path, admin_password=settings.admin_password)

    if not yes:
        report = load_synastry(settings.db_path, report_id)
        if report is None:
            click.echo(f"Error: Synastry report {report_id} not found.", err=True)
            sys.exit(1)
        name_a = report.chart_a.name or "(unnamed)"
        name_b = report.chart_b.name or "(unnamed)"
        if not click.confirm(f"Delete synastry report {report_id} ({name_a} & {name_b})?"):
            click.echo("Cancelled.")
            return

    deleted = delete_synastry(settings.db_path, report_id)
    if deleted:
        click.echo(f"Synastry report {report_id} deleted.")
    else:
        click.echo(f"Error: Synastry report {report_id} not found.", err=True)
        sys.exit(1)


def _resolve_city(city, db_path, username, quiet):
    init_db(db_path)
    cached = get_cached_location(db_path, city)
    if cached is not None:
        if not quiet:
            click.echo(f"Using cached location: {cached.city_name}", err=True)
        return cached

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
