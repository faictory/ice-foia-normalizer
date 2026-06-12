# deportation-foia-normalizer

A command-line tool to normalize raw ICE FOIA dumps (CSV/XLSX files) into a clean, canonical-schema table with standardized column names, normalized dates, and per-row validation reports.

## Quick Start

```bash
python -m deportation_foia_normalizer <INPUT> [flags]
# or
deportation-foia-normalizer <INPUT> [flags]
```

## Command Surface

The tool exposes one command: normalize a single raw FOIA file.

### Required Argument

| Element | Takes | What it does |
| --- | --- | --- |
| `INPUT` | path to a `.csv` or `.xlsx` file | The raw FOIA file to normalize. Format is detected by file extension. |

### Flags

| Flag | Takes | Default | What it does |
| --- | --- | --- | --- |
| `-o, --output` | path | `<INPUT-stem>.normalized.csv` (or `.sqlite` with `--format sqlite`) | Destination for the clean canonical table. |
| `--format` | `csv` \| `sqlite` | `csv` | Output format. `sqlite` writes a single table named `records`. |
| `--rejects` | path | `<INPUT-stem>.rejects.csv` | Destination for rows that failed validation, each annotated with a reason. |
| `--report` | `text` \| `json` | `text` | Format of the summary report printed to stdout. |
| `--schema` | path | (bundled default) | Path to a custom mapping config (YAML or JSON) that replaces the bundled schema. |
| `--strict` | — | (disabled) | Treat any value coercion as a failure; exit code 3 if any row required coercion. Rows are still written. |
| `--version` | — | — | Print the tool version and exit 0. |
| `-h, --help` | — | — | Print usage and exit 0. |

## Output Schema

The tool produces a clean canonical table with these seven columns, in this fixed order:

| Column | Type | Normalization |
| --- | --- | --- |
| `record_id` | string | Carried through from input; synthesized from source row number if absent. |
| `event_type` | enum | One of `arrest`, `detainer`, `removal`. Lower-cased and code-mapped (e.g., `ARR`→`arrest`). **Required.** |
| `event_date` | date | ISO-8601 `YYYY-MM-DD` format. Parsed from mixed source formats (e.g., `MM/DD/YYYY`, `YYYY-MM-DD`, `M/D/YY`, `Mon D, YYYY`). **Required.** |
| `field_office` | string | Trimmed whitespace; mapped from `Apprehension AOR`, `AOR`, or similar aliases. |
| `nationality` | string | Trimmed country name or code, upper-cased. |
| `removal_country` | string | Trimmed; blank when not applicable. |
| `gender` | enum | One of `M`, `F`, `U`. Code-mapped: `1`/`Male`→`M`, `2`/`Female`→`F`, blank→`U`. |

**Required columns:** `event_type` and `event_date` must be present in the input (under any alias) or the run exits with code 2.

## Alias Map

The bundled default schema maps these source column names to their canonical equivalents:

```
Canonical Column     Source Headers (any of these)
─────────────────────────────────────────────────
event_date           Event Date, Apprehension Date
field_office         Apprehension AOR, AOR
nationality          Citizenship, Country
gender               Sex
event_type           Event Type
record_id            Record ID, ID
removal_country      Removal Country
```

Any source column matching one of the aliases above is mapped to its canonical column. Unrecognized columns are ignored. Use `--schema <PATH>` to supply a custom alias map.

## Output Artifacts

The tool produces up to three files and a stdout report:

### 1. Clean Canonical Table (`--output`)

A table (CSV or SQLite based on `--format`) containing only the seven canonical columns in order, with one header row followed by normalized data rows.

**CSV format:** UTF-8, comma-separated, `\n` line endings, rows in input order.  
**SQLite format:** One table named `records` with columns as `TEXT` type, same row order.

### 2. Rejects File (`--rejects`)

A CSV file containing every **original** input column (in input order) plus two appended columns:

- `__source_row`: 1-based row number in the original input
- `__reject_reason`: Human-readable reason for rejection (e.g., `unparseable event_date: "32/13/2026"` or `event_type not in {arrest,detainer,removal}: "xyz"`)

Every row appears in exactly one artifact (clean table or rejects file) — none are silently dropped.

### 3. Summary Report (stdout)

Printed to stdout; format controlled by `--report` flag.

**`text` format (default):**
```
deportation-foia-normalizer 1.0.0
input:           <INPUT>
output:          <OUTPUT> (csv|sqlite)
rejects:         <REJECTS>
rows ingested:   <N>
rows normalized: <N>
rows coerced:    <N>
rows rejected:   <N>
column mappings:
  <source-header> -> <canonical-column>
  ...
reject reasons:
  <reason>: <count>
  ...
exit: <code>
```

**`json` format:**
A single JSON object with keys: `version`, `input`, `output`, `format`, `rejects`, `rows_ingested`, `rows_normalized`, `rows_coerced`, `rows_rejected`, `column_mappings` (object), `reject_reasons` (object), `exit_code`.

**Invariants:**
- `rows_ingested == rows_normalized + rows_rejected`
- `rows_coerced <= rows_normalized`

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | Success. Rows may have been rejected; this is not a failure. |
| `1` | Unexpected error: missing or unreadable input file, unparseable file format, or invalid `--schema`. |
| `2` | A **required** canonical column (`event_type` or `event_date`) could not be mapped from the input. The error names the missing column. |
| `3` | `--strict` was set and at least one row required coercion. All rows are still written; only the exit code changes. |

## Examples

**Basic usage (CSV output beside the input):**
```bash
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

**SQLite output to a chosen path:**
```bash
python -m deportation_foia_normalizer examples/sample.csv --format sqlite -o out/records.sqlite
```

**Machine-readable JSON report:**
```bash
python -m deportation_foia_normalizer examples/sample.csv --report json
```

**Strict mode (fail if any coercion occurs):**
```bash
python -m deportation_foia_normalizer examples/sample.csv --strict
```

**Custom alias map:**
```bash
python -m deportation_foia_normalizer 2026q1.csv --schema configs/q1-mapping.yaml
```

## Make Targets

| Target | What it does |
| --- | --- |
| `make build` | Install the package in development mode (`pip install -e .[dev]`) |
| `make lint` | Run code linting with ruff |
| `make test` | Run the test suite with pytest |
| `make check` | Run lint and test (quality gate for CI) |
| `make run` | Smoke-test the tool on the bundled example (`examples/sample.csv`) |

## Design and Schema

See [DESIGN.md](DESIGN.md) for the full design document, including problem statement, goals, non-goals, test expectations, and design rationale.
