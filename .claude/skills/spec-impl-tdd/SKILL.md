---
name: spec-impl-tdd
description: Execute TDD with Red/Green/QA team separation using worktree isolation. Integrates with speckit artifacts (spec.md, plan.md, tasks.md, contracts/).
disable-model-invocation: true
argument-hint: "<feature-name> [task-ids...]"
---

# spec-impl-tdd — TDD Separated Execution

Red Team writes tests in a worktree without seeing implementation. Green Team
implements in a separate worktree without seeing test code. QA Agent judges
failures against the contract. This physical separation prevents "Test Theatre"
— tests that merely validate implementation rather than specifying behavior.

ultrathink

## Quick Reference

| File | When to Read |
|------|-------------|
| `references/red-team-agent.md` | Before launching Red Phase agent |
| `references/green-team-agent.md` | Before launching Green Phase agent |
| `references/qa-agent.md` | When tests fail after Green Phase |

---

## Step 1: Initialization

### 1a. Resolve Feature

Parse `$ARGUMENTS`:
- `$0` = feature name (e.g., `001-todo-app`)
- Remaining args = optional task IDs (e.g., `T012 T013`)

Set `FEATURE_DIR` = `specs/$0/`

If the directory does not exist, list available features under `specs/` and stop.

### 1b. Load Speckit Artifacts

Read from `FEATURE_DIR`:

| File | Required | Purpose |
|------|----------|---------|
| `tasks.md` | Yes | Task list and execution order |
| `plan.md` | Yes | Tech context: language, test framework, project structure |
| `spec.md` | Yes | Requirements, acceptance scenarios (Given/When/Then) |
| `contracts/*.md` | No | API/interface contracts (endpoints, formats, errors) |
| `data-model.md` | No | Entity definitions, validation rules, state transitions |

Stop with a clear error naming the missing file if any required artifact is absent.

### 1c. Extract Config from plan.md

From the "Technical Context" section, extract:

| Setting | Source in plan.md | Default |
|---------|-------------------|---------|
| `language` | "Language/Version" field | (required — stop if missing) |
| `test_command` | "Testing" field | `pytest -v` |
| `src_dir` | "Project Structure" section | `src` |
| `test_dir` | "Project Structure" section | `tests` |

Fixed settings:
- `max_retries` = 3 (QA judgment retry limit)

When extracting `src_dir` and `test_dir`, look at the source code directory tree
in plan.md. For example, if plan.md shows `backend/app/` and `backend/tests/`,
set `src_dir = backend/app` and `test_dir = backend/tests`.

### 1d. Assemble Contract

Build the combined contract from speckit artifacts. This contract is the single
source of truth for both Red Team (test writing) and Green Team (implementation).

1. **API contracts** (from `contracts/*.md`): Endpoints, request/response formats,
   status codes, error response shapes
2. **Data model** (from `data-model.md`): Entity schemas, field constraints,
   validation rules, state transitions, indexes
