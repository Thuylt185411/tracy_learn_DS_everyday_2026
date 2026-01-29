from evidently import Dataset
from evidently.core.report import Context
from evidently.core.metric_types import SingleValue
from evidently.core.metric_types import SingleValueMetric
from evidently.core.metric_types import SingleValueCalculation
from evidently.core.metric_types import BoundTest
from evidently.tests import Reference, eq
from typing import List, Optional



class DefaultRateMetric(SingleValueMetric):
    true_column: str
    pred_column: str

    def _default_tests(self) -> List[BoundTest]:
        return [eq(0.0).bind_single(self.get_fingerprint())]

    def _default_tests_with_reference(self) -> List[BoundTest]:
        return [eq(Reference(relative=0.05)).bind_single(self.get_fingerprint())]

class DefaultRateMetricImplementation(SingleValueCalculation[DefaultRateMetric]):
    def calculate(self, context: Context,
        current_data: Dataset,
        reference_data: Optional[Dataset]
        ) -> SingleValue:
        y_true = current_data.column(self.metric.true_column).data
        # default_rate = (y_true == 1).sum() / len(y_true)
        default_rate = (y_true == 1).sum() / len(y_true)
        result = self.result(value=default_rate)
        if reference_data is not None:
            ref_y_true = reference_data.column(self.metric.true_column).data
            ref_default_rate = (ref_y_true == 1).sum() / len(ref_y_true)
            result_ref = self.result(value=ref_default_rate)
            return result, result_ref
        else:
            return result

    def display_name(self) -> str:
        return (
            f"Default rate for {self.metric.true_column}"
        )