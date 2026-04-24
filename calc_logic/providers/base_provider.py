class BaseBenchmarkProvider:
    provider_name = "unknown"
    supported_metrics = ()

    def supports_metric(self, metric_name: str) -> bool:
        return metric_name in self.supported_metrics

    def build_metric_result(
        self,
        metric_name: str,
        label: str,
        value: float,
        method: str,
        detail: dict = None,
    ) -> dict:
        return {
            "metric_name": metric_name,
            "label": label,
            "value": float(value),
            "source": self.provider_name,
            "method": method,
            "detail": detail or {},
        }

    def build_analysis_result(self, method: str, detail: dict = None, **payload) -> dict:
        result = {
            "source": self.provider_name,
            "method": method,
            "detail": detail or {},
        }
        result.update(payload)
        return result

    def get_metric(self, metric_name: str, selection: dict, profile) -> dict:
        raise NotImplementedError(f"{self.__class__.__name__} does not support metric lookups.")
