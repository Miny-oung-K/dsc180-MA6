---
name: seed-fault
description: Reproduce one bikeshare pipeline fault, capture the hook failure, and verify the repair.
---

Reproduce this single fault from Exercise 2: $ARGUMENTS.

1. Open a disposable copy that contains the current source, tests, and
   shared hook configuration. Keep the original checkout and CSV intact.
2. Run the test that should catch the fault. Once it passes, use Claude Code
   Edit to apply the smallest source change that introduces the fault.
3. Record the exact diff, failing pytest output, and live PostToolUse stderr
   and exit code. If the hook stays green, report the gap in coverage.
4. Ask for the repair. Record both the number of user repair prompts and the
   number of model turns if Claude Code reports it. Verify that the source
   matches the original and run the full suite again.
5. Add the evidence to `docs/SEEDED_FAULTS.md`. For the Bash CSV-copy case,
   use a temporary copy of the CSV, record the schema test and explain why
   the Edit/Write hook did not fire.
