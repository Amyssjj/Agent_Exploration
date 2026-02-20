# Understanding Artifacts Index

| Artifact Title | Description | Direct Link |
| :--- | :--- | :--- |
| **OpenClaw Architecture Guide** | Comprehensive guide with Critique, Mental Models, and **Rendered Charts**. | [View Artifact](./architecture_guide.md) |
| **Skills & Agents Understanding** | How Skills and Agents work together: loading, filtering, and configuration. | [View Artifact](./skills_understanding.md) |
| **Video Analysis Understanding** | How OpenClaw analyzes videos: size limits, base64 encoding, Gemini API, token usage. | [View Artifact](./video_analysis_understanding.md) |
| **Token Efficiency Evaluation** | OpenClaw vs Claude Code per-call token comparison with measured numbers from codebase. | [View Artifact](./token_efficiency_evaluation.md) |
| **Session Architecture & Scenarios** | Deep dive into `session_status`, storing state, threading, and model overrides. | [View Artifact](./session_architecture.md) |
| **System Prompt & Optimization** | Analysis of token usage drivers (context/skills) and strategies to reduce per-turn cost. | [View Artifact](./system_prompt_structure.md) |
| **Exec Approval Plan & Safe Scripting** | Strategy for safe "General Control" of commands (Allowlist + Python) to avoid prompts. | [View Artifact](./exec_approval_implementation_plan.md) |
| **Agent Collaboration & Architecture** | High-level insights on Direct vs Channel routing, Hybrid Event Bus model, and interaction diagrams. | [View Artifact](./agent_collaboration_insights.md) |
| **Relationship between tools, memory, soul** | Deep dive into `TOOLS.md`, `MEMORY.md`, and `SOUL.md` with relationship visualization. | [View Artifact](./tools_memory_soul_relationship.md) |
| **Agent Structure & Workflow Guide** | Findings on essential agent files (`AGENTS.md`) and how to implement workflows (Projects). | [View Artifact](./investigation_agent_structure_workflow.md) |
| **Agent Files Best Practices** | How to cleanly separate SOUL, AGENTS, MEMORY, TOOLS, and SKILL files — decision flowchart and overlap fixes. | [View Artifact](./agent_files_best_practices.md) |
| **Workflow Enforcement Analysis** | Why STATUS.md goes stale, what's actually enforceable (gateway-level only), heartbeat vs cron for session reflection. | [View Artifact](./workflow_enforcement_analysis.md) |
| **Exec Security Two-Layer Flow** | How `openclaw.json` (agent layer) and `exec-approvals.json` (host layer) work together — 4 scenarios + employee handbook/building security analogy. | [View Artifact](./exec_security_two_layer_flow.md) |

