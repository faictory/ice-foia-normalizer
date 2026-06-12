# deportation-foia-normalizer

## Charter

`deportation-foia-normalizer` is a command-line tool that lets advocates and journalists turn one
raw ICE FOIA dump (a messy CSV or XLSX from the Deportation Data Project) into a clean,
canonical-schema table — with normalized ISO-8601 dates, stable column names, a per-row rejects
file, and a coercion/rejection summary — in a single deterministic command.

## Command Surface

The tool exposes **one** command: normalize a single raw FOIA file. Canonical invocation form is
`python -m deportation_foia_normalizer <INPUT> [flags]` (the installed console script
`deportation-foia-normalizer` is an exact alias). There are no subcommands.

| Element | Kind | Takes | What it does |
| --- | --- | --- | --- |
| `INPUT` | positional arg (required) | path to a `.csv` or `.xlsx` raw FOIA file | The single dump to normalize. Format detected by extension. |
| `-o, --output` | flag | path | Destination for the clean canonical table. Default: `<INPUT-stem>.normalized.csv` (or `.sqlite` when `--format sqlite`) beside the input. |
| `--format` | flag | `csv` \| `sqlite` | Output table format. Default `csv`. `sqlite` writes a single table named `records`. |
| `--rejects` | flag | path | Destination for the rejects file (original rows that failed validation, each annotated with a reason). Default: `<INPUT-stem>.rejects.csv`. |
| `--report` | flag | `text` \| `json` | Format of the summary report printed to **stdout**. Default `text`. |
| `--schema` | flag | path | Path to a custom canonical-schema/mapping config (YAML or JSON) that replaces the bundled default mapping. Default: the bundled schema. |
| `--strict` | flag (boolean) | — | Treat any value coercion as a failure: the run exits non-zero (code 3) if one or more rows required coercion. Rows are still written. |
| `--version` | flag | — | Print the tool version and exit 0. |
| `-h, --help` | flag | — | Print usage for the command surface above and exit 0. |

## Output schema/format

The tool produces up to **three artifacts** plus an **exit code**. None of the data artifacts are
JSON; the only optionally-JSON output is the stdout report under `--report json`.

### 1. Clean canonical table (`--output`)

Canonical columns, in this fixed order, with these documented meanings:

| Column | Type | Normalization |
| --- | --- | --- |
| `record_id` | string | Carried through; synthesized from source row number if absent. |
| `event_type` | enum `arrest` \| `detainer` \| `removal` | Lower-cased, code-mapped (e.g. `ARR`→`arrest`). **Required.** |
| `event_date` | ISO-8601 `YYYY-MM-DD` | Parsed from mixed source formats. **Required.** |
| `field_office` | string | Trimmed; from any AOR/field-office alias. |
| `nationality` | string | Trimmed country name/code, upper-cased. |
| `gender` | enum `M` \| `F` \| `U` | Code-mapped (`1`/`Male`→`M`, `2`/`Female`→`F`, blank→`U`). |
| `removal_country` | string | Trimmed; blank when not applicable. |

For `csv`: a header row of exactly the columns above, comma-separated, UTF-8, `\n` line endings,
rows in input order. For `sqlite`: one table `records` with those columns as `TEXT`, same row order.

### 2. Rejects file (`--rejects`)

CSV containing every **original** input column verbatim, plus two appended columns:
`__source_row` (1-based row number in the input) and `__reject_reason` (a short human string, e.g.
`unparseable event_date: "32/13/2026"` or `event_type not in {arrest,detainer,removal}: "xyz"`).
A row appears in exactly one of the clean table or the rejects file — never silently dropped.

### 3. Summary report (stdout, `--report`)

`text` (default) — literal shape:

```
deportation-foia-normalizer 1.0.0
input:           examples/sample.csv
output:          examples/sample.normalized.csv (csv)
rejects:         examples/sample.rejects.csv
rows ingested:   12
rows normalized: 10
rows coerced:    7
rows rejected:   2
column mappings:
  Event Date        -> event_date
  Apprehension AOR  -> field_office
  Citizenship       -> nationality
  Sex               -> gender
reject reasons:
  unparseable event_date: 1
  event_type not in enum: 1
exit: 0
```

`json` — a single object: `{"version", "input", "output", "format", "rejects",
"rows_ingested", "rows_normalized", "rows_coerced", "rows_rejected",
"column_mappings": {<source>: <canonical>}, "reject_reasons": {<reason>: <count>}, "exit_code"}`.

Invariant: `rows_ingested == rows_normalized + rows_rejected`; `rows_coerced <= rows_normalized`.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success (rows may have been rejected; that is not a failure). |
| `2` | A **required** canonical column (`event_type` or `event_date`) could not be mapped from the input. The error names the missing canonical column and the source headers seen. |
| `3` | `--strict` was set and at least one row required coercion. |
| `1` | Unexpected error (missing/unreadable input file, unparseable file, bad `--schema`). |

