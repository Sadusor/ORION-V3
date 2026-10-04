# V3-RUN-054 — canonical Workspace Registry foundation staged

Date: 2026-10-04

## Why this is isolated

After RUN-053R, ordinary read-only usage examples will move to a batched Usage
Scenario Suite.

The Workspace Registry is different: it is a new authority surface.

Therefore its foundation is proven once in an isolated deterministic gate before
the suite depends on it.

## Architecture

Cross-project scope is split into independent concepts:

- trust class;
- access policy;
- authorization lifetime.

Registry trust classes initially:
- `owner_project`
- `donor_repo`
- `shared_or_client`

Archive state:
- active
- archived

Read policy:
- allowed
- blocked

Write policy:
- deny
- owner_approval

Additional policy metadata:
- `no_cloud`
- `license_state`
- repo identity
- revision
- logical project ID/name

The absolute trusted root exists only in local canonical registry state.

## Owner-only mutation

Project registration/update:
owner-only.

Project-group creation/membership changes:
owner-only.

Local/cloud models cannot:
- register projects;
- change trusted roots;
- change group membership;
- change trust class/policy.

## Versioning / integrity

Every project mutation creates an immutable project revision with:
- monotonically increasing version;
- owner identity;
- previous revision ID;
- canonical record JSON;
- SHA256.

Every group mutation creates the same style of immutable revision.

Current registry rows are checked against:
1. their own content hash;
2. the corresponding immutable revision.

Direct DB modification of:
- trusted root;
- group membership

must fail closed during scope resolution with:
`registry_integrity_failure`.

## Semantic scope resolver

Initial deterministic tokens:
- `active_project`
- `project:<id>`
- `registered_projects`
- `donor_repos`
- `archived_projects`
- `project_group:<id>`

`registered_projects` initially means readable active:
- owner projects;
- shared/client projects.

Donor repos are intentionally separate.

Archived projects are default-excluded and require explicit archived scope.

## Scope cap

ORION enforces a maximum project-count cap.

A semantic token resolving to more projects than the current cap fails closed.

This prevents a small phrase such as "my projects" from silently producing an
unbounded blast radius.

## Model-safe scope packet

The model may receive:
- logical project ID;
- human project name;
- repo identity;
- trust class;
- archive state;
- no-cloud marker;
- license state;
- revision;
- registry version/hash.

The model never receives:
- trusted absolute root.

## Frozen resolution

A ScopeResolution contains exact project registry versions/hashes.

If the owner later changes a project entry:
- the old resolution object remains unchanged;
- a new resolution receives a new resolution ID and new project version/hash.

This is the basis for freezing cross-project read leases in the next slice.

RUN-054 does not yet claim in-flight lease invalidation after registry change;
that remains an isolated later authority test.

## Physical fixture

Create five registry entries:
1. active owner project
2. second owner project
3. shared/client project with `no_cloud=true`
4. donor repo with Apache-2.0 metadata
5. archived owner project

Create owner group:
`work`

Prove:
- owner-only project mutation;
- owner-only group mutation;
- semantic scope separation;
- archived default exclusion;
- donor license metadata;
- no-cloud metadata;
- scope project cap;
- trusted-root secrecy;
- frozen resolution stability;
- new resolution changes after registry revision;
- direct root tamper blocked;
- direct group membership tamper blocked.

## Gate mode

- zero model
- zero network
- zero provider API
- zero filesystem Hand

## PASS meaning

PASS proves the Project/Workspace Registry is a canonical, versioned,
checksummed, owner-controlled source for semantic cross-project scope.

After this gate, ordinary cross-project read scenarios can move into the batched
Usage Scenario Suite rather than one RUN per example.
