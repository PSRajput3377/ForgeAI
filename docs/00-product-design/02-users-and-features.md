# 02 — Target Users & Core Features

## Target users

| User       | Priority   | Representative ask                  |
|------------|------------|-------------------------------------|
| Developers | ⭐⭐⭐⭐⭐ | "I want to add authentication."     |
| Companies  | ⭐⭐⭐⭐⭐ | "Build an internal dashboard."      |
| Startups   | ⭐⭐⭐⭐   | "We need CRUD APIs."                |
| Students   | ⭐⭐⭐⭐   | "Build my assignment."              |

Developers and companies are the primary audience — we optimize for them first.

## Core features

We define the **core product** instead of bolting on random features.

### 1. Project Creation
Create a project and choose a stack.

```
Create Project → Choose Stack → [ React | Next | FastAPI | Node | Spring ]
```

### 2. Task Chat
A chat interface where the user states the task in plain language.

> "Build Login Page"  ·  "Add JWT Authentication"

### 3. Agent Execution
Watch the team work, live, with per-agent status.

```
Planner    ✓
Research   ✓
Coding     ⟳ Running
Testing    … Waiting
```

### 4. Project Explorer
Browse the generated/edited project tree.

```
src/
  components/
  pages/
backend/
README
```

### 5. Logs
Every tool call is recorded and visible.

```
Opened file
Edited file
Ran npm install
Ran pytest
Created PR
```

### 6. Memory
Per-project history — past tasks, decisions, and context the agents can recall.

### 7. Settings
Choose the AI model (and provider) — see the Model Router in
[`04-architecture.md`](04-architecture.md).