## Default no-flag behavior

Running the tool with only the required `INPUT` and no flags demonstrates the headline use case:
read the raw dump, map drifting column names to the canonical schema, normalize dates and coded
fields, validate every row, write the clean canonical CSV and the rejects CSV beside the input, and
print the text summary to stdout. Worked example:

```
$ python -m deportation_foia_normalizer examples/sample.csv
deportation-foia-normalizer 1.0.0
input:           examples/sample.csv
output:          examples/sample.normalized.csv (csv)
rejects:         examples/sample.rejects.csv
rows ingested:   12
rows normalized: 10
rows coerced:    7
rows rejected:   2
column mappings:
  Event Date        -> event_date
  Apprehension AOR  -> field_office
  Citizenship       -> nationality
  Sex               -> gender
reject reasons:
  unparseable event_date: 1
  event_type not in enum: 1
exit: 0
```

This writes `examples/sample.normalized.csv` (canonical schema, ISO dates, stable headers) and
`examples/sample.rejects.csv` (the 2 bad rows with reasons), and exits 0.

## Canonical invocations

1. **Headline / default** — normalize one dump to CSV beside it:
   ```
   $ python -m deportation_foia_normalizer examples/sample.csv
   ... text summary (see above) ... exit: 0
   ```

2. **SQLite output to a chosen path** — `--format` + `--output`:
   ```
   $ python -m deportation_foia_normalizer examples/sample.csv --format sqlite -o out/records.sqlite
   ...
   output:          out/records.sqlite (sqlite)
   exit: 0
   # out/records.sqlite now holds table `records` with the canonical columns
   ```

3. **Machine-readable run with explicit rejects path** — `--report json` + `--rejects`:
   ```
   $ python -m deportation_foia_normalizer examples/sample.csv --report json --rejects out/bad.csv
   {"version":"1.0.0","input":"examples/sample.csv","output":"examples/sample.normalized.csv",
    "format":"csv","rejects":"out/bad.csv","rows_ingested":12,"rows_normalized":10,
    "rows_coerced":7,"rows_rejected":2,"column_mappings":{"Event Date":"event_date",...},
    "reject_reasons":{"unparseable event_date":1,"event_type not in enum":1},"exit_code":0}
   ```

4. **Custom mapping for a renamed dump** — `--schema`:
   ```
   $ python -m deportation_foia_normalizer 2026q1.csv --schema configs/q1-mapping.yaml
   ... column mappings reflect q1-mapping.yaml ... exit: 0
   ```

5. **Strict gate for CI / fail on missing required column** — `--strict` and the required-mapping guard:
   ```
   $ python -m deportation_foia_normalizer examples/sample.csv --strict
   ... rows coerced: 7 ... exit: 3        # coercion occurred under --strict

   $ python -m deportation_foia_normalizer no_date_column.csv
   error: required canonical column 'event_date' could not be mapped from input headers
          [Name, Country, AOR]
   exit: 2
   ```

6. **Version** — `--version`:
   ```
   $ python -m deportation_foia_normalizer --version
   deportation-foia-normalizer 1.0.0
   ```

## Acceptance criteria

Each criterion is bound to exactly one command/flag; every element of the Command Surface is
exercised by at least one criterion.

- **[`INPUT`]** Given `examples/sample.csv` (a representative raw dump), the tool produces a clean
  table whose header is exactly the canonical columns in order and whose `event_date` values are all
  ISO-8601 `YYYY-MM-DD`.
- **[`--output`]** `-o PATH` writes the clean table to `PATH` (and nowhere else); omitting it writes
  to `<INPUT-stem>.normalized.csv`.
- **[`--format`]** `--format sqlite` produces a SQLite file with a `records` table carrying the
  canonical columns; `--format csv` (default) produces the CSV described above.
- **[`--rejects`]** Rows failing validation are written to the rejects file at the given (or default)
  path, each with `__source_row` and a non-empty `__reject_reason`, and none are silently dropped.
- **[`--report`]** The stdout summary reports `rows ingested`, `rows normalized`, `rows coerced`, and
  `rows rejected` with `ingested == normalized + rejected`; `--report json` emits the documented
  object with those same counts.
- **[`--schema`]** With no `--schema`, two inputs whose differing source headers both alias the same
  canonical field (e.g. `Event Date` and `Apprehension Date` → `event_date`) both normalize to that
  one canonical column; passing `--schema PATH` substitutes the supplied mapping for the bundled one.
- **[`--strict`]** When at least one row requires coercion, `--strict` causes exit code 3 (and exit 0
  without it).
- **[required-mapping guard]** When a required canonical column (`event_type` or `event_date`) cannot
  be mapped, the tool exits 2 and the error message names the missing canonical column.
