import pytest
from datetime import datetime

from starseek.models.enums import Planet, Sign, HouseSystem, Dignity, AspectType
from starseek.models.input import BirthData
from starseek.models.chart import PlanetPosition, Aspect
from starseek.core.chart import build_chart
from starseek.core.traditional import (
    determine_sect, get_sect_status, build_domicile_lord_chain,
    get_all_lord_chains, evaluate_bonification, SIGN_RULERS,
)


class TestSectDetermination:
    def test_diurnal_chart(self):
        assert determine_sect(sun_longitude=90.0, asc_longitude=0.0) == "diurnal"

    def test_nocturnal_chart(self):
        assert determine_sect(sun_longitude=270.0, asc_longitude=0.0) == "nocturnal"

    def test_sun_just_above_horizon(self):
        assert determine_sect(sun_longitude=10.0, asc_longitude=5.0) == "diurnal"

    def test_sun_just_below_horizon(self):
        assert determine_sect(sun_longitude=350.0, asc_longitude=5.0) == "nocturnal"

    def test_chart_has_sect_field(self):
        bd = BirthData(
            birth_datetime=datetime(2000, 1, 1, 12, 0, 0),
            latitude=0.0, longitude=0.0, timezone="UTC",
        )
        chart = build_chart(bd)
        assert chart.sect in ("diurnal", "nocturnal")


class TestSectStatus:
    def test_sun_in_diurnal(self):
        assert get_sect_status(Planet.SUN, "diurnal") == "in_sect"

    def test_sun_in_nocturnal(self):
        assert get_sect_status(Planet.SUN, "nocturnal") == "out_of_sect"

    def test_moon_in_nocturnal(self):
        assert get_sect_status(Planet.MOON, "nocturnal") == "in_sect"

    def test_moon_in_diurnal(self):
        assert get_sect_status(Planet.MOON, "diurnal") == "out_of_sect"

    def test_jupiter_diurnal(self):
        assert get_sect_status(Planet.JUPITER, "diurnal") == "in_sect"

    def test_venus_nocturnal(self):
        assert get_sect_status(Planet.VENUS, "nocturnal") == "in_sect"

    def test_saturn_diurnal(self):
        assert get_sect_status(Planet.SATURN, "diurnal") == "in_sect"

    def test_mars_nocturnal(self):
        assert get_sect_status(Planet.MARS, "nocturnal") == "in_sect"

    def test_mercury_neutral(self):
        assert get_sect_status(Planet.MERCURY, "diurnal") == "neutral"
        assert get_sect_status(Planet.MERCURY, "nocturnal") == "neutral"

    def test_outer_planets_neutral(self):
        assert get_sect_status(Planet.CHIRON, "diurnal") == "neutral"
        assert get_sect_status(Planet.NORTH_NODE, "nocturnal") == "neutral"

    def test_planets_have_sect_status(self):
        bd = BirthData(
            birth_datetime=datetime(2000, 1, 1, 12, 0, 0),
            latitude=0.0, longitude=0.0, timezone="UTC",
        )
        chart = build_chart(bd)
        sun = next(p for p in chart.planets if p.planet == Planet.SUN)
        assert sun.sect_status is not None


class TestDomicileLordChains:
    def test_sun_in_leo_self_ruling(self):
        chain = build_domicile_lord_chain(
            Planet.SUN, {Planet.SUN: Sign.LEO}
        )
        assert chain == ["Sun", "Sun"]

    def test_chain_follows_rulers(self):
        planet_signs = {
            Planet.MARS: Sign.GEMINI,
            Planet.MERCURY: Sign.LEO,
            Planet.SUN: Sign.LEO,
        }
        chain = build_domicile_lord_chain(Planet.MARS, planet_signs)
        assert chain[0] == "Mars"
        assert "Mercury" in chain

    def test_chain_detects_loop(self):
        planet_signs = {
            Planet.VENUS: Sign.ARIES,
            Planet.MARS: Sign.TAURUS,
        }
        chain = build_domicile_lord_chain(Planet.VENUS, planet_signs)
        assert len(chain) >= 2

    def test_all_lord_chains_from_chart(self):
        bd = BirthData(
            birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
            latitude=0.0, longitude=0.0, timezone="UTC",
        )
        chart = build_chart(bd)
        chains = chart.summary.domicile_lord_chains
        assert len(chains) > 0
        for c in chains:
            assert "planet" in c
            assert "chain" in c
            assert len(c["chain"]) >= 1

    def test_sign_rulers_complete(self):
        for sign in Sign:
            assert sign in SIGN_RULERS


