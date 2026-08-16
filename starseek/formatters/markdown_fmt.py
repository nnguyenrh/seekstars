from starseek.models.chart import BirthChart, TransitReport


def to_markdown(chart: BirthChart) -> str:
    lines: list[str] = []

    name = chart.name or "Birth Chart"
    lines.append(f"# {name}")
    lines.append("")
    lines.append(f"**Date/Time:** {chart.birth_datetime.isoformat()}")
    lines.append(f"**Location:** {chart.birth_location} ({chart.latitude:.4f}, {chart.longitude:.4f})")
    lines.append(f"**Timezone:** {chart.timezone}")
    lines.append(f"**House System:** {chart.house_system.value}")
    lines.append("")

    lines.append("## Planetary Positions")
    lines.append("")
    lines.append("| Planet | Sign | Degree | House | Dignity | Rx |")
    lines.append("|--------|------|--------|-------|---------|----|")
    for p in chart.planets:
        rx = "R" if p.is_retrograde else ""
        deg = int(p.sign_degree)
        minute = p.sign_minute
        dignity = p.dignity.value if p.dignity and p.dignity.value != "Peregrine" else ""
        lines.append(f"| {p.planet.value} | {p.sign.value} | {deg}°{minute:02d}' | {p.house} | {dignity} | {rx} |")
    lines.append("")

    lines.append("## House Cusps")
    lines.append("")
    lines.append("| House | Sign | Degree | Quality |")
    lines.append("|-------|------|--------|---------|")
    for h in chart.houses:
        deg = int(h.sign_degree)
        lines.append(f"| {h.house_number} | {h.sign.value} | {deg}° | {h.quality.value} |")
    lines.append("")

    lines.append("## Aspects")
    lines.append("")
    lines.append("| Planet A | Aspect | Planet B | Orb | App/Sep |")
    lines.append("|----------|--------|----------|-----|---------|")
    for a in sorted(chart.aspects, key=lambda x: x.orb):
        app_sep = "Applying" if a.is_applying else "Separating"
        lines.append(f"| {a.planet_a.value} | {a.aspect_type.value} | {a.planet_b.value} | {a.orb:.2f}° | {app_sep} |")
    lines.append("")

    s = chart.summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"**Dominant Element:** {s.dominant_element.value}")
    elem_str = ", ".join(f"{e.value}: {c}" for e, c in s.element_counts.items())
    lines.append(f"**Elements:** {elem_str}")
    lines.append(f"**Dominant Modality:** {s.dominant_modality.value}")
    mod_str = ", ".join(f"{m.value}: {c}" for m, c in s.modality_counts.items())
    lines.append(f"**Modalities:** {mod_str}")

    if s.stelliums:
        lines.append("")
        lines.append("**Stelliums:**")
        for st in s.stelliums:
            planets_str = ", ".join(st["planets"])
            lines.append(f"- {st['sign']}: {planets_str}")

    lines.append("")
    return "\n".join(lines)


def transit_to_markdown(report: TransitReport) -> str:
    lines: list[str] = []

    title = f"Transits for {report.natal_name}" if report.natal_name else "Transit Report"
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Transit Date/Time:** {report.transit_datetime.isoformat()}")
    if report.natal_chart_id is not None:
        lines.append(f"**Natal Chart ID:** {report.natal_chart_id}")
    lines.append("")

    lines.append("## Current Planetary Positions")
    lines.append("")
    lines.append("| Planet | Sign | Degree | Natal House | Rx |")
    lines.append("|--------|------|--------|-------------|----|")
    for p in report.transit_positions:
        rx = "R" if p.is_retrograde else ""
        deg = int(p.sign_degree)
        minute = p.sign_minute
        lines.append(f"| {p.planet.value} | {p.sign.value} | {deg}\u00b0{minute:02d}' | {p.natal_house} | {rx} |")
    lines.append("")

    lines.append("## Transit-to-Natal Aspects")
    lines.append("")
    if report.transit_aspects:
        lines.append("| Transit Planet | Aspect | Natal Planet | Orb | App/Sep |")
        lines.append("|---------------|--------|-------------|-----|---------|")
        for a in sorted(report.transit_aspects, key=lambda x: x.orb):
            app_sep = "Applying" if a.is_applying else "Separating"
            lines.append(
                f"| {a.transit_planet.value} | {a.aspect_type.value} "
                f"| {a.natal_planet.value} | {a.orb:.2f}\u00b0 | {app_sep} |"
            )
    else:
        lines.append("No major transit aspects found.")
    lines.append("")

    return "\n".join(lines)
