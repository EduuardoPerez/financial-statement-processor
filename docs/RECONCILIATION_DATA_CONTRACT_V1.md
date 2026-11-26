# Reconciliation data contract v1

This document specifies the processor's structured output for reconciliation
([issue #9](https://github.com/EduuardoPerez/financial-statement-processor/issues/9)).
The `export` command implements the source observation and manifest package;
the existing Excel commands remain available. Examples under
[`docs/examples/reconciliation-v1/`](examples/reconciliation-v1/) are synthetic.

## Export command

Run `PYTHONPATH=src uv run python -m cli.main export declaration.json --output-dir output/reconciliation-v1`.
The declaration is UTF-8 JSON. File paths are relative to the declaration file.
For example:

```json
{
  "schema_version": "1.0",
  "files": [
    {
      "path": "statement.pdf",
      "system": "bbva_mastercard",
      "expected_coverage": [
        {"kind": "statement_cycle", "start": "2026-06-01", "end": "2026-06-30"}
      ]
    },
    {
      "path": "activity.csv",
      "system": "bbva_visa",
      "expected_coverage": [
        {"kind": "transaction_dates", "start": "2026-07-01", "end": "2026-07-31"}
      ],
      "confirmed_export_range": {"start": "2026-07-01", "end": "2026-07-31"}
    }
  ]
}
```

Declare every expected input, including files that may be missing. The optional
`confirmed_export_range` applies only to tabular exports and must come from an
independently confirmed export request. The exporter never treats first and last
transaction dates as proof of coverage. A missing or unreadable file, discarded
transaction row, unverified Mastercard close cycle, or unmet expected interval
makes the batch incomplete. An export without confirmed tabular coverage records
a warning; when no interval was required, its rows may still be complete relative
to the declaration. The command refuses to overwrite an existing package.

## Package and version

A batch is a directory containing `manifest.json` and `movements.jsonl`, encoded
as UTF-8. JSONL has one source observation per nonempty line. No line represents
a deduplicated purchase, a reconciliation decision, or a Sheets row. A consumer
must reject an unsupported `schema_version` rather than guessing field meanings.
Version `1.0` fixes the required fields and meanings below. Producers may add
fields within v1; consumers must ignore unknown fields but preserve the original
record if they store it. A change to identity, amount, or completeness semantics
requires a new major version.

For example, a v1.1 producer may add `parsed.merchant_hint` to an otherwise
valid v1 record. A v1 reader ignores that field and still uses the original
`raw.description` and required `parsed.description`. A proposed v2 record that
changes the meaning of `parsed.amount` from source sign to accounting direction
is incompatible: a v1 reader rejects `"schema_version": "2.0"` rather than
silently treating the new sign as a source observation. The manifest and every
line must declare the same supported major version; a reader rejects a mixed
batch. Minor versions may add optional fields but cannot remove required fields
or redefine them.

The manifest names the JSONL file, its SHA-256 digest and record count. The
producer writes the JSONL first, then publishes the manifest only after closing
and hashing it. Consumers verify the digest and count before accepting the batch.
An interrupted write without a valid manifest is incomplete.

## Movement record

Every line is a JSON object with these required fields. `null` means unknown;
an empty string must not stand in for unknown data.

| Field | Type and meaning |
| --- | --- |
| `schema_version` | String `"1.0"` for this package. Consumers supporting v1 accept compatible `1.x` minor versions. |
| `observation_id` | Opaque, stable identifier of this exact source-file record. The same file bytes and locator produce the same ID across runs; a different export of the same movement gets a different ID. |
| `source` | Object with `system`, `record_type`, `file_id`, `locator`, and optional `account_mask`. `file_id` references a manifest entry. `locator` is a stable row/page/record coordinate within that file, including a suffix if a page has repeated row labels. `account_mask` is masked, never a full account or card number. |
| `native_ids` | Object of exact identifier names and string values supplied by the source, such as `Número de Movimiento`, `Operación Relacionada`, `SOURCE_ID`, or `receipt_operation`. Missing identifiers are omitted. These strings must not be coerced to numbers. |
| `source_identity` | Object with `status` (`confirmed` or `unconfirmed`), `key` (string or null), and `basis` (array of field names). A confirmed key identifies one underlying *source movement* across overlapping exports within a source namespace; it does not assert a cross-source match. For unconfirmed identity, `key` is null and `basis` is empty. |
| `raw` | Object with `date`, `amount`, `currency`, and `description` as exact source text, plus optional source-specific text fields. Preserve the sign and formatting of `amount` and every original date. |
| `parsed` | Object with `amount` as a signed decimal string, `currency` as an ISO 4217 code or null, `dates` as an array of `{role, value}` where `value` is an ISO date/datetime string, and `description` as parsed text. A missing or unverified date role is omitted. |
| `references` | Object of available exact source values such as `voucher`, `purchase_date`, `statement_close`, `installment_number`, and `installment_total`; absent values are omitted. Numbers in references remain strings if the source presents them as text. |
| `diagnostics` | Array of `{code, message}` for row-level interpretation warnings. Empty when none. The source row remains present even when its meaning is uncertain. |

`raw.amount` is source evidence; `parsed.amount` changes only decimal notation,
not direction. Use a base-10 decimal string, optionally prefixed by `-`, with a
period as decimal separator, no grouping separators, no exponent, and no binary
float conversion. Preserve meaningful source precision, including trailing
zeros. Do not silently map a positive Activity display amount to a negative
expense: a receipt can establish payment direction while the Activity sign
remains positive. The eventual accounting interpretation belongs to review.
Dates have explicit roles such as `posted`, `purchase`, and `statement_close`.
Do not interpret an unverified timestamp suffix or substitute posting date for
purchase date. A source-specific time zone can be retained in `raw` until its
meaning is established.

The producer assigns `observation_id` deterministically from a source-system
namespace, the source file's SHA-256 digest, and its locator. The encoding and
hash algorithm for the final opaque ID are implementation details; equality
across runs is required. `file_id` identifies one byte-exact input, and its
manifest entry carries the digest. The source path is for audit only and is not
part of deduplication. Replacing a file with changed bytes changes its file ID
and observation IDs, so consumers must recheck prior decisions.

`source_identity.key` has a source-specific namespace and must be based on
native identifiers whose uniqueness has been established for that movement
type, including an account namespace where identifiers can be reused between
accounts. For a Mercado Pago balance row, `Número de Movimiento` can identify the
same row in overlapping exports. `Operación Relacionada` links different rows
of an operation and cannot by itself identify one movement. For a card charge,
the key must distinguish installments; a voucher, date, and amount alone may
still be shared by different installments. If uniqueness is not established,
use `unconfirmed`, even when a plausible composite key could be fabricated.
The consumer may group confirmed equal keys as repeat observations but retains
both records and provenance. Equal dates and absolute amounts, including the
current Excel `DUPLICATED:` label, are only candidate signals.

## Separate identities and review boundary

The consumer creates a reconciliation `link_id` for a proposed relationship
between observation or source-movement identities. It records the participating
IDs, evidence, alternatives, and a state of `pending`, `confirmed`, or
`distinct`. Candidate evidence never changes an observation or its source
identity. A source-side `Operación Relacionada` may explain a balance pair
without proving that the pair equals a bank charge or a purchase. A refund or
adjustment is its own movement, linked to another movement when evidenced.
The consumer models a purchase separately from its funding and from each
installment charge. A balance inflow and payment pair can be related within
Mercado Pago; neither row alone becomes a purchase. A receipt may support a
purchase even when Activity displays an unexpected sign. The purchase-to-card
charge relationship remains a candidate until its specific installment and
bank evidence are established.
The `link_id` is stable for a relationship type and the sorted participant
identities: use confirmed source keys where available and observation IDs
otherwise. If identity or relevant evidence changes, the consumer must
re-evaluate a previous decision rather than silently carrying it forward.

An eventual `import_row_id` belongs to the reviewed accounting charge and the
target sheet, including its installment identity. It is not an observation ID
or a `link_id`. It is allocated only after the accounting and historical-row
policy is settled and must remain stable across re-exports and retries. It must
not be derived from a sheet row number or date/amount alone. Multiple source
observations may support one import row;
separate installments need separate import rows even if a statement repeats the
date, voucher, and amount. The storage and revision of review decisions belong
to [issue #18](https://github.com/EduuardoPerez/financial-statement-processor/issues/18).
This v1 package does not serialize decisions or import rows.

For a reviewed installment, the downstream budget date of installment 1 is
the purchase date. For installment *n* ≥ 2, it is day 1 of the purchase month
shifted by *n*−1 calendar months, including year changes. The actual statement
close remains a separate date for each charge. A missing or unverified purchase
date cannot be replaced with the statement date to calculate the budget date.
These are consumer rules; the source package carries the evidence needed to
apply them and never rewrites the source dates.

| Source observation | Source identity | Reconciliation link | Import row |
| --- | --- | --- | --- |
| One file record, always retained | Same native movement across exports only when proven | Cross-source relationship with evidence and review state | One reviewed accounting charge in a specific destination |

## Manifest and completeness

The required manifest fields are:

| Field | Type and meaning |
| --- | --- |
| `schema_version` | String `"1.0"` for this package; it must match every movement line. |
| `batch_id` | Stable identifier for this declared input set and configuration. A changed input or scope creates a new batch ID. |
| `generated_at` | ISO 8601 timestamp with offset for the export attempt. |
| `movements` | `{path, sha256, record_count}` for the JSONL file. Path is relative to the batch directory. |
| `expected_files` | Array of every file declared for the batch, including missing files. Each has `file_id`, relative `path`, `system`, `expected_coverage`, `status`, `observed_coverage`, `rows_read`, `rows_emitted`, `rows_discarded`, `errors`, and `warnings`. `sha256` is required for a readable file and null otherwise. |
| `complete` | Boolean computed from the rules below, never asserted from a successful process exit alone. |

Coverage entries have `kind` (for example `transaction_dates` or
`statement_cycle`), `start`, and `end` inclusive as ISO dates. An empty array
means no coverage was established; it is not equivalent to full coverage.
`status` is `complete`, `partial`, `missing`, or `unreadable`. Each error or
warning is `{code, message}` and may include `locator`. A discarded source row
must increment `rows_discarded` and carry a warning or error with its locator
and reason; a row excluded by a known nontransaction header/footer rule must
still be accounted for consistently in the parser's documented row count.
The movement count equals the sum of `rows_emitted` for the files in this
manifest. A consumer rejects references to undeclared file IDs.

`complete` is true only when every expected file is `complete`, every declared
coverage interval is met by verified observed coverage, no required source row
failed extraction, and the JSONL digest/count checks pass. A missing, unreadable,
or partial file forces `complete: false`. A warning about uncertain *meaning*
may coexist with a complete extraction; the affected reconciliation link stays
pending. A consumer may inspect records from an incomplete batch, but cannot
claim full coverage, infer absence of a counterpart, or automatically import a
case that depends on the missing evidence. An undeclared expected period cannot
be inferred as complete. The caller must declare the intended files and periods
before processing; the processor cannot discover missing statements from an
input directory alone.

## Synthetic review cases

The [example manifest](examples/reconciliation-v1/manifest.json) intentionally
declares a missing card statement and therefore an incomplete batch. The
[JSONL example](examples/reconciliation-v1/movements.jsonl) illustrates:

1. Two balance exports with the same confirmed native movement key. Their
   observation IDs and file provenance differ; a consumer can prove a repeat.
2. Two card installments with the same visible date, voucher, and amount. Both
   identities remain unconfirmed and both observations remain separate.
3. A balance payment and a card charge with equal dates and amounts but no
   shared native identity. Their cross-source link remains pending.
4. A positive Activity entry whose receipt says it was a card payment. The
   positive source amount remains positive; the diagnostic preserves the
   conflict for review.
5. A missing expected card file. The manifest marks the batch incomplete even
   though the readable files were exported successfully.

These examples are contract illustrations, not executable exports. Their short
IDs and placeholder SHA-256 values are synthetic. Real exporters calculate
digests and deterministic IDs from actual bytes.
