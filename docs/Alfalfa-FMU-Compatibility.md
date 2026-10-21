# Alfalfa FMU Compatibility Guide

> **Audience:** authors of the FMU Compilation Workbench (and anyone exporting
> Modelica-derived FMUs). This document describes exactly what an FMU must look
> like so it uploads **and runs** in Alfalfa. It is self-contained and can be
> copied into the FMU Workbench repo to drive autogeneration of compatible FMUs.

---

## TL;DR checklist

An FMU is Alfalfa-compatible when **all** of these are true:

- [ ] **FMI version 2.0** (not 1.0, not 3.0).
- [ ] **Co-Simulation** kind (the FMU embeds a `<CoSimulation>` element with binaries).
- [ ] **`linux64` binaries present** — `binaries/linux64/<model>.so` inside the FMU zip. Alfalfa runs the FMU in a Linux x86-64 container; macOS/Windows-only binaries will **not** load.
- [ ] At least one variable with causality **`input`** and one with causality **`output`** (these become Alfalfa points).
- [ ] Variable names contain **no spaces** and no exotic characters (use `snake_case`).

Recommended (not required, but avoids warnings / improves behavior):

- [ ] Embed an (at minimum empty) **`resources/kpis.json`** → `{}`.
- [ ] Provide sensible **start values** so the model does not trip physical assertions at t=0.
- [ ] Only declare **`min`/`max`** on an input if you actually want Alfalfa to clamp it (see below).

---

## How Alfalfa runs an FMU (so the contract makes sense)

1. **Upload.** A file whose name ends in `.fmu` is routed to the modelica job by
   extension (`alfalfa_worker/jobs/modelica/create_run.py`), which copies it to
   `model.fmu` and marks the run `READY`. **No validation happens at upload** — a
   successful upload does _not_ mean the model will run.
2. **Start.** `alfalfa_worker/jobs/modelica/step_run.py` → `initialize_simulation()`
   loads the FMU with `pyfmi.load_fmu` (via `alfalfa_worker/lib/testcase.py::TestCase`),
   and `setup_points()` reads its model variables to create:
   - one **INPUT** point for each variable whose causality is `input`, and
   - one **OUTPUT** point for each variable whose causality is `output`.
3. **Advance.** On each step Alfalfa writes the current input values into the FMU,
   performs a co-simulation step, and reads back the outputs.

If loading or reading variables fails, the run goes to **ERROR** at start — which
from the UI looks like "the FMU didn't work." Getting the contract below right is
what prevents that.

---

## Hard requirements

| Requirement         | What to export                                               | Why                                                                                                                 |
| ------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| **FMI version**     | `2.0`                                                        | Alfalfa rejects anything else (`FMU must be version 2.0.`).                                                         |
| **FMI kind**        | **Co-Simulation**                                            | Alfalfa steps the model itself; a Model-Exchange-only FMU has no solver to step.                                    |
| **Platform binary** | `binaries/linux64/<model>.so`                                | The worker is a Linux x86-64 container. Export/cross-compile the Linux binary even if you develop on macOS/Windows. |
| **Causality**       | `input` on variables to drive, `output` on variables to read | Only `input`/`output` variables become points. `parameter`/`local`/`internal` variables are ignored.                |
| **Names**           | `snake_case`, no spaces                                      | Names are used verbatim as point IDs; spaces are not sanitized reliably.                                            |

---

## Variable naming & causality → Alfalfa points

Alfalfa supports **two** styles. Pick one per model.

### Style A — Plain physical model (recommended for workbench models)

Just set standard Modelica causality. Names are used verbatim.

| Modelica variable | Causality | Becomes               |
| ----------------- | --------- | --------------------- |
| `T_in`            | `input`   | INPUT point `T_in`    |
| `m_flow`          | `input`   | INPUT point `m_flow`  |
| `u`               | `input`   | INPUT point `u`       |
| `Q_flow`          | `output`  | OUTPUT point `Q_flow` |
| `T_out`           | `output`  | OUTPUT point `T_out`  |

Nothing else is required. This is the right choice for the workbench's physical
component wrappers (boiler, valve, pump, etc.).

### Style B — BOPTEST overwrite convention (optional)

Use this only if you want BOPTEST-style "enable/override" semantics. For each
controllable signal you export a **pair** of inputs plus a suffixed output:

| Variable          | Causality | Role                                                           |
| ----------------- | --------- | -------------------------------------------------------------- |
| `<name>_u`        | `input`   | the value to write                                             |
| `<name>_activate` | `input`   | enable flag (`1` = use `_u`, `0` = use the model's own signal) |
| `<name>_y`        | `output`  | the resulting/measured value                                   |

Alfalfa creates a single INPUT point named `<name>_u`. The `_activate` flag is
**managed automatically**: when you set a value on the `_u` point Alfalfa writes
`_activate = 1`; when the value is cleared it writes `_activate = 0`. The `_y`
suffix on outputs is just a naming convention (outputs are otherwise treated the
same as Style A).

> Do **not** mix the styles for the same signal. If you export a lone `<name>_u`
> without a matching `<name>_activate`, it is treated as a plain Style-A input.

---

## Worked example: a Workbench-exported FMU

The workbench's physical component wrappers (e.g. `BoilerPolynomial_FMU`: inputs
`T_in`, `m_flow`, `u`; outputs `Q_flow`, `T_out`) already follow Style A and, once
built for `linux64`, run in Alfalfa without modification — they upload, reach
`READY`, start `RUNNING`, and produce INPUT/OUTPUT points automatically.

