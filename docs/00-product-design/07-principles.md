# 07 — Engineering Principles

These rules hold for the entire project, every phase.

1. **One feature at a time.** Don't jump ahead. Finish and verify before moving on.

2. **Every feature is documented.** We maintain architecture notes in `docs/`
   as we build — documentation is part of "done," not an afterthought.

3. **Clean architecture over quick hacks.** Favor modular, testable code.
   The Model Router and the Manager-delegates rule exist because of this.

4. **Git discipline.** Small, meaningful commits with clear messages. One
   logical change per commit.

5. **Production mindset.** Even the MVP should be something you'd be
   comfortable showing in an interview. No throwaway code in `main`.

## How we apply them

- A phase isn't "done" until its code **and** its docs are committed.
- New cross-cutting decisions get an entry in [`../DECISIONS.md`](../DECISIONS.md).
- If a feature isn't in [`06-mvp-scope.md`](06-mvp-scope.md), it waits.
