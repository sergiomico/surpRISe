# Contributing

surpRISe is maintained by [Sergio Mico-Rosa](https://github.com/sergiomico).
Use [GitHub issues](https://github.com/sergiomico/surpRISe/issues) for reproducible
bugs and proposals, or contact [sermiro@iteam.upv.es](mailto:sermiro@iteam.upv.es).

## Set up and validate

Use Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/sergiomico/surpRISe.git
cd surpRISe
uv sync --locked
uv run --locked python -m unittest discover -s tests
uv run --locked python examples/single_user.py
uv run --locked python examples/multiuser_superposition.py
uv build
```

Use `uv add` or `uv add --dev` for dependency changes and commit the corresponding
`uv.lock` update. Keep dependency upgrades separate from unrelated work.
See [development commands](docs/development.md) for more workflows.

## Numerical changes

Describe the physical assumptions, units, phase signs, array shapes, and any
normalization or tolerance changes. Include a small deterministic regression
case and justify numerical tolerances. Preserve existing single-user behavior
when adding new optimization methods. Do not infer experimental validation
from a passing smoke test. See [model conventions](docs/models.md).

Keep notebook source changes focused. Avoid committing newly generated large
outputs, raw measurements, credentials, or machine-specific paths. Archived
notebooks are historical material, not compatibility tests.

## Style and pull requests

Ruff uses an 88-character line limit and targets Python 3.12. Check new code with:

```sh
uv run --locked ruff check examples tests src/surpRISe/optimizers/tx_ris_rx_multiuser_opt.py
uv run --locked ruff format --check examples tests src/surpRISe/optimizers/tx_ris_rx_multiuser_opt.py
```

The rest of `src` has existing lint and formatting debt. Run
`uv run --locked ruff check src` to inspect it; avoid unrelated blanket fixes or
disabling checks to hide findings. CI enforces style on the paths above and
reports full-source lint separately without blocking on the existing debt.

Use a focused branch and describe the problem, resulting behavior, and checks
actually run. Prefer Conventional Commit messages such as `fix: ...` or
`feat: ...`. Contributions are provided under the repository's [MIT license](LICENSE).
