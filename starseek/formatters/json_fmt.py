from starseek.models.chart import BirthChart


def to_json(chart: BirthChart, indent: int = 2) -> str:
    return chart.model_dump_json(indent=indent)


def to_dict(chart: BirthChart) -> dict:
    return chart.model_dump(mode="json")