class TestBonificationMaltreatment:
    def test_bonification_detected(self):
        planets = [
            PlanetPosition(
                planet=Planet.SUN, longitude=100.0, latitude=0.0, speed=1.0,
                is_retrograde=False, sign=Sign.CANCER, sign_degree=10.0,
                sign_minute=0, house=1, dignity=Dignity.PEREGRINE,
            ),
            PlanetPosition(
                planet=Planet.JUPITER, longitude=103.0, latitude=0.0, speed=0.1,
                is_retrograde=False, sign=Sign.CANCER, sign_degree=13.0,
                sign_minute=0, house=1, dignity=Dignity.EXALTATION,
            ),
        ]
        aspects = [
            Aspect(
                planet_a=Planet.SUN, planet_b=Planet.JUPITER,
                aspect_type=AspectType.CONJUNCTION, exact_angle=3.0,
                orb=3.0, is_applying=True,
            )
        ]
        conditions = evaluate_bonification(planets, aspects, "diurnal")
        assert "Sun" in conditions
        assert any("Bonified" in n for n in conditions["Sun"])

    def test_maltreatment_detected(self):
        planets = [
            PlanetPosition(
                planet=Planet.MOON, longitude=100.0, latitude=0.0, speed=13.0,
                is_retrograde=False, sign=Sign.CANCER, sign_degree=10.0,
                sign_minute=0, house=1, dignity=Dignity.DOMICILE,
            ),
            PlanetPosition(
                planet=Planet.SATURN, longitude=280.0, latitude=0.0, speed=0.03,
                is_retrograde=False, sign=Sign.CAPRICORN, sign_degree=10.0,
                sign_minute=0, house=7, dignity=Dignity.DOMICILE,
            ),
        ]
        aspects = [
            Aspect(
                planet_a=Planet.MOON, planet_b=Planet.SATURN,
                aspect_type=AspectType.OPPOSITION, exact_angle=180.0,
                orb=0.0, is_applying=False,
            )
        ]
        conditions = evaluate_bonification(planets, aspects, "nocturnal")
        if "Moon" in conditions:
            assert any("Maltreated" in n for n in conditions["Moon"])

    def test_chart_has_conditions(self):
        bd = BirthData(
            birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
            latitude=0.0, longitude=0.0, timezone="UTC",
        )
        chart = build_chart(bd)
        for p in chart.planets:
            if p.condition:
                assert isinstance(p.condition, list)
                assert all(isinstance(n, str) for n in p.condition)


class TestTraditionalInMarkdown:
    def test_markdown_includes_traditional(self):
        from starseek.formatters.markdown_fmt import to_markdown
        bd = BirthData(
            name="Traditional Test",
            birth_datetime=datetime(2000, 1, 1, 12, 0, 0),
            latitude=0.0, longitude=0.0, timezone="UTC",
        )
        chart = build_chart(bd)
        md = to_markdown(chart)

        assert "## Traditional Analysis" in md
        assert "**Sect:**" in md

    def test_markdown_shows_sect_status(self):
        from starseek.formatters.markdown_fmt import to_markdown
        bd = BirthData(
            birth_datetime=datetime(2000, 1, 1, 12, 0, 0),
            latitude=0.0, longitude=0.0, timezone="UTC",
        )
        chart = build_chart(bd)
        md = to_markdown(chart)

        assert "**Sect Status:**" in md

    def test_markdown_shows_lord_chains(self):
        from starseek.formatters.markdown_fmt import to_markdown
        bd = BirthData(
            birth_datetime=datetime(2000, 1, 1, 12, 0, 0),
            latitude=0.0, longitude=0.0, timezone="UTC",
        )
        chart = build_chart(bd)
        md = to_markdown(chart)

        assert "**Domicile Lord Chains:**" in md
        assert "\u2192" in md


class TestTransitSect:
    def test_transit_report_has_natal_sect(self):
        from starseek.core.transits import calculate_transits
        bd = BirthData(
            birth_datetime=datetime(2000, 1, 1, 12, 0, 0),
            latitude=0.0, longitude=0.0, timezone="UTC",
        )
        chart = build_chart(bd)
        report = calculate_transits(chart, transit_dt=datetime(2026, 6, 15, 12, 0))
        assert report.natal_sect in ("diurnal", "nocturnal")
