from starseek.models.chart import BirthChart, TransitReport, SynastryReport


def to_json(chart: BirthChart, indent: int = 2) -> str:
    return chart.model_dump_json(indent=indent)


def to_dict(chart: BirthChart) -> dict:
    return chart.model_dump(mode="json")


def transit_to_json(report: TransitReport, indent: int = 2) -> str:
    return report.model_dump_json(indent=indent)


def transit_to_dict(report: TransitReport) -> dict:
    return report.model_dump(mode="json")


def synastry_to_json(report: SynastryReport, indent: int = 2) -> str:
    return report.model_dump_json(indent=indent)


def synastry_to_dict(report: SynastryReport) -> dict:
    return report.model_dump(mode="json")
