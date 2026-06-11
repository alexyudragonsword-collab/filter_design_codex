# Architecture

## Design goals

The implementation follows the same broad separation used by mature filter-design tools while remaining independently testable:

1. **Specification** captures electrical intent and rejects contradictory edge ordering.
2. **Synthesis** computes order and normalized prototype values, then performs impedance/frequency transforms.
3. **Circuit representation** retains topology instead of flattening a design into display strings.
4. **Analysis** starts from the generated components, not from the synthesis transfer function. This catches transform and topology defects.
5. **Presentation and export** consume immutable domain results and contain no filter mathematics.

## Dependency direction

```text
Qt UI / cli / exporters
        ↓
     workflow
     ↙      ↘
synthesis  analysis
     ↘      ↙
       domain
```

The domain, synthesis, and analysis layers never import PySide6. Qt is isolated under `filter_design.ui`, so a future web UI or service can reuse the same workflow.

## Numerical model

Each series impedance and shunt admittance is represented by a two-port ABCD matrix. Matrices are cascaded in schematic order and converted to S parameters using the requested real port impedances. Phase is unwrapped before centered finite differences calculate group delay.

No NumPy dependency is required. This favors deployment simplicity for the current design sizes (normally fewer than 2,000 frequency samples). A future Monte Carlo module may add an optional vectorized backend behind the same analysis interface.

## Persistence

`.ofd.json` projects contain a mandatory integer version and the validated specification. Synthesized results are deliberately regenerated when opening a project so stale computed data cannot conflict with the current algorithm version.

## Current limitations

- Ideal inductors and capacitors only; no finite Q, ESR, self-resonance, or coupling.
- Ladder prototypes begin with a series element.
- Automatic synthesis targets equal real source/load impedances. Unequal values can be analyzed but generate a warning.
- No transmission-line, microstrip, active, digital, or electromagnetic geometry synthesis.
- The custom-painted Qt response widget is intentionally lightweight and currently displays insertion loss and return loss; CSV/S2P contain the numerical data for external plotting.


## Qt desktop architecture

The desktop layer uses Qt for Python (PySide6) and is split by responsibility:

- `SpecificationPanel` converts engineering-unit widget values into a validated domain specification.
- `DesignWorker` runs the existing workflow in a `QThread` and returns immutable domain results through signals.
- `ResponsePlot` and `SchematicView` are custom-painted widgets with no plotting-library dependency.
- `ComponentTableModel` exposes the synthesized topology through Qt's model/view API.
- `MainWindow` owns project actions, export actions, status reporting, and persisted `QSettings`.

Only the main GUI thread mutates widgets. The worker receives a complete immutable specification and never reads widget state.
