"""Phase-only superposition of independently focused TX-RIS-RX beams."""

from copy import deepcopy
from typing import Optional

import numpy as np

from surpRISe.components.antenna import Antenna
from surpRISe.components.ris import RIS
from surpRISe.optimizers.tx_ris_rx_opt import (
    calc_tx_ris_rx_phase_opt,
    quantize_phases,
)


class tx_ris_rx_superposition_opt:
    """Combine continuous user beams, quantizing only the final shared phases.

    For K > 1, ``optimizer`` is ignored: every user uses continuous analytical
    compensation, even when the final mode is discrete. K = 1 delegates to the
    selected single-user algorithm and mode to preserve its exact behavior.
    Weights scale complex field vectors, not user powers. This is a multibeam
    heuristic, not a joint sum-power or fairness optimizer.
    """

    def __init__(
        self,
        tx_antenna: Antenna,
        rx_antenna: Antenna,
        rx_positions: np.ndarray,
        ris: RIS,
        optimizer: str = "iterative",
        mode: str = "disc",
        wave_model: str = "spherical",
        fc: Optional[float] = None,
        user_weights: Optional[np.ndarray] = None,
    ) -> None:
        if not isinstance(tx_antenna, Antenna) or not isinstance(rx_antenna, Antenna):
            raise ValueError("tx_antenna and rx_antenna must be of class Antenna")
        if not isinstance(ris, RIS):
            raise ValueError("ris must be of class RIS")
        if mode not in ("disc", "cont"):
            raise ValueError("mode must be either 'disc' or 'cont'")
        if wave_model not in ("spherical", "plane"):
            raise ValueError("wave_model must be either 'spherical' or 'plane'")

        positions = np.array(rx_positions, dtype=float, copy=True)
        if (
            positions.ndim != 2
            or positions.shape[1] != 3
            or positions.shape[0] == 0
            or not np.all(np.isfinite(positions))
        ):
            raise ValueError("rx_positions must be a finite, nonempty (K, 3) array")
        if np.any(np.linalg.norm(positions - ris.center, axis=1) == 0):
            raise ValueError("Receiver cannot be at RIS center")

        weights = (
            np.ones(len(positions))
            if user_weights is None
            else np.array(user_weights, dtype=float, copy=True)
        )
        if (
            weights.shape != (len(positions),)
            or not np.all(np.isfinite(weights))
            or np.any(weights < 0)
            or not np.any(weights > 0)
        ):
            raise ValueError(
                "user_weights must have shape (K,), finite, nonnegative, "
                "with at least one positive weight"
            )
        # Scale before summing to avoid overflow; a common scale changes no phase.
        weights /= np.max(weights)
        self.user_weights = weights / np.sum(weights)
        self.rx_positions = positions
        self.tx_antenna = tx_antenna
        self.rx_antenna = rx_antenna
        self.ris = ris
        self.optimizer = optimizer
        self.mode = mode
        self.wave_model = wave_model
        self.fc = fc

    def optimize(self, return_history: bool = False):
        """Return phases of shape (Nrow, Ncol), leaving input objects unchanged.

        With history enabled, return ``(phases, history)``. For K > 1 history
        contains continuous per-user phases, normalized field weights, and a
        cancellation mask. Near-zero sums (magnitude <= 1e-12 with normalized
        weights) use the highest-weight user's phase, choosing the first on ties.
        K = 1 returns the underlying single-user history instead.
        """
        per_user_phases = []
        for position in self.rx_positions:
            receiver = deepcopy(self.rx_antenna)
            receiver.position = position.copy()
            receiver.point_to(self.ris.center)
            phases, history = calc_tx_ris_rx_phase_opt(
                tx_antenna=self.tx_antenna,
                rx_antenna=receiver,
                ris=self.ris,
                optimizer=self.optimizer,
                mode=self.mode if len(self.rx_positions) == 1 else "cont",
                wave_model=self.wave_model,
                fc=self.fc,
                return_history=return_history and len(self.rx_positions) == 1,
            )
            if len(self.rx_positions) == 1:
                return (phases, history) if return_history else phases
            per_user_phases.append(phases)

        per_user_phases = np.stack(per_user_phases)
        combined = np.sum(
            self.user_weights[:, None, None] * np.exp(1j * per_user_phases), axis=0
        )
        phases = np.angle(combined)
        cancelled = np.abs(combined) <= 1e-12
        fallback = per_user_phases[np.argmax(self.user_weights)]
        phases[cancelled] = fallback[cancelled]

        if self.mode == "disc":
            phases = quantize_phases(
                phases, np.array(sorted(self.ris.phase_shifts_dict.values()))
            )
        if return_history:
            return phases, {
                "per_user_phases": per_user_phases,
                "user_weights": self.user_weights.copy(),
                "cancelled": cancelled,
            }
        return phases
