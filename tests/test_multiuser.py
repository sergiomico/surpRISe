"""Small deterministic checks: uv run --locked python -m unittest discover -s tests."""

import contextlib
import copy
import io
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

from surpRISe.channels.tx2ris2rx.tang_ff_channel import tang_ff_channel
from surpRISe.channels.tx2ris2rx.tang_general_channel import tang_general_channel
from surpRISe.components.antenna import Antenna
from surpRISe.components.ris import RIS
from surpRISe.optimizers import tx_ris_rx_multiuser_opt as multiuser
from surpRISe.optimizers import tx_ris_rx_opt as single


class SuperpositionTests(unittest.TestCase):
    def setUp(self):
        # Existing solvers print Greek characters; capture progress independently
        # of the Windows console encoding and keep test output concise.
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)
        self.tx = Antenna([1.0, 0.5, 4.0], 6.0)
        self.rx = Antenna([2.0, 1.0, 3.0], 6.0)
        self.positions = np.array([self.rx.position, [-2.0, 1.5, 4.0]])
        self.ris = RIS(
            fc=3e9,
            Nrow=3,
            Ncol=4,
            delta_h=0.05,
            delta_v=0.05,
            dx=0.04,
            dy=0.04,
            phase_shifts_dict={0: 0.0, 1: np.pi},
            att_dict={0: 0.9, 1: 0.8},
        )

    def test_one_user_matches_original_algorithms(self):
        algorithms = {
            "direct_disc": single.tx_ris_rx_direct_disc_opt,
            "chen_alg1": single.tx_ris_rx_chen_alg1_opt,
            "grid_search": single.tx_ris_rx_max_bf_grid_search_opt,
            "iterative": single.tx_ris_rx_max_bf_iterative_opt,
            "1d_search": single.tx_ris_rx_max_bf_1D_search_opt,
        }
        for wave_model in ("spherical", "plane"):
            for name, algorithm in algorithms.items():
                with self.subTest(wave_model=wave_model, optimizer=name):
                    expected = algorithm(
                        self.tx, self.rx, self.ris, wave_model, fc=3.1e9
                    ).optimize()
                    for channel_type in (tang_general_channel, tang_ff_channel):
                        for positions in (None, self.positions[:1]):
                            panel = copy.deepcopy(self.ris)
                            channel_type().optimize(
                                optimizer=name,
                                mode="disc",
                                wave_model=wave_model,
                                tx_antenna=self.tx,
                                rx_antenna=self.rx,
                                ris=panel,
                                fc=3.1e9,
                                rx_positions=positions,
                            )
                            np.testing.assert_array_equal(
                                panel.get_all_phase_shifts(), expected
                            )
            _, expected = single.calc_tx_ris_rx_cont_opt(
                self.tx, self.rx, self.ris, wave_model, fc=3.1e9
            )
            panel = copy.deepcopy(self.ris)
            tang_general_channel().optimize(
                mode="cont",
                wave_model=wave_model,
                tx_antenna=self.tx,
                rx_antenna=self.rx,
                ris=panel,
                fc=3.1e9,
                rx_positions=self.positions[:1],
                verbose=True,
            )
            np.testing.assert_array_equal(panel.get_all_phase_shifts(), expected)

    def test_multiuser_continuous_then_final_quantization(self):
        original_rx = self.rx.position.copy()
        original_pointing = self.rx.pointing_direction.copy()
        original_states = self.ris.get_all_state_indices()
        weights = np.array([1.0, 0.7])
        for wave_model in ("spherical", "plane"):
            user_phases = []
            for position in self.positions:
                receiver = Antenna(position, self.rx.gain_dbi)
                _, phases = single.calc_tx_ris_rx_cont_opt(
                    self.tx, receiver, self.ris, wave_model, fc=3.1e9
                )
                user_phases.append(phases)
            expected_cont = np.angle(
                np.sum(
                    weights[:, None, None] * np.exp(1j * np.array(user_phases)), axis=0
                )
            )
            expected_disc = single.quantize_phases(
                expected_cont, np.array([0.0, np.pi])
            )
            for mode, expected in (("cont", expected_cont), ("disc", expected_disc)):
                with self.subTest(wave_model=wave_model, mode=mode):
                    solver = multiuser.tx_ris_rx_superposition_opt(
                        self.tx,
                        self.rx,
                        self.positions,
                        self.ris,
                        mode=mode,
                        wave_model=wave_model,
                        fc=3.1e9,
                        user_weights=weights,
                    )
                    with patch.object(
                        multiuser,
                        "calc_tx_ris_rx_phase_opt",
                        wraps=single.calc_tx_ris_rx_phase_opt,
                    ) as solve:
                        actual = solver.optimize()
                    self.assertEqual(solve.call_count, 2)
                    self.assertTrue(
                        all(
                            call.kwargs["mode"] == "cont"
                            for call in solve.call_args_list
                        )
                    )
                    np.testing.assert_allclose(actual, expected, atol=1e-12)
                    for channel_type in (tang_general_channel, tang_ff_channel):
                        panel = copy.deepcopy(self.ris)
                        channel = channel_type()
                        with patch.object(
                            panel, "set_all_shift", wraps=panel.set_all_shift
                        ) as apply:
                            channel.optimize(
                                mode=mode,
                                wave_model=wave_model,
                                tx_antenna=self.tx,
                                rx_antenna=self.rx,
                                ris=panel,
                                rx_positions=self.positions,
                                fc=3.1e9,
                                user_weights=weights,
                                verbose=True,
                            )
                        apply.assert_called_once()
                        self.assertEqual(channel.last_optimizer, "superposition")
                        np.testing.assert_allclose(
                            panel.get_all_phase_shifts(), expected, atol=1e-12
                        )
                        gains = channel.path_gain_multrx(
                            self.tx, self.rx, self.positions, panel
                        )
                        self.assertEqual(gains.shape, (2,))
                        self.assertTrue(np.all(np.isfinite(gains)))
                        self.assertTrue(np.all(gains > 0))
        np.testing.assert_array_equal(self.rx.position, original_rx)
        np.testing.assert_array_equal(self.rx.pointing_direction, original_pointing)
        np.testing.assert_array_equal(self.ris.get_all_state_indices(), original_states)

    def test_cancellation_falls_back_to_first_highest_weight_user(self):
        first = np.full((3, 4), 0.3)
        opposite = first + np.pi
        with patch.object(
            multiuser,
            "calc_tx_ris_rx_phase_opt",
            side_effect=[(first, None), (opposite, None)],
        ):
            phases, history = multiuser.tx_ris_rx_superposition_opt(
                self.tx, self.rx, self.positions, self.ris, mode="cont"
            ).optimize(return_history=True)
        np.testing.assert_array_equal(phases, first)
        self.assertTrue(np.all(history["cancelled"]))

    def test_invalid_users_and_weights(self):
        for positions in ([], [1, 2, 3], [[1, 2]], [[np.nan, 0, 1]], [[0, 0, 0]]):
            with self.subTest(positions=positions), self.assertRaises(ValueError):
                multiuser.tx_ris_rx_superposition_opt(
                    self.tx, self.rx, positions, self.ris
                )
        for weights in ([1], [0, 0], [-1, 1], [np.inf, 1]):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                multiuser.tx_ris_rx_superposition_opt(
                    self.tx, self.rx, self.positions, self.ris, user_weights=weights
                )


if __name__ == "__main__":
    unittest.main()
