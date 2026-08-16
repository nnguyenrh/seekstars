from starseek.models.chart import BirthChart, TransitReport, SynastryReport


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

    if chart.sect:
        lines.append("## Traditional Analysis")
        lines.append("")
        lines.append(f"**Sect:** {chart.sect.capitalize()}")
        lines.append("")

        sect_planets = [p for p in chart.planets if p.sect_status and p.sect_status != "neutral"]
        if sect_planets:
            lines.append("**Sect Status:**")
            for p in sect_planets:
                lines.append(f"- {p.planet.value}: {p.sect_status.replace('_', ' ')}")
            lines.append("")

        conditioned = [p for p in chart.planets if p.condition]
        if conditioned:
            lines.append("**Planetary Condition:**")
            for p in conditioned:
                for note in p.condition:
                    lines.append(f"- {p.planet.value}: {note}")
            lines.append("")

        if s.domicile_lord_chains:
            lines.append("**Domicile Lord Chains:**")
            for chain_info in s.domicile_lord_chains:
                chain_str = " \u2192 ".join(chain_info["chain"])
                lines.append(f"- {chain_str}")
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


def synastry_to_markdown(report: SynastryReport) -> str:
    lines: list[str] = []

    name_a = report.chart_a.name or "Chart A"
    name_b = report.chart_b.name or "Chart B"
    lines.append(f"# Synastry: {name_a} & {name_b}")
    lines.append("")

    lines.append("## Inter-Chart Aspects")
    lines.append("")
    if report.inter_aspects:
        lines.append(f"| {name_a} Planet | Aspect | {name_b} Planet | Orb | App/Sep |")
        lines.append("|---------------|--------|---------------|-----|---------|")
        for a in sorted(report.inter_aspects, key=lambda x: x.orb):
            app_sep = "Applying" if a.is_applying else "Separating"
            lines.append(
                f"| {a.planet_a.value} | {a.aspect_type.value} "
                f"| {a.planet_b.value} | {a.orb:.2f}\u00b0 | {app_sep} |"
            )
    else:
        lines.append("No major inter-chart aspects found.")
    lines.append("")

    lines.append(f"## {name_a}'s Planets in {name_b}'s Houses")
    lines.append("")
    lines.append("| Planet | Sign | Degree | House |")
    lines.append("|--------|------|--------|-------|")
    for p in report.a_in_b_houses:
        deg = int(p.planet_degree)
        minute = int((p.planet_degree % 1) * 60)
        lines.append(f"| {p.planet.value} | {p.planet_sign.value} | {deg}\u00b0{minute:02d}' | {p.overlay_house} |")
    lines.append("")

    lines.append(f"## {name_b}'s Planets in {name_a}'s Houses")
    lines.append("")
    lines.append("| Planet | Sign | Degree | House |")
    lines.append("|--------|------|--------|-------|")
    for p in report.b_in_a_houses:
        deg = int(p.planet_degree)
        minute = int((p.planet_degree % 1) * 60)
        lines.append(f"| {p.planet.value} | {p.planet_sign.value} | {deg}\u00b0{minute:02d}' | {p.overlay_house} |")
    lines.append("")

    return "\n".join(lines)
