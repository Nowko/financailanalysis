from collectors.document_source_collector import DocumentSourceCollector
from collectors.kosis_collector import KosisCollector
from collectors.manual_source_collector import ManualSourceCollector


COLLECTOR_MAP = {
    KosisCollector.collector_key: KosisCollector,
    ManualSourceCollector.collector_key: ManualSourceCollector,
    DocumentSourceCollector.collector_key: DocumentSourceCollector,
}


def get_collector(collector_key: str, settings):
    if collector_key not in COLLECTOR_MAP:
        raise KeyError(f"Unknown collector: {collector_key}")
    return COLLECTOR_MAP[collector_key](settings)
