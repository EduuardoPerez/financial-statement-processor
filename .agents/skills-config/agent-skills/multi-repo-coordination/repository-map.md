# Repository coordination map

This map covers the planned statement reconciliation workflow. Consult each repository for its current interfaces and checks.

| Repository | Responsibility | State |
| --- | --- | --- |
| financial-statement-processor | Parse and validate source statements, preserve provenance, and produce versioned structured transactions alongside the existing Excel output. | Existing |
| financial-statement-sheets-sync | Normalize and reconcile transactions, store review decisions, and prepare and apply reviewed imports. | Planned |
| financial-statement-orchestrator | Run local steps, pass configuration and paths, record progress, and resume batches. | Planned |

## Interfaces

- Processor to synchronizer. A versioned structured transaction output with a batch summary. The contract is being defined in [issue #9](https://github.com/EduuardoPerez/financial-statement-processor/issues/9). Verify compatibility by feeding processor-generated output to the synchronizer once both exist.
- Synchronizer to orchestrator. Local commands and results for preparation, review, preview, import, and resumption. The interface is pending. Verify command sequencing with synthetic results first, then against the synchronizer.
- Synchronizer to Google Sheets. A reviewed import preview and an approved write. Mapping and test-copy validation are tracked in [issues #16–#19](https://github.com/EduuardoPerez/financial-statement-processor/issues/16).

Issues may be hosted temporarily in the processor repository until the owning repositories exist. Check the current repository and linked issues before changing an interface.
