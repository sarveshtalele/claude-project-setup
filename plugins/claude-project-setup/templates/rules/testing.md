---
paths:
  - "tests/**"
  - "**/*.test.*"
  - "**/*_test.*"
  - "**/test_*.py"
---
# Test rules (loaded only when touching tests)
- A test must fail if the behaviour it names breaks. Assertions on mocks alone don't count.
- Never weaken or delete an assertion to make a suite pass. Report the regression instead.
- Bug fix means a regression test named after the bug (`test_<symptom>`), and it has to be seen failing first.
- Fixtures come from real inputs (trimmed), not invented ones. Record the origin in a comment.
- Real-browser or network tests are tagged and runnable separately from unit tests.
