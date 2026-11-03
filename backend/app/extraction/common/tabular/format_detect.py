import csv


def detect_format(text: str) -> str:
    if "\t" in text.splitlines()[0] if text else False:
        return "tsv"
    try:
        sample = text[:4096]
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        return {"\t": "tsv", ",": "csv", ";": "semicolon_csv"}.get(dialect.delimiter, "unsupported")
    except csv.Error:
        return "unsupported"
