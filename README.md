# surpRISe

**Simulator Under Reconfigurable Propagation in RIS Environments**

A Python research library for simulating wireless channels through a
Reconfigurable Intelligent Surface (RIS). Model a TX-RIS-RX link, configure
continuous or discrete RIS phases, and evaluate complex channel coefficients,
path gains, and beamforming patterns at one or multiple receiver positions.

**Status:** research software under active development. The current regression
suite covers small deterministic optimization cases, not comprehensive physical
or experimental validation. Python **3.12+** is required.

## Capabilities

- Tang general channel model with element-wise spherical propagation distances.
- Tang far-field model with plane-wave phase and center-distance amplitude
  approximations.
- Rectangular RIS panels with configurable orientation, element spacing,
  radiation patterns, phase states, and state-dependent attenuation.
- Continuous phase compensation and five discrete single-user optimizers.
- Multiuser phase superposition with optional user weights.
- Multiple RX evaluation positions and channel-coefficient frequency sweeps.
- Matplotlib/SciencePlots and interactive Plotly visualizations.

The implementation uses NumPy and SciPy for numerical calculations, Hatchling
for packaging, and `uv` for dependency and environment management. It currently
models the reflected TX-RIS-RX path; it does not add a direct TX-RX path,
random multipath fading, noise, or a full communication protocol stack.

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then clone
and synchronize the project:

```sh
git clone https://github.com/sergiomico/surpRISe.git
cd surpRISe
uv sync --locked
```

This installs the library in editable mode plus Jupyter and Ruff. Commands below
run from the repository root; there is no need to activate the virtual environment.
Installation guidance here uses the repository rather than assuming a PyPI release.
For local wheel installation, see [development commands](docs/development.md).

## First simulation

This complete example creates a 3 GHz, 8-by-8, one-bit RIS at the origin, with
its normal along positive Z. Both antennas are placed in front of the panel.

```python
import numpy as np

from surpRISe.channels.tx2ris2rx.tang_general_channel import tang_general_channel
from surpRISe.components.antenna import Antenna
from surpRISe.components.ris import RIS

tx = Antenna([1.0, 0.5, 4.0], gain_dbi=6.0)
rx = Antenna([2.0, 1.0, 3.0], gain_dbi=6.0)
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
    optimizer="direct_disc",
    mode="disc",
    wave_model="spherical",
    tx_antenna=tx,
    rx_antenna=rx,
    ris=ris,
)
gains = channel.path_gain_multrx(tx, rx, rx.position[None, :], ris)
print("Path gain (dB):", 10 * np.log10(gains))
```

`optimize()` updates the supplied RIS in place. Choose `mode="cont"` for
analytical continuous phase compensation with unit element attenuation.
Discrete mode uses the configured states and their associated attenuations.

Run the standalone version, optionally showing the phase distribution:

```sh
uv run --locked python examples/single_user.py
uv run --locked python examples/single_user.py --plot
```

## Multiple users

Continue from the setup above, supplying one row per user:

```python
rx_positions = np.array([[2.0, 1.0, 3.0], [-2.0, 1.5, 4.0]])
channel.optimize(
    mode="disc",
    wave_model="spherical",
    tx_antenna=tx,
    rx_antenna=rx,
    ris=ris,
    rx_positions=rx_positions,
    multiuser_method="superposition",
    user_weights=None,  # Equal field weights, or one nonnegative weight per user.
)
gains = channel.path_gain_multrx(tx, rx, rx_positions, ris)
print("Per-user path gains (dB):", 10 * np.log10(gains))
```

For $K>1$, each user gets a continuous phase solution. The algorithm combines
unit complex phase vectors and extracts their shared phase, quantizing only
that final result in discrete mode. The discrete `optimizer` selection is
ignored for $K>1$. `rx` provides the common receiver hardware properties; the
original antennas are unchanged. This is a multibeam heuristic, with no guarantee
of maximum sum power or equal user coverage.

For $K=1$, the selected single-user algorithm and mode are preserved. Omitting
`rx_positions` uses the original single-user API. See [model details](docs/models.md)
for weights, cancellation behavior, and physical conventions.

```sh
uv run --locked python examples/multiuser_superposition.py
```

## Models and optimization

| Choice | Available values |
| --- | --- |
| Channel | `tang_general_channel`, `tang_ff_channel` |
| Optimization wave model | `spherical`, `plane` |
| RIS phase mode | `cont`, `disc` |
| Single-user discrete optimizer | `direct_disc`, `chen_alg1`, `grid_search`, `iterative`, `1d_search` |
| Multiuser method | `superposition` |

The channel model and optimization wave model are separate choices. For example,
a plane-wave-designed RIS can be evaluated using the general channel.

Positions and distances use meters, frequencies use Hz, and RIS phases use
radians. Antenna gains are specified in dBi; path gains are returned in linear
power scale. Receiver positions have shape `(Nrx, 3)`. Complex channel methods
return `(Nrx,)` for one frequency and `(Nrx, Nfreq)` for a frequency vector.

**Current limitations:** far-field `path_gain_multrx` is a separate implementation
from `channel_matrix_multrx` and does not apply all of its antenna-pattern factors
or expose its frequency-sweep argument. Plotting imports modify global styles
and select a notebook Plotly renderer. See [model assumptions and references](docs/models.md)
before comparing simulations or interpreting angle conventions.

## Examples, notebooks, and development

- [Single-user script](examples/single_user.py) and [multiuser script](examples/multiuser_superposition.py): small runnable starting points.
- [Notebook guide](notebooks/README.md): exploratory experiments and historical archives.
- [Contributing](CONTRIBUTING.md): environment, validation, and numerical-change guidelines.
- [Development commands](docs/development.md): packaging, editable installation, and reproducibility.

```sh
uv run --locked python -m unittest discover -s tests
uv build
```

GitHub Actions is configured to run tests, headless examples, scoped style checks,
and package builds on Python 3.12 for Linux and Windows. Existing full-source
lint debt is reported separately; a passing scoped check does not mean the entire
library is lint-clean.

## Author and license

Maintained by [Sergio Mico-Rosa](https://github.com/sergiomico).
Contact: [sermiro@iteam.upv.es](mailto:sermiro@iteam.upv.es).
Report reproducible problems through [GitHub issues](https://github.com/sergiomico/surpRISe/issues).

Released under the [MIT license](LICENSE). Scientific background and algorithm
references are listed in [the model documentation](docs/models.md#references).
