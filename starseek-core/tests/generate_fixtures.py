"""
One-time script to generate reference chart fixtures.
Run: python tests/generate_fixtures.py > tests/fixtures/reference_charts.json
"""

import swisseph as swe
import json

CHARTS = [
    {
        "label": "null_island",
        "year": 2000, "month": 1, "day": 1,
        "hour_utc": 0.0,
        "lat": 0.0, "lng": 0.0,
    },
    {
        "label": "princess_diana",
        "year": 1961, "month": 7, "day": 1,
        "hour_utc": 18.75,
        "lat": 52.8306, "lng": 0.5145,
    },
    {
        "label": "midnight_boundary",
        "year": 1985, "month": 12, "day": 31,
        "hour_utc": 14.9167,
        "lat": 35.6762, "lng": 139.6503,
    },
    {
        "label": "date_shift_west",
        "year": 1992, "month": 3, "day": 15,
        "hour_utc": 9.5,
        "lat": 34.0522, "lng": -118.2437,
    },
    {
        "label": "retrograde_heavy",
        "year": 2023, "month": 7, "day": 22,
        "hour_utc": 12.0,
        "lat": 51.5074, "lng": -0.1278,
    },
]

PLANETS = [
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mercury", swe.MERCURY),
    ("Venus", swe.VENUS),
    ("Mars", swe.MARS),
    ("Jupiter", swe.JUPITER),
    ("Saturn", swe.SATURN),
    ("Uranus", swe.URANUS),
    ("Neptune", swe.NEPTUNE),
    ("Pluto", swe.PLUTO),
    ("North Node", swe.TRUE_NODE),
    ("Chiron", swe.CHIRON),
    ("Black Moon Lilith", swe.MEAN_APOG),
]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def compute_chart(chart_def):
    jd = swe.julday(
        chart_def["year"], chart_def["month"], chart_def["day"],
        chart_def["hour_utc"]
    )

    planets = []
    for name, body_id in PLANETS:
        xx, _ = swe.calc_ut(jd, body_id)
        lon = xx[0]
        sign_idx = int(lon / 30)
        planets.append({
            "name": name,
            "longitude": round(lon, 6),
            "latitude": round(xx[1], 6),
            "speed": round(xx[3], 6),
            "is_retrograde": xx[3] < 0,
            "sign": SIGNS[sign_idx],
            "degree_in_sign": round(lon % 30, 4),
        })

    nn = next(p for p in planets if p["name"] == "North Node")
    sn_lon = (nn["longitude"] + 180) % 360
    sn_sign_idx = int(sn_lon / 30)
    planets.append({
        "name": "South Node",
        "longitude": round(sn_lon, 6),
        "latitude": 0.0,
        "speed": round(nn["speed"], 6),
        "is_retrograde": nn["speed"] < 0,
        "sign": SIGNS[sn_sign_idx],
        "degree_in_sign": round(sn_lon % 30, 4),
    })

    cusps, ascmc = swe.houses(jd, chart_def["lat"], chart_def["lng"], b'P')
    house_cusps = []
    for i in range(12):
        lon = cusps[i]
        sign_idx = int(lon / 30)
        house_cusps.append({
            "house": i + 1,
            "longitude": round(lon, 6),
            "sign": SIGNS[sign_idx],
            "degree_in_sign": round(lon % 30, 4),
        })

    return {
        "label": chart_def["label"],
        "julian_day": jd,
        "input": {
            "year": chart_def["year"],
            "month": chart_def["month"],
            "day": chart_def["day"],
            "hour_utc": chart_def["hour_utc"],
            "lat": chart_def["lat"],
            "lng": chart_def["lng"],
        },
        "planets": planets,
        "house_cusps": house_cusps,
        "ascendant": round(ascmc[0], 6),
        "midheaven": round(ascmc[1], 6),
    }


if __name__ == "__main__":
    import os
    ephe_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ephe")
    swe.set_ephe_path(ephe_path)
    results = [compute_chart(c) for c in CHARTS]
    swe.close()
    print(json.dumps(results, indent=2))
