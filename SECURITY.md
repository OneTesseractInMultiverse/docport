# Security Policy

Use this document for vulnerability handling and secure implementation rules.

## Supported versions

| docport version | Python versions | Supported   |
|----------------------|-----------------|-------------|
| `1.x` latest         | `>=3.12`        | Active      |
| Older releases       | Superseded      | Unsupported |

Security fixes belong on the latest supported `docport` release.
Any approved dependency risk exception should be recorded
in [docs/dependency-risk-exceptions.md](docs/dependency-risk-exceptions.md).

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability.
Report it privately through GitHub's security advisory flow for this repository.

Include a short issue summary, steps to reproduce, expected impact, and any known short-term mitigation.

## Secure coding rules

`docport` sits on a persistence boundary.
Small design choices here can spread into many services, so changes should preserve these rules:

- keep validation in Pydantic entity classes and projection models
- keep `_id` inside the adapter boundary, except when a projection model asks for it on purpose
- keep driver objects out of domain code and service-facing contracts
- keep optimistic concurrency checks active for entity replacement writes
- keep secrets, credentials, tokens, and live database values out of code, docs, tests, and logs
- keep partial reads separate from entity hydration

## Verification

Before merge, run:

```bash
make check
```
