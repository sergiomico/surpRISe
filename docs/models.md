# Models and numerical conventions

This page describes the current implementation. The literature references
provide scientific background; they do not establish that every implementation
detail has been independently validated against a paper or measurement campaign.

## Link and geometry

The channel is the coherent sum of reflections along TX-RIS-element-RX paths.
It does not include direct TX-RX propagation, environmental multipath, noise,
mutual coupling, polarization, or a full-wave electromagnetic solution.
The general model uses spherical element-to-antenna distances; this does not
constitute a model of reactive near-field coupling.

The RIS is rectangular, with positive-axis boresight `x`, `y`, or `z`.
Element radiation patterns are cosine powers in the forward hemisphere and zero
behind the panel. Choose antenna positions consistent with the panel's front face.
Positions have shape `(Nrow, Ncol, 3)`; phase, state, and attenuation matrices
have shape `(Nrow, Ncol)`.

For boresight `z`, columns run along positive X and rows along negative Y.
For boresight `x`, columns run along positive Y and rows along negative Z.
For boresight `y`, columns run along negative X and rows along negative Z.

## Units and coordinates

| Quantity | Convention |
| --- | --- |
| Position, spacing, element dimensions | Meters |
| Carrier and sweep frequencies | Hz |
| RIS phase | Radians |
| Antenna gain input | dBi |
| RIS attenuation | Linear field amplitude |
| Path gain output | Linear power ratio |
| Path gain in dB | $10\log_{10}(G)$ |
| Coordinate utility input/output | Rows `[R, phi_deg, theta_deg]` |

In `sph2cart` and `cart2sph`, $\phi$ is azimuth from positive X toward positive Y,
and $\theta$ is the polar angle measured from positive Z. Some plotting and helper
docstrings call $\theta$ elevation; inspect the formula before supplying angles
from a convention measured above the XY plane.

Propagation uses $e^{-jkd}$ with $k=2\pi f/c$. The RIS reflection coefficient is
$a_n e^{j\phi_n}$. Phase-only beamforming power excludes attenuation, radiation
patterns, and geometric amplitude decay, so it is distinct from full path gain.

## Channel choices

`tang_general_channel` uses each element's TX and RX distances for phase and
amplitude, including element and antenna pattern factors. Its path gain is the
squared magnitude of its complex channel coefficient.

`tang_ff_channel` approximates phase using directions from the RIS center and
uses center distances for amplitude decay. Its complex-channel method includes
antenna-pattern factors. Its separate `path_gain_multrx` implementation omits
some of those factors and lacks a frequency-sweep argument. Do not assume its
path gain equals the squared magnitude returned by its complex-channel method.

Both complex-channel methods accept `f_vector`: one frequency returns `(Nrx,)`,
and multiple frequencies return `(Nrx, Nfreq)`. Propagation phase changes with
frequency while the chosen RIS reflection coefficients remain fixed. This is
not a frequency-dependent hardware scattering model. Pattern factors and gains
are also treated as fixed. The optimizer's optional `fc` selects the design
frequency; it does not change `ris.fc` or retune the hardware during evaluation.

For evaluation at multiple RX positions, the channel methods point the modeled
RX pattern toward the RIS center rather than using the template antenna's
pointing direction. They construct the RX cosine pattern from its gain; a
custom pattern defined on the RX template is not applied by these methods.

## Single-user configuration

Continuous compensation cancels the modeled propagation phase element by
element. Continuous mode assigns unit attenuation and state index `-1`.
Discrete mode maps phases to configured states and applies each state's
attenuation. State and attenuation dictionaries must have matching keys.

Available discrete algorithms are direct quantization (`direct_disc`), the
implementation labeled Chen Algorithm 1 (`chen_alg1`), grid search
(`grid_search`), iterative search (`iterative`), and one-dimensional search
(`1d_search`). These optimize phase-based objectives, not a general weighted
channel-power objective incorporating every pattern and attenuation factor.

Choose `spherical` or `plane` for optimization independently of the evaluation
channel. The plane optimization omits a common propagation phase while the
far-field complex channel retains center-distance phase. A common phase can
matter when comparing complex coefficients even when power is unchanged.

## Multiuser superposition

For $K>1$, the solver computes continuous phases $\phi_{k,n}$ for every user,
even if the requested final RIS mode is discrete. The combined phase is

$$
\phi_n = \arg\left(\sum_{k=1}^{K} w_k e^{j\phi_{k,n}}\right).
$$

Weights must be finite and nonnegative, with at least one positive value.
They scale field vectors, not received powers, and are normalized internally.
Equal weights are the default. Scaling every weight by a common positive factor
does not change the configuration.

When the normalized complex sum has magnitude at most $10^{-12}$, the solver
uses the highest-weight user's phase for that element, selecting the first
user on ties. In discrete mode, the combined phases are quantized once, after
superposition. The single-user discrete `optimizer` selection is ignored for
$K>1$. There is no guarantee of maximum sum power, fairness, or a minimum gain
for every user.

For $K=1$, the selected single-user algorithm and mode are used directly.
The optimizer copies the RX hardware template for each supplied position and
points it at the panel center. The channel entry point applies the final shared
configuration to the original RIS once. Standalone
`tx_ris_rx_superposition_opt.optimize()` returns phases without updating the RIS;
`return_history=True` also exposes per-user phases, weights, and cancellation
flags for $K>1$.

## References

- W. Tang et al., [Wireless Communications With Reconfigurable Intelligent Surface:
  Path Loss Modeling and Experimental Measurement](https://ieeexplore.ieee.org/document/9206044),
  IEEE Transactions on Wireless Communications, 2021.
  Background for near/far-field RIS path-loss modeling and radiation patterns.
- W. Tang et al., [Path Loss Modeling and Measurements for Reconfigurable Intelligent
  Surfaces in the Millimeter-Wave Frequency Band](https://ieeexplore.ieee.org/document/9837936/),
  IEEE Transactions on Communications, 2022.
  Additional background on element-area and radiation-pattern modeling.
- Z. Chen, L. X. Cai, and X. Hao, [Near-Field and Far-Field Beamforming Design for
  RIS-enabled Millimeter Wave Systems](https://doi.org/10.1109/VTC2024-SPRING62846.2024.10683528),
  IEEE VTC Spring, 2024. The source code attributes `chen_alg1` to this paper;
  the repository also contains exploratory notebooks on its near/far-field border.
