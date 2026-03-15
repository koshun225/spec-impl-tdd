---

description: "Task list for TODO App feature implementation"
---

# Tasks: TODO App

**Input**: Design documents from `/specs/001-todo-app/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api.md

**Tests**: TDD required per Constitution Principle I (Test-First). Tests MUST be written and FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend project structure: backend/app/__init__.py, backend/app/main.py, backend/tests/__init__.py, backend/tests/conftest.py
- [x] T002 Create backend/pyproject.toml with mypy strict, ruff, pytest configuration
- [x] T003 Create backend/requirements.txt with fastapi, uvicorn, aiosqlite, pydantic, structlog, httpx, pytest, pytest-asyncio dependencies
- [x] T004 [P] Initialize frontend Next.js project in frontend/ with TypeScript configuration
- [x] T005 [P] Create .gitignore with backend/todo.db, __pycache__, .venv, node_modules, .next

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Implement database connection manager and TODO table initialization (id, title, completed, created_at, updated_at with completed index) in backend/app/database.py
- [x] T007 Define Pydantic request/response models (TodoCreate, TodoUpdate, TodoResponse, TodoListResponse) in backend/app/models.py
- [x] T008 Configure structlog with JSON output and request_id middleware in backend/app/logging_config.py
- [x] T009 Setup FastAPI app with CORS (localhost:3000), lifespan event for DB init, and logging middleware in backend/app/main.py
- [x] T010 [P] Create pytest fixtures (async test client, test database, cleanup) in backend/tests/conftest.py
- [x] T011 [P] Create API client module for FastAPI communication (base URL, fetch/post/patch/delete helpers) in frontend/src/lib/api.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - TODO の基本操作 (Priority: P1) MVP

**Goal**: ユーザーが TODO を作成・表示・編集・削除できる

**Independent Test**: TODO の作成・表示・編集・削除を一通り操作し、データが正しく永続化されていることを確認する

### Tests for User Story 1 (TDD - write FIRST, ensure they FAIL)

- [x] T012 [P] [US1] Write Pydantic model validation tests (title required, max 200 chars, empty string rejection, whitespace-only rejection) in backend/tests/test_models.py
- [x] T013 [P] [US1] Write API tests for POST /api/todos (create with valid title, reject empty title, reject 201+ char title) in backend/tests/test_routes.py
- [x] T014 [P] [US1] Write API tests for GET /api/todos (list all todos, empty list response) in backend/tests/test_routes.py
- [x] T015 [P] [US1] Write API tests for PATCH /api/todos/{id} (update title, 404 for non-existent) in backend/tests/test_routes.py
- [x] T016 [P] [US1] Write API tests for DELETE /api/todos/{id} (delete existing, 404 for non-existent) in backend/tests/test_routes.py

### Implementation for User Story 1

- [x] T017 [US1] Implement CRUD database operations (create, get_all, get_by_id, update, delete) in backend/app/database.py
- [x] T018 [US1] Implement API routes for POST /api/todos, GET /api/todos, PATCH /api/todos/{id}, DELETE /api/todos/{id} in backend/app/routes.py
- [x] T019 [US1] Register routes in FastAPI app and verify all US1 tests pass in backend/app/main.py
- [x] T020 [US1] Create TodoForm component (title input, submit button, empty validation error display) in frontend/src/components/TodoForm.tsx
- [x] T021 [US1] Create TodoItem component (title display, inline edit on click, delete button with confirmation dialog) in frontend/src/components/TodoItem.tsx
- [x] T022 [US1] Create TodoList component (fetch and render todo list, empty state message) in frontend/src/components/TodoList.tsx
- [x] T023 [US1] Integrate components in main page (TodoForm + TodoList, state management) in frontend/src/app/page.tsx

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 完了管理とフィルタリング (Priority: P2)

**Goal**: ユーザーが TODO を完了/未完了に切り替え、ステータスでフィルタリングできる

**Independent Test**: TODO を複数作成し、一部を完了に切り替えた後、フィルタリングで「未完了のみ」「完了のみ」「全件」を切り替えて正しく絞り込めることを確認する

### Tests for User Story 2 (TDD - write FIRST, ensure they FAIL)

- [x] T024 [P] [US2] Write API tests for PATCH /api/todos/{id} with completed toggle (true→false, false→true) in backend/tests/test_routes.py
- [x] T025 [P] [US2] Write API tests for GET /api/todos?status=completed, status=active, status=all filtering in backend/tests/test_routes.py

### Implementation for User Story 2

- [x] T026 [US2] Add status query parameter filtering logic to GET /api/todos in backend/app/routes.py
- [x] T027 [US2] Add completion toggle checkbox (completed state visual distinction with strikethrough) to TodoItem in frontend/src/components/TodoItem.tsx
- [x] T028 [US2] Create TodoFilter component (All/Active/Completed filter buttons) in frontend/src/components/TodoFilter.tsx
- [x] T029 [US2] Integrate TodoFilter into main page and connect filter state to API calls in frontend/src/app/page.tsx

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 Run mypy --strict on backend/ and fix all type errors
- [ ] T031 [P] Run ruff check and ruff format on backend/ and fix all lint/format issues
- [ ] T032 [P] Add frontend layout with app title and basic styling in frontend/src/app/layout.tsx
- [ ] T033 Run quickstart.md verification steps (all 7 steps) end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion. Can start after Phase 2, but logically builds on US1 components
- **Polish (Phase 5)**: Depends on all user stories being complete

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Constitution: Test-First)
- Database operations before API routes
- API routes before frontend components
- Individual components before page integration
- Story complete before moving to next priority

### Parallel Opportunities

- T004, T005 can run in parallel with T001-T003 (different directories)
- T010, T011 can run in parallel (different directories)
- T012-T016 can all run in parallel (different test functions in same/different files)
- T024, T025 can run in parallel (different test functions)
- T030, T031, T032 can run in parallel (independent concerns)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test independently -> Demo (MVP!)
3. Add User Story 2 -> Test independently -> Demo
4. Polish -> Final validation with quickstart.md

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (Red-Green-Refactor)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