- **[`--version`]** `--version` prints the version string and exits 0.
- **[`-h/--help`]** `--help` prints usage covering the command surface and exits 0.

## Coherence requirements (your design is REJECTED unless all hold)

(1) exactly one tool / one contract
(2) every criterion exercises THIS contract
(3) the default invocation demonstrates the headline
(4) NO second/competing contract or mode hiding

## Problem

The Deportation Data Project publishes raw ICE FOIA dumps (arrests, detainers, removals through
March 2026) as inconsistently-formatted CSV/XLSX files. Column names drift between releases, dates
arrive in mixed formats, coded fields are undocumented, and individual rows are silently malformed.
There is no shared, repeatable normalizer, so every newsroom and advocacy group re-implements the
same brittle hand-cleanup each release — burning hours and risking divergent, miscounted published
figures drawn from the same source data. This hurts the journalists and advocates who rely on these
dumps as the primary public evidence base for enforcement activity, and by extension the public that
reads counts which disagree only because the cleanup was done differently.

## Goals / Non-goals

**Goals**

- Map drifting source column names to one documented canonical schema via a configurable alias map.
- Normalize mixed-format dates to ISO-8601 and known coded fields (event type, gender) to fixed enums.
- Validate every row; route failures to a rejects file with a per-row reason; never silently drop.
- Emit a deterministic clean table (CSV or SQLite) plus a summary of ingested/normalized/coerced/
  rejected counts.
- Fail loudly (non-zero, named) when a required canonical column cannot be mapped.

**Non-goals**

- Parquet output (CSV + SQLite only for the MVP; Parquet deferred to avoid a heavy dependency).
- Downloading, scraping, or fetching dumps from any network source — input is a local file only.
- Merging/deduplicating across multiple dumps, or any cross-file joins (one input file per run).
- Statistical analysis, charts, dashboards, or interpretation of the data.
- Fuzzy/ML column inference — mapping is an explicit, auditable alias table, not a guesser.
- Persistent databases, servers, accounts, or any stateful service.

## Hermetic build constraints

- **Language/toolchain:** Python (3.11+), packaged with `pyproject.toml`; lint via `ruff`, tests via
  `pytest`. Dependencies are permissive-licensed only (CSV/SQLite via the standard library; `openpyxl`
  (MIT) for XLSX input; a small YAML reader for `--schema`). No paid services, no secrets, no network
  access at build or test time; all fixtures ship in-repo.
- **License + docs:** ships an OSI license (MIT) and a README documenting the canonical schema, the
  alias map, and the command surface.
- **Makefile contract:** the repo's `Makefile` honors the canonical targets — `make check` (lint +
  test), `make test` (the pytest suite), `make build` (`pip install -e .[dev]`), and `make run`.
- **`make run`** invokes the real entrypoint on a bundled fixture and produces real output:
  `python -m deportation_foia_normalizer examples/sample.csv`. The fixture `examples/sample.csv`
  ships in the repo — a small raw dump (~12 rows) with drifting headers (e.g. `Event Date`,
  `Apprehension AOR`, `Citizenship`, `Sex`), mixed date formats, coded gender/event values, and a
  couple of malformed rows — so `make run` writes a real normalized table and rejects file and prints
  the populated summary (not `--help`).

## Test expectations

Every acceptance criterion is covered by at least one test below.

**Unit**

- Date normalizer: `MM/DD/YYYY`, `YYYY-MM-DD`, `M/D/YY`, and `Mon D, YYYY` → ISO `YYYY-MM-DD`;
  `"32/13/2026"` and empty → flagged unparseable.
- Code normalizers: gender `1`/`Male`/`F`/blank → `M`/`M`/`F`/`U`; event-type `ARR`/`removal` →
  `arrest`/`removal`; out-of-enum value → invalid.
- Alias resolution: differing source headers (`Event Date`, `Apprehension Date`) both resolve to
  `event_date`; required-column-absent raises the named-mapping error.
- Schema loader: a valid `--schema` YAML/JSON overrides the bundled map; a malformed schema errors.

**Integration**

- Full run on `examples/sample.csv`: clean CSV has canonical header in order with ISO dates;
  rejects CSV holds the malformed rows with `__source_row` + `__reject_reason`; summary counts satisfy
  `ingested == normalized + rejected`.
- `--format sqlite` writes a `records` table with the canonical columns and the same rows as the CSV.
- `--report json` emits the documented object with counts matching the text report.
- `-o`/`--rejects` honor explicit paths; defaults derive from the input stem.

**End-to-end (process-level, asserting exit codes and stdout)**

- Default invocation exits 0 and prints the text summary.
- Input missing a required canonical column exits 2 with the missing column named in stderr.
- `--strict` on an input requiring coercion exits 3; the same input without `--strict` exits 0.
- `--version` prints the version and exits 0; `--help` prints usage and exits 0.
