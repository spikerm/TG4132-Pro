from __future__ import annotations

import math
from typing import List, Tuple


class MeasurementEngine:
    @staticmethod
    def interpolate_crossing(f1: float, y1: float, f2: float, y2: float, target: float) -> float:
        if y2 == y1:
            return f2
        return f1 + (target - y1) * (f2 - f1) / (y2 - y1)

    def bandwidth(self, frequencies: List[float], values: List[float], center_index: int, depth_db: float = 3.0, notch: bool = False):
        if not frequencies or len(frequencies) != len(values):
            return None
        center_index = max(0, min(len(values) - 1, center_index))
        reference = values[center_index]
        target = reference + depth_db if notch else reference - depth_db

        left = None
        for i in range(center_index, 0, -1):
            if (values[i] - target) * (values[i - 1] - target) <= 0:
                left = self.interpolate_crossing(frequencies[i], values[i], frequencies[i - 1], values[i - 1], target)
                break
        right = None
        for i in range(center_index, len(values) - 1):
            if (values[i] - target) * (values[i + 1] - target) <= 0:
                right = self.interpolate_crossing(frequencies[i], values[i], frequencies[i + 1], values[i + 1], target)
                break
        if left is None or right is None or right <= left:
            return None
        bw = right - left
        f0 = frequencies[center_index]
        return {"f0_mhz": f0, "left_mhz": left, "right_mhz": right, "bw_mhz": bw, "q": f0 / bw if bw else math.inf, "threshold": target}

    @staticmethod
    def ripple(values: List[float]) -> float:
        return (max(values) - min(values)) if values else 0.0

    @staticmethod
    def notch_depth(values: List[float]) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        top = ordered[max(0, int(len(ordered) * 0.75)):]
        baseline = sum(top) / len(top) if top else max(values)
        return baseline - min(values)

    @staticmethod
    def return_loss_from_swr(swr: float) -> float:
        swr = max(1.000001, float(swr))
        gamma = (swr - 1.0) / (swr + 1.0)
        return -20.0 * math.log10(max(gamma, 1e-12))
