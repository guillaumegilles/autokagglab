<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->

---

# Copilot Instructions

> **Replace this section** with conventions specific to your project.
> The headings below are a starting point — remove or adapt them freely.

## Project Overview

<!-- Describe what this project does in 2–3 sentences. -->
[YOUR PROJECT NAME] is a [type of project] that [solves X problem] for [target users].

## Tech Stack

<!-- List the core technologies so Copilot knows which idioms to use. -->
- **Language**: [e.g. TypeScript 5, Python 3.12, Go 1.22]
- **Framework**: [e.g. Next.js 14, FastAPI, Gin]
- **Database**: [e.g. PostgreSQL via Prisma, SQLite]
- **Testing**: [e.g. Vitest, pytest, Go test]
- **Linter / Formatter**: [e.g. ESLint + Prettier, Ruff, gofmt]

## Project Structure

```
[YOUR-REPO-NAME]/
├── src/          # Application source code
├── tests/        # Test files (mirror src/ structure)
├── docs/         # Documentation
└── ...
```

## Code Conventions

### General
- Prefer clarity over cleverness — write code that is easy to read and review.
- Keep functions small and focused on a single responsibility.
- Avoid premature optimisation; profile before optimising.

### Naming
- Use descriptive names; avoid single-letter variables outside of loop counters.
- [Language-specific convention, e.g. camelCase for JS/TS, snake_case for Python]

### Comments
- Only comment code that needs clarification — avoid restating what the code does.
- Use `TODO:` and `FIXME:` prefixes for inline notes.

### Error Handling
- Always handle errors explicitly; never silently swallow exceptions.
- Surface meaningful error messages to the caller.

### Testing
- Write tests alongside new features; target meaningful coverage, not 100%.
- Follow Arrange / Act / Assert structure in test bodies.

## Commit & Branch Conventions

Follow **Conventional Commits**: `<type>(<scope>): <subject>`

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change with no behaviour change |
| `test` | Adding or updating tests |
| `chore` / `ci` | Build, tooling, CI changes |

Branch naming: `feature/`, `fix/`, `docs/`, `chore/`, `hotfix/` prefixes.
See [CONTRIBUTING.md](../CONTRIBUTING.md) for full details.

## What Copilot Should Avoid

- Do **not** add dependencies without checking the existing stack.
- Do **not** disable linting rules inline unless strictly necessary.
- Do **not** commit secrets, credentials, or `.env` files.
- Do **not** generate placeholder/stub implementations without a `TODO:` comment.

