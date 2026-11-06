"""Run with: uv run --locked python examples/multiuser_superposition.py [--plot]."""

import argparse

import numpy as np

from surpRISe.channels.tx2ris2rx.tang_general_channel import tang_general_channel
from surpRISe.components.antenna import Antenna
from surpRISe.components.ris import RIS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot", action="store_true", help="Show the RIS phases")
    args = parser.parse_args()

    tx = Antenna([1.0, 0.5, 4.0], gain_dbi=6.0)
    rx = Antenna([2.0, 1.0, 3.0], gain_dbi=6.0)
    rx_positions = np.array([[2.0, 1.0, 3.0], [-2.0, 1.5, 4.0]])
    ris = RIS(
        center=[0, 0, 0],
        boresight="z",
        fc=3e9,
        Nrow=8,
        Ncol=8,
        delta_h=0.05,
        delta_v=0.05,
        dx=0.04,
        dy=0.04,
        phase_shifts_dict={0: 0.0, 1: np.pi},
        att_dict={0: 1.0, 1: 1.0},
    )
    channel = tang_general_channel()
    channel.optimize(
        mode="disc",
        wave_model="spherical",
        multiuser_method="superposition",
        tx_antenna=tx,
        rx_antenna=rx,
        ris=ris,
        rx_positions=rx_positions,
        user_weights=None,
    )
    gains = channel.path_gain_multrx(tx, rx, rx_positions, ris)
    for index, gain in enumerate(gains, start=1):
        print(f"User {index} path gain: {gain:.6e} ({10 * np.log10(gain):.2f} dB)")
    if args.plot:
        ris.plot_phase_dist()


if __name__ == "__main__":
    main()
