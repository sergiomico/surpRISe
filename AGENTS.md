# Project instructions

## Purpose and scope

`surpRISe` means Simulator Under Reconfigurable Propagation in RIS Environments.
It is a Python research library for simulating channels assisted by a
Reconfigurable Intelligent Surface (RIS), currently centered on the TX-RIS-RX
reflection path. It models antenna patterns, rectangular RIS geometry, complex
channel coefficients, path gain, and phase beamforming. Experiments explore
near-field and far-field propagation, phase quantization, frequency sweeps, and
RIS configuration optimization.

Treat numerical behavior and physical assumptions as part of the public contract.
Do not add propagation paths or claim support for effects absent from the code.

## Technologies and layout

- Python `>=3.12`, with a `src` package layout. Preserve the import spelling
  `surpRISe`, including its capitalization.
- `uv` manages dependencies, environments, execution, and builds. `pyproject.toml`
  declares dependencies and tools; `uv.lock` records resolved dependencies.
- Hatchling is the build backend.
- NumPy handles arrays and complex arithmetic; SciPy supplies physical constants.
- Matplotlib and SciencePlots provide scientific plots; Plotly provides
  interactive plots. Jupyter and Ruff are development dependencies.
- `src/surpRISe/components/antenna.py`: `Antenna`, position, gain, pointing, and
  normalized radiation patterns.
- `src/surpRISe/components/ris.py`: `RIS`, panel geometry, element states,
  attenuation, phase shifts, radiation patterns, and configuration plots.
- `src/surpRISe/channels/tx2ris2rx/tx2ris2rx.py`: abstract channel interface,
  optimizer dispatch, and spatial/angular visualization helpers.
- `src/surpRISe/channels/tx2ris2rx/tang_general_channel.py`: Tang general model
  using individual element distances.
- `src/surpRISe/channels/tx2ris2rx/tang_ff_channel.py`: Tang far-field model
  using plane-wave phase approximations and center-distance amplitude decay.
- `src/surpRISe/optimizers/tx_ris_rx_opt.py`: spherical/plane propagation phase,
  continuous compensation, direct phase quantization, Chen algorithm 1, grid
  search, iterative search, and one-dimensional search.
- `src/surpRISe/optimizers/tx_ris_rx_multiuser_opt.py`: weighted complex-phase
  superposition. K>1 always solves continuous user beams and quantizes only the
  final configuration in discrete mode; K=1 retains the single-user algorithm.
- `src/surpRISe/utils/utils.py`: coordinate conversion, distances, numerical
  rounding, and a far-field boundary estimate.
- `notebooks/`: research experiments and usage examples.
- `notebooks/archive/`: historical experiments; do not treat them as
  authoritative API documentation or regenerate them as routine validation.
- `examples/`: small runnable single-user and multiuser simulations; plotting
  requires the optional `--plot` flag.
- `README.md`: public setup and usage guide. `docs/models.md`: conventions,
  limitations, and literature. `CONTRIBUTING.md` and `docs/development.md`:
  development workflows. `LICENSE`: MIT, Sergio Mico-Rosa (`sergiomico`).
- `.github/workflows/ci.yml`: tests, examples, scoped style checks, and builds
  on Python 3.12 for Linux and Windows. Full-source lint debt is nonblocking.

## Environment and commands

Run commands from the repository root. Prefer `uv` over direct `pip` installation
or manual virtual-environment management.

```powershell
uv sync --locked
uv run --locked ruff check src
uv run --locked ruff format --check src
uv run --locked python -c "from surpRISe.components.ris import RIS; from surpRISe.channels.tx2ris2rx.tang_general_channel import tang_general_channel"
uv run --locked jupyter lab
uv run --locked python examples/single_user.py
uv run --locked python examples/multiuser_superposition.py
uv build
```

Use `uv add` or `uv add --dev` for intentional dependency changes and review both
`pyproject.toml` and `uv.lock`. Do not update dependencies incidentally. Build when
packaging changes require it; generated distributions must remain untracked.

## Numerical and API conventions

- Positions and distances are in meters; frequencies are in Hz. Phase shifts are
  in radians. Antenna gains are supplied in dBi and converted to linear scale.