Two practical things to watch for with these single-component "two-port" wrappers:

1. **Build for `linux64`.** Use the workbench's `output/build-linux64` target so
   `binaries/linux64/*.so` is embedded; macOS/Windows-only binaries will not load
   in the worker.
2. **Provide meaningful inputs / start values.** Run with zero/default inputs and
   the underlying Modelica component may hit physical assertions (e.g. `T >= 1 K`).
   Drive the inputs (`T_in`, `m_flow`, `u`, …) with realistic values via the
   Alfalfa client.

---

## Optional resources

### `resources/kpis.json`

BOPTEST-wrapped FMUs embed `resources/kpis.json` (and sometimes
`resources/*.csv` forecast/price/weather data). Alfalfa **tolerates its absence** —
the model still loads and runs — but the UI shows a non-fatal notice explaining it
was missing. To suppress that notice and make the intent explicit, embed a minimal
file inside the FMU zip at `resources/kpis.json`:

```json
{}
```

If you want KPI reporting later, populate it BOPTEST-style, e.g.:

```json
{
  "ener_tot": ["Q_flow"],
  "tdis_tot": ["T_out"]
}
```

### Units, min, max, description

- **Units / description are optional.** Alfalfa tolerates variables with no declared
  `unit` or `description` (common for dimensionless control signals like a `0..1`
  valve command).
- **`min`/`max` are enforced when present.** If you declare `min`/`max` on an
  input, Alfalfa **clamps** incoming values to that range. Only declare bounds you
  actually want enforced. Leave them unset for unbounded control signals.

---

## Guidance for the FMU Workbench autogeneration

When generating FMUs, the workbench should:

1. **Always target FMI 2.0 Co-Simulation** in the export options.
2. **Emit the `linux64` binary** (`binaries/linux64/<model>.so`). Add a Linux
   build target to the pipeline even when building on macOS/Windows.
3. **Name I/O in `snake_case`** with no spaces; keep names stable across regen so
   Alfalfa point IDs are stable.
4. **Inject `resources/kpis.json` = `{}`** into every FMU zip by default (cheap,
   removes the "missing kpis.json" notice). Allow overriding with real KPIs.
5. **Set physically valid start values** on inputs (e.g. `T_in = 293.15`,
   `m_flow = 0.1`) so the model does not hit assertions such as `T >= 1 K` when
   started with zeros.
6. **Only declare `min`/`max`** on inputs where clamping is desired.
7. If BOPTEST semantics are wanted, **generate the `_u` / `_activate` / `_y`
   triplet** consistently; otherwise use plain causality (Style A).

A convenient post-export step is to unzip the FMU, ensure `resources/kpis.json`
exists (write `{}` if not), confirm `binaries/linux64/*.so` is present, and re-zip.

---

## Compatibility checklist (per exported FMU)

| Check              | Pass condition                                       |
| ------------------ | ---------------------------------------------------- |
| FMI version        | `modelDescription.xml` → `fmiVersion="2.0"`          |
| Kind               | `modelDescription.xml` contains `<CoSimulation ...>` |
| Linux binary       | `binaries/linux64/<model>.so` exists in the zip      |
| Inputs             | ≥1 `ScalarVariable` with `causality="input"`         |
| Outputs            | ≥1 `ScalarVariable` with `causality="output"`        |
| Names              | no spaces / special characters                       |
| KPIs (recommended) | `resources/kpis.json` present (may be `{}`)          |
| Bounds             | `min`/`max` set **only** where clamping is intended  |

---

## Historical note: relaxed BOPTEST-only assumptions

Earlier versions of `TestCase`/`Data_Manager` assumed every FMU was a
BOPTEST-wrapped model and would raise before the run could start when:

1. `resources/kpis.json` was missing from the FMU zip
   (`KeyError: 'resources/kpis.json'`), and
2. any non-`_activate` I/O variable had no declared `unit`
   (`FMUException: No unit was found for the variable ...`).

Both are now handled gracefully (see "Optional resources" above), so plain
OpenModelica FMUs run without needing to be re-wrapped BOPTEST-style.

---

## Troubleshooting: symptom → likely cause

| Symptom in Alfalfa                              | Likely cause                              | Fix                                                                                                |
| ----------------------------------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Run goes to **ERROR** immediately on start      | FMU failed to load                        | Verify FMI 2.0 **Co-Simulation** and that `binaries/linux64/*.so` exists (not just macOS/Windows). |
| `FMU must be version 2.0.`                      | Exported FMI 1.0 or 3.0                   | Re-export as FMI 2.0.                                                                              |
| Loads but has **no INPUT/OUTPUT points**        | No `input`/`output` causality declared    | Mark driveable/observable variables with the correct causality.                                    |
| Web notice: _"no resources/kpis.json"_          | KPI file not embedded                     | Add `resources/kpis.json` = `{}` (non-fatal; only a notice).                                       |
| Input value "ignored" / snapped to a limit      | `min`/`max` declared → value clamped      | Remove the bounds, or send a value within range.                                                   |
| Model errors after a few steps with zero inputs | Physical assertion at default/zero inputs | Provide realistic start values and drive the inputs.                                               |

---

_Generated for Alfalfa. Behavior described here reflects Alfalfa's modelica job
path, which accepts both plain OpenModelica Co-Simulation FMUs and BOPTEST-wrapped
FMUs._
