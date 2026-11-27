# Repository coordination map

This map covers the planned statement reconciliation workflow. Consult each repository for its current interfaces and checks.

| Repository | Responsibility | State |
| --- | --- | --- |
| financial-statement-processor | Parse and validate source statements, preserve provenance, and produce versioned structured transactions alongside the existing Excel output. | Existing |
| [financial-statement-sheets-sync](https://github.com/EduuardoPerez/financial-statement-sheets-sync) | Normalize and reconcile transactions, store review decisions, and prepare and apply reviewed imports. | Existing |
| financial-statement-orchestrator | Run local steps, pass configuration and paths, record progress, and resume batches. | Planned |

## Interfaces

- Processor to synchronizer. The producer owns the [v1.0 JSONL and manifest contract](../../../../docs/RECONCILIATION_DATA_CONTRACT_V1.md). Verify compatibility with synthetic examples and processor-generated output.
- Synchronizer to orchestrator. Local commands and results for preparation, review, preview, import, and resumption. The interface is pending. Verify command sequencing with synthetic results first, then against the synchronizer.
- Synchronizer to Google Sheets. A reviewed import preview and an approved write. Mapping and test-copy validation are tracked in [issues #16–#19](https://github.com/EduuardoPerez/financial-statement-processor/issues/16).

Check the Project for current issue ownership and linked handoffs before changing an interface. The orchestrator repository is still planned.
