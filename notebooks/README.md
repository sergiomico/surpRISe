# Research notebooks

Start with the runnable [examples](../examples/) for the maintained API.
These notebooks are exploratory research material and have not all been rerun
against the current package. Saved outputs are historical illustrations rather
than current validation results. Some sweeps use large panels and dense grids.

Launch from the repository root after `uv sync --locked`:

```sh
uv run --locked jupyter lab
```

| Notebook | Subject |
| --- | --- |
| [test_freq_ris_opt.ipynb](test_freq_ris_opt.ipynb) | Design-frequency override and frequency-dependent propagation experiments |
| [test_disc_algs.ipynb](test_disc_algs.ipynb) | Discrete phase optimization comparisons |
| [test_newtangffmodel.ipynb](test_newtangffmodel.ipynb) | Tang channel construction and beam-pattern exploration |
| [test_paper_nf_ff_border.ipynb](test_paper_nf_ff_border.ipynb) | Chen paper, discrete phases, and near/far-field boundary exploration |
| [nf_to_ff_discrete_effects_simulations.ipynb](nf_to_ff_discrete_effects_simulations.ipynb) | Near/far-field effects with quantized RIS phase states |
| [sensing_tests.ipynb](sensing_tests.ipynb) | Exploratory channel-response and sensing calculations |

## Archive

[`archive/`](archive/) contains the previous `src/surpRISe/old_notebooks/`
collection. It is preserved outside the installable package. Historical imports,
class names, and workflows may require adaptation. Moving the notebooks does not
change their Git history. Do not use archived `test_` notebooks as automated tests.

Research outputs are preserved except for saved errors or text outputs exposing
local absolute paths removed during public-release preparation. Avoid committing
new large outputs or measurements without reviewing their contents.
