# Next session prompt

Use the complete canonical prompt from:

```text
docs/CONTINUATION_PROMPT.md
```

The file is intentionally the single source of truth for starting the next chat. Do not duplicate or partially copy older prompt text from PR descriptions or historical comments.

Mandatory first action in the next chat:

```text
read AGENTS.md
-> read docs/PROJECT_STATE.md
-> read docs/CONTINUATION_PROMPT.md
-> query live local/GitHub state
-> perform repository audit before functional development
```

Verified implementation checkpoint before handoff documentation:

```text
66fd5ed89520070a7d48392f41fbfb7cb352b0f7
Verify repository run #598: success
trigger mode: workflow_dispatch
```

The live branch HEAD after handoff documentation must be queried rather than copied from this file.
