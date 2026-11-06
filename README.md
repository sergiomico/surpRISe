# surpRISe
Simulator Under Reconfigurable Propagation in RIS Environments

## Optimizing multiple receivers

Use the existing channel `optimize` method with an array of receiver positions
in meters. `tx`, `rx`, and `ris` below are configured `Antenna` and `RIS` instances;
`rx` supplies the common receiver hardware properties.

```python
import numpy as np

from surpRISe.channels.tx2ris2rx.tang_general_channel import tang_general_channel

channel = tang_general_channel()
rx_positions = np.array([[2.0, 1.0, 3.0], [-2.0, 1.5, 4.0]])
channel.optimize(
    tx_antenna=tx,
    rx_antenna=rx,
    ris=ris,
    rx_positions=rx_positions,
    multiuser_method="superposition",
    mode="disc",
    wave_model="spherical",
    user_weights=None,  # Equal field weights; optionally supply one per user.
)
gains = channel.path_gain_multrx(tx, rx, rx_positions, ris)
```

For more than one user, each beam uses continuous analytical phase compensation.
The shared phases are the angles of the weighted sum of the users' unit complex
phase vectors. Discrete mode quantizes only this final configuration to the RIS's
allowed phase states, which also select their associated attenuations. The
single-user `optimizer` argument is ignored for multiple users. This is a
multibeam heuristic and does not guarantee maximum sum power or equal coverage.
Near-zero sums use the highest-weight user's phase, choosing the first on ties.

With one row in `rx_positions`, optimization uses the selected single-user
algorithm and mode, preserving the original single-user result at that position.
Omitting `rx_positions` retains the original API. Input antennas are unchanged;
the supplied RIS receives the final shared configuration once.

Run the small deterministic regression suite with:

```powershell
uv run --locked python -m unittest discover -s tests
```

---

## 📥 Installation

To install the **surpRISe** package, follow the method below:

### From a local file (`.whl`)

1.  Download the package file (`.whl`) provided by the developer.
2.  Open a terminal (Command Prompt on Windows or Terminal on macOS/Linux).
3.  Execute the following command to install the module with **uv** or **pip**:
    ```bash
    # uv
    uv add "C:Users/YourUser/Documents/yourdir/surpRISe-0.1.0-py3-none-any.whl"

    # pip
    pip install "C:Users/YourUser/Documents/yourdir/surpRISe-0.1.0-py3-none-any.whl"
    ```
5.  Once the installation is complete, the module will be ready to use in your projects.

---
