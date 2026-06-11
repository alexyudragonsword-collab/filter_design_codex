# Roadmap and product boundary

This roadmap keeps separate mathematical domains separate rather than presenting an incomplete imitation of a commercial suite.

## 0.1 — Lumped passive MVP (implemented)

- Butterworth and Chebyshev-I low/high/band-pass/band-stop synthesis.
- Automatic order, LC ladder generation, ABCD/S-parameter verification.
- Desktop and CLI workflows, project persistence, CSV/S2P/SPICE/HTML export.

## 0.2 — Manufacturability

- E-series component rounding with optimization after rounding.
- Finite Q, ESR/ESL, self-resonance, and vendor component models.
- Deterministic worst-case and seeded Monte Carlo tolerance analysis.
- Response envelopes, yield metrics, and sensitivity ranking.

## 0.3 — Additional lumped approximations

- Bessel, inverse Chebyshev, elliptic, and Gaussian families.
- Zero-bearing canonical and Cauer topologies.
- Source-first shunt topology and impedance-transforming terminations.

Each family must include independent tabulated references and circuit-response tests before UI registration.

## 0.4 — Digital filters

A separate synthesis provider for FIR/IIR design, SOS representation, quantization analysis, and C/CMSIS coefficient export. Digital filters will not be forced into the LC circuit model.

## 0.5 — Active filters

Sallen-Key and multiple-feedback realization, op-amp gain-bandwidth/noise constraints, and SPICE model export.

## 0.6 — Matching and distributed filters

- L/π/T impedance-matching networks.
- Transmission-line and microstrip realizations with explicitly selected substrate models.
- Neutral geometry/netlist export for external EM tools.

Direct proprietary project generation or undocumented automation of commercial solvers is outside the core project boundary. Integrations should use documented public APIs or neutral interchange formats.
