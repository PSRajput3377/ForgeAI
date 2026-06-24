# Contributing

Conventions we follow from day one — even on the MVP, the code should be
interview-grade.

## Branches

- `main` — stable, always working.
- `develop` — integration branch.
- `feature/*` — one feature per branch, branched from `develop`.

## Commit messages

Conventional Commits:

| Prefix      | Use for                          |
|-------------|----------------------------------|
| `feat:`     | a new feature                    |
| `fix:`      | a bug fix                        |
| `docs:`     | documentation only               |
| `refactor:` | code change, no behavior change  |
| `test:`     | adding/adjusting tests           |
| `chore:`    | tooling, deps, scaffolding       |

Keep commits small and meaningful — one logical change each.

## Coding standards

### Backend (Python 3.12)
- **Black** (line length 100) + **Ruff** for formatting & linting.
- Type hints on all public functions.
- Docstrings on modules and public functions.
- Run: `make api-fmt`.

### Frontend (TypeScript)
- **ESLint** (`next/core-web-vitals`) + **Prettier**.
- **Strict** TypeScript (`strict: true`).
- Run: `npm run lint` / `npm run format` in `apps/web`.

## Definition of done

A change is done when its **code and its docs** are committed, formatters/linters
pass, and (where applicable) tests pass. See the engineering principles in
[`00-product-design/07-principles.md`](00-product-design/07-principles.md).
