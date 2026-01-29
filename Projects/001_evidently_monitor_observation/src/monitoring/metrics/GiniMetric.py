from sklearn.metrics import roc_auc_score
from evidently import Dataset
from evidently.core.report import Context
from evidently.core.metric_types import SingleValue
from evidently.core.metric_types import SingleValueMetric
from evidently.core.metric_types import SingleValueCalculation
from evidently.core.metric_types import BoundTest
from evidently.tests import Reference, eq
from typing import List, Optional


class GiniMetric(SingleValueMetric):
    true_column: str
    pred_column: str

    def _default_tests(self) -> List[BoundTest]:
        return [eq(0.0).bind_single(self.get_fingerprint())]

    def _default_tests_with_reference(self) -> List[BoundTest]:
        return [eq(Reference(relative=0.05)).bind_single(self.get_fingerprint())]

# implementation
class GiniMetricImplementation(SingleValueCalculation[GiniMetric]):
    def calculate(self, context: Context, 
        current_data: Dataset, 
        reference_data: Optional[Dataset]
        ) -> SingleValue:
        y_true = current_data.column(self.metric.true_column).data
        y_pred = current_data.column(self.metric.pred_column).data
        auc = roc_auc_score(y_true, y_pred)
        gini = 2 * auc - 1
        result = self.result(value=gini)
        if reference_data is not None:
            ref_auc = roc_auc_score(reference_data.column(self.metric.true_column).data,
                                   reference_data.column(self.metric.pred_column).data)
            ref_gini = 2 * ref_auc - 1
            result_ref = self.result(value=ref_gini)
            return result, result_ref
        else:
            return result

    def display_name(self) -> str:
        return (
            f"Gini score for {self.metric.true_column} vs {self.metric.pred_column} "
        )