- Coordinate utilities accept/return rows `[R, phi_deg, theta_deg]`; `phi` is
  azimuth and `theta` is the polar angle from positive Z, as defined by their
  formulas. Some docstrings call `theta` elevation; inspect the implementation
  before translating between angle conventions.
- RIS positions have shape `(Nrow, Ncol, 3)`. State, phase, attenuation, and
  reflection-coefficient arrays have shape `(Nrow, Ncol)`. Receiver positions
  have shape `(Nrx, 3)`.
- Channel coefficient methods return complex values with shape `(Nrx,)` for one
  frequency and `(Nrx, Nfreq)` for multiple frequencies. Preserve this behavior.
- Preserve propagation phase `exp(-1j * k * distance)` and reflection coefficient
  `attenuation * exp(1j * phase)`. Distinguish field amplitude, power, linear
  gain, and decibels; power gain uses `10 * log10`.
- `phase_bf_multrx` computes phase-only beamforming power, distinct from the full
  channel and path gain with attenuation, patterns, and distance factors.
- Discrete RIS states pair phase and attenuation dictionaries with matching
  keys. Continuous mode uses arbitrary phases, unit attenuation, and state `-1`.
- Channel `optimize` mutates the supplied RIS. Keep its `disc`/`cont` modes and
  `spherical`/`plane` wave models explicit. A frequency override for optimization
  is distinct from `ris.fc` and from a channel evaluation frequency sweep.
- Explain changes to approximations, normalization, tolerances, orientation, or
  phase signs. Preserve complex precision and avoid changing formulas merely
  to satisfy lint. Record experiment parameters and random seeds when relevant.

## Validation and existing limitations

`tests/test_multiuser.py` contains small deterministic regression checks using
standard-library `unittest`. Run:

```powershell
uv run --locked python -m unittest discover -s tests
```

There is no additional test runner dependency. CI runs these tests, the
headless examples, scoped Ruff checks, and package builds.
Notebook names beginning with `test_` do not constitute an automated suite.
Do not claim comprehensive validation from imports or lint alone.

For numerical changes, run a small deterministic example covering the changed
behavior. Check shapes, finite values, and relevant physical invariants with
justified tolerances. Useful checks include continuous phase alignment,
discrete-state membership, frequency-sweep shapes, and general/far-field
agreement at sufficiently large distances. Add focused regression tests for
substantive numerical fixes when appropriate, stating how to run them.

The following are existing caveats, not instructions to fix unrelated code:

- Ruff targets `py312`, matching the package's minimum Python version. CI
  enforces lint and formatting for `examples`, `tests`, and the multiuser
  optimizer. Inspect full-source findings without blanket cleanup.
- Existing code contains lint/style issues, wildcard imports, and a duplicated
  `plot_phase_bf_angle_2d_polar` definition. Avoid blanket formatting or cleanup.
- Far-field `path_gain_multrx` is a separate implementation from
  `channel_matrix_multrx`; it lacks the latter's frequency-sweep argument and
  does not apply all of its antenna-pattern factors. Do not assume they match.
- Plotting modules modify global Matplotlib styles and set a notebook Plotly
  renderer on import. Use a noninteractive backend for numerical smoke checks
  where needed, and avoid opening plots during unattended validation.

For documentation-only changes, inspect the content and run `git diff --check`.
Report checks actually run, failures, and unavailable checks. Keep existing
failures distinct from regressions introduced by the task.

## Editing, writing, and Git

Keep changes scoped to the requested task. Preserve existing public names and
notebook workflows unless a change explicitly requires otherwise. Do not
rewrite notebook outputs, run costly sweeps, or commit generated data and plots
as a side effect of reviewing the project.

Use plain language, ASCII dashes instead of em dashes, `$x$` for inline math,
and `$$x$$` for display math. Keep commands, paths, and identifiers in backticks.

After meaningful tracked-file changes, review status and diffs, perform relevant
validation, and create an atomic local Conventional Commit. Stage task-related
paths explicitly; preserve user and concurrent changes. Ask if ownership is
unclear. Never commit secrets, raw/large measurements, generated binaries,
temporary files, or ignored files, or change ignore rules to include them.

Push only with explicit authorization or explicit project policy. Do not infer
authorization from command examples. Report validation results, commit hash
and message, push destination/status, and remaining task changes.
