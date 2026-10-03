# Failure lesson — authoring syntax must be mechanically preflighted

Date: 2026-10-03

Canonical lesson ID:
`FAILURE_LESSON-AUTHORING-SYNTAX-001`

Status:
**PROMOTED TO EXECUTABLE REGRESSION RULE**

## Evidence

V3-RUN-020 first physical attempt did not reach the execution-envelope test.

Remote staging SHA:
`d97373e49156a4fda941c248b2d13c51cc038895`

Named-task session:
`1738e15e6d7f`

Result:
`FAIL`

Observed regression collection:
- two pytest collection errors;
- root cause: literal escaped `\\n` sequences were authored into the
  `orion_v3.state` import block in `coding_factory/blackboard.py`;
- architecture under test: **NOT REACHED**.

This is the same general failure class as earlier generated-source escaping /
syntax mistakes: generated text looked structurally plausible but had not passed
a deterministic language parser before physical execution.

## Promoted rule

Do not rely on model recollection or reviewer attention.

Every V3 physical regression gate must run a self-contained authoring preflight
before pytest/probe execution.

The current mandatory repo preflight validates tracked:
- Python through Python `compile(..., "exec")`;
- JSON through the standard JSON parser;
- PowerShell through `System.Management.Automation.Language.Parser` before the regression suite.

Coding Factory execution additionally preflights actual changed Python/JSON
files after mechanical application and actual Git-path scope validation, before
evidence may be accepted or an Attempt may succeed.

A syntax failure is classified:
```text
failure_class: AUTHORING_SYNTAX_ERROR
architecture_gate_state: NOT_REACHED
```

## Why this is learning

The prior failure is no longer only a log or a remembered conversation.
It changed future ORION behavior:
- the failure has a stable lesson identity;
- the rule is documented for every contributor/model;
- the rule is executable;
- the exact escaped-newline case has a regression test;
- malformed generated source is rejected by the Coding Factory before success.

This is the intended ORION learning pattern:
`evidence -> classified lesson -> explicit promotion -> deterministic guard -> regression replay`.


## Physical replay evidence

V3-RUN-020 attempt 2 physically proved the promoted guard itself.

Remote staging SHA:
`7dee2b31ff31413a52221fb945b4911ce827533e`

Session:
`8a1ee466c6cb`

Observed:
```text
AUTHORING_PREFLIGHT> START
AUTHORING_PREFLIGHT_FILES> 60
AUTHORING_PREFLIGHT_DETAIL> src/orion_v3/coding_factory/blackboard.py: python_syntax_error line=6 unexpected character after line continuation character
AUTHORING_FAILURE_CLASS> AUTHORING_SYNTAX_ERROR
ARCHITECTURE_GATE_STATE> NOT_REACHED
AUTHORING_PREFLIGHT> FAIL
STATUS> FAIL
```

Meaning:
the lesson is no longer merely coded/documented. The physical Remote path
actually stopped the repeated malformed-source failure before pytest and before
the RUN-020 architecture under test was entered.

The underlying file was then repaired by replacing the seven literal escaped
newline byte sequences in the import block with real newline characters.