3. **Acceptance scenarios** (from `spec.md`): Given/When/Then scenarios,
   functional requirements (FR-###), success criteria

### 1e. Parse Tasks

From `tasks.md`:

1. `- [ ]` = incomplete (execution candidate), `- [x]` = completed (skip)
2. If task IDs given in args, filter to only those tasks
3. Otherwise, select all incomplete tasks in document order
4. For each task, extract: ID (T###), description, file paths mentioned,
   phase context (which User Story / phase it belongs to)

---

## Step 2: Task Loop

For each target task, initialize `retry_count = 0` and execute Steps 2a–2f.

### Step 2a: Red Phase — Test Creation

Read `references/red-team-agent.md` for the full prompt template.

Launch an Agent with worktree isolation:

```
Agent(
  description: "Red Team: Test creation - {task_id}",
  isolation: "worktree",
  prompt: red-team-agent.md template with:
    - {contract}: assembled contract from Step 1d
    - {spec_md}: spec.md content
    - {task_description}: task entry from tasks.md
    - {src_dir}, {test_dir}, {language}
    - {qa_feedback}: QA feedback if retrying, empty string otherwise
)
```

After the agent completes:

1. Get `worktree_path` from agent return value
2. Copy test artifacts to main repo:
   ```bash
   cp -R {worktree_path}/{test_dir}/ {project_root}/{test_dir}/
   ```
3. Copy skeleton implementation to main repo:
   ```bash
   cp -R {worktree_path}/{src_dir}/ {project_root}/{src_dir}/
   ```
4. Copy test config files (e.g., `conftest.py`) from worktree root if present
5. Clean up worktree:
   ```bash
   rm -rf {worktree_path} && git worktree prune
   ```

If copy fails, preserve the worktree, report error, and stop.

### Step 2b: Red State Check

Run tests on main repo against the skeleton:

```bash
{test_command} {test_dir}/
```

- **All tests FAIL** → Red state confirmed. Proceed to Step 2c.
- **Some tests PASS against skeleton** → The test does not verify implementation
  properly. Increment `retry_count`. If `retry_count >= max_retries`, escalate
  (Step 3). Otherwise, retry Step 2a with feedback listing which tests passed
  and why this indicates a test defect.

### Step 2c: Filter Test Results

Run tests with result capture and extract only:

```
nodeid                              | outcome | exception_type
test_module::TestClass::test_name   | FAIL    | NotImplementedError
test_module::TestClass::test_other  | FAIL    | AssertionError
```

For pytest projects, use `pytest --json-report --json-report-file=report.json`
and extract `nodeid`, `outcome`, and exception type from `call.crash.message`.

**Remove all of the following** from the results given to Green Team:
- Assertion content (expected vs actual values)
- Stack traces
- Test file paths
- Any detail that reveals what the test checks

This filtered view prevents Green Team from reverse-engineering test assertions.

### Step 2d: Green Phase — Implementation

Read `references/green-team-agent.md` for the full prompt template.

Launch an Agent with worktree isolation:

```
Agent(
  description: "Green Team: Implementation - {task_id}",
  isolation: "worktree",
  prompt: green-team-agent.md template with:
    - {contract}: assembled contract from Step 1d
    - {filtered_test_result}: from Step 2c
    - {task_description}: task entry from tasks.md
    - {test_dir}: for deletion in worktree
    - {qa_feedback}: QA feedback if retrying, empty string otherwise
)
```

After the agent completes:

1. Get `worktree_path` from agent return value
2. Copy implementation to main repo:
   ```bash
   cp -R {worktree_path}/{src_dir}/ {project_root}/{src_dir}/
   ```
3. Clean up worktree:
   ```bash
   rm -rf {worktree_path} && git worktree prune
   ```

### Step 2e: Test and QA

Run tests on main repo:

```bash
{test_command} {test_dir}/
```

**If all tests PASS** → proceed to Step 2f.

**If test command itself fails** (import error, syntax error — no results
generated): Report as a command error (distinct from test failure) and stop.

**If tests fail** → launch QA Agent.

#### QA Agent

Read `references/qa-agent.md` for the prompt template.

Launch an Agent (no isolation — full access to both test and implementation):

```
Agent(
  description: "QA Agent: Judgment - {task_id}",
  prompt: qa-agent.md template with:
    - {test_code}: full test source from {test_dir}/
    - {impl_code}: full implementation from {src_dir}/
    - {contract}: assembled contract
    - {full_test_output}: unfiltered test output
    - {spec_md}: spec.md content
)
```

Route based on QA judgment:

| Judgment | Action |
|----------|--------|
| `test_violation` | `retry_count += 1`. If `>= max_retries` → escalate (Step 3). Otherwise → retry Red Phase (Step 2a) with QA feedback. |
| `impl_violation` | `retry_count += 1`. If `>= max_retries` → escalate (Step 3). Otherwise → re-run Step 2c to update filtered results, then retry Green Phase (Step 2d) with QA feedback. |
| `contract_issue` | Escalate immediately (Step 3). The contract needs human revision. Does NOT consume retry count. |

### Step 2f: Task Completion

Execute in this exact order:

1. **Cumulative regression test**: Run ALL tests (all completed tasks + current):
   ```bash
   {test_command} {test_dir}/
   ```
   If any prior task's tests regress → escalate (Step 3).

2. **Update tasks.md**: Change `- [ ]` to `- [x]` for this task.

3. **Commit**:
   ```bash
   git add {src_dir}/ {test_dir}/ {FEATURE_DIR}/tasks.md
   git commit -m "tdd({feature_name}): complete {task_id} - {task_summary}"
   ```

4. **Next task**: If tasks remain → Step 2a with fresh `retry_count = 0`.
   If all tasks done → Step 4.

---

## Step 3: Escalation

When retry limit is reached or a contract issue is found:

1. **Preserve code**: Keep all current test and implementation code in main repo.
   No rollback, no deletion.

2. **Ask user** via `AskUserQuestion`:

   ```
   ## Escalation

   Task {task_id}: {description}
   Reason: {escalation_reason}
   Retry count: {retry_count}/{max_retries}
   Last QA judgment: {judgment_type}
   Failed tests: {failed_test_list}

   ### Options
   1. Skip this task and continue with remaining tasks
   2. Stop all processing
   ```

3. **If skip**: Mark task in tasks.md as `- [ ] ~~{description}~~ (skipped)`.
   Continue to the next task.

4. **If stop**: End processing. Display the last successful commit hash as a
   restore point.

---

## Step 4: Completion

When all target tasks are done:

```
## TDD Complete — {feature_name}

### Completed
{completed_tasks_with_checkmarks}

### Skipped
{skipped_tasks_if_any}

### All cumulative tests: PASS
```

---

## Error Handling

All errors follow "safe stop" — never destroy existing git state or code.

| Error | Response |
|-------|----------|
| Missing speckit artifact | Name the missing file, suggest which speckit command to run |
| Worktree creation failure | Report error details, preserve git state |
| Test command error (not test failure) | Distinguish from test failure, report and stop |
| Agent produces no worktree | Report that agent generated no changes, stop |
| Artifact copy failure | Preserve worktree for recovery, report and stop |
| `plan.md` missing Technical Context | Stop and ask user to update plan.md |
