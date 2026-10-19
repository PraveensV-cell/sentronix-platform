from typing import Any

import torch
from ultralytics.models.yolo.detect.train import DetectionTrainer


LOW_PRIORITY_CLASS_IDS = {6, 10, 12, 15, 20, 11}
LOW_PRIORITY_WEIGHT = 0.1
EXPECTED_CLASS_COUNT = 25


class SentronixWeightedTrainer(DetectionTrainer):
    """Apply custom classification weights to Sentronix detection classes."""

    def _get_class_weights(self) -> torch.Tensor:
        class_count = len(self.data["names"])

        if class_count != EXPECTED_CLASS_COUNT:
            raise ValueError(
                f"Expected {EXPECTED_CLASS_COUNT} classes, got {class_count}."
            )

        if not LOW_PRIORITY_CLASS_IDS.issubset(range(class_count)):
            raise ValueError("A low-priority class ID is outside the valid range.")

        weights = torch.ones(class_count, dtype=torch.float32)

        for class_id in LOW_PRIORITY_CLASS_IDS:
            weights[class_id] = LOW_PRIORITY_WEIGHT

        return weights / weights.mean()

    def _apply_class_weights(self, model: Any) -> None:
        unwrapped_model: Any = model
        if hasattr(unwrapped_model, "module"):
            unwrapped_model = unwrapped_model.module

        weights = self._get_class_weights().to(self.device)
        unwrapped_model.class_weights = weights

        criterion: Any = getattr(unwrapped_model, "criterion", None)
        if criterion is None:
            return

        branches = [getattr(criterion, name, None) for name in ("one2many", "one2one")]
        branches = [branch for branch in branches if branch is not None]

        if not branches:
            branches = [criterion]

        for branch in branches:
            branch_weights = getattr(branch, "class_weights", None)
            if isinstance(branch_weights, torch.Tensor):
                branch_weights.copy_(
                    weights.to(device=branch_weights.device).view(1, 1, -1)
                )
            else:
                branch.class_weights = weights.to(device=branch.device).view(1, 1, -1)

    def set_class_weights(self) -> None:
        if self.model is None:
            raise RuntimeError(
                "Model must be initialized before setting class weights."
            )

        self._apply_class_weights(self.model)

        model: Any = self.model
        if hasattr(model, "module"):
            model = model.module

        print(
            "Sentronix custom class weights:",
            model.class_weights.detach().cpu().tolist(),
        )
