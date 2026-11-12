# Javo Agents — Local Runtime API Reference

Base URL: `http://127.0.0.1:8000` (Interactive OpenAPI docs available at `/docs` when running).

## 1. Health & Diagnostics
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health/` | Runtime health, DB connectivity, uptime |
| `GET` | `/health/system` | CPU, RAM, disk metrics (`SystemInfoResponse`) |
| `GET` | `/health/diagnostics` | Service readiness checks |

## 2. Agents
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/agents/` | List all 29 specialist agents |
| `GET` | `/agents/{agent_key}` | Detailed schema, capabilities, and config |
| `POST` | `/agents/{agent_key}/run` | Execute an agent with JSON inputs |
| `PUT` | `/agents/{agent_key}/config` | Update AI model, temperature, retry policy |
| `POST` | `/agents/{agent_key}/enable` | Enable agent |
| `POST` | `/agents/{agent_key}/disable` | Disable agent |

## 3. Tasks & Goals
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/tasks/` | Filter tasks by `state`, `priority`, `assigned_agent` |
| `POST` | `/tasks/` | Create a new task |
| `POST` | `/tasks/{task_id}/execute` | Run task via Master Orchestrator |
| `GET` | `/goals/` | List goals and milestones |
| `POST` | `/goals/` | Create a goal |
| `POST` | `/goals/{goal_id}/milestones` | Add milestone to a goal |

## 4. Workflows (16 Node Types)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/workflows/` | List visual workflows |
| `GET` | `/workflows/{id}` | Get workflow nodes & edges |
| `POST` | `/workflows/` | Create workflow (validated against `@javo/workflow-schema`) |
| `POST` | `/workflows/{id}/execute` | Execute workflow graph |

## 5. Social Accounts & Content
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/accounts/` | List connected social accounts |
| `POST` | `/accounts/` | Register social account |
| `GET` | `/accounts/{id}/brand` | Get Brand Profile |
| `PUT` | `/accounts/{id}/brand` | Update Brand Profile |
| `GET` | `/content/` | List content assets |
| `POST` | `/content/scan` | Scan local folder for new media |
| `POST` | `/content/schedule` | Schedule content for publishing |

## 6. Security, Approvals, Devices & Settings
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/security/status` | Emergency stop state, autopilot mode, warnings |
| `POST` | `/security/emergency-stop` | Activate global kill switch |
| `POST` | `/security/resume` | Resume from pause/stop |
| `GET` | `/security/audit-logs` | View immutable audit log entries |
| `GET` | `/approvals/` | List pending human approval items |
| `POST` | `/approvals/{id}/{decision}` | `approve`, `reject`, or `reschedule` |
| `GET` | `/settings/ai` | Get AI provider config & spend |
| `PUT` | `/settings/ai` | Update AI provider & budget caps |
| `GET` | `/devices/` | List paired Android/browser devices |
| `DELETE` | `/devices/{id}` | Revoke paired device |

## 7. WebSocket Events
Connect to `ws://127.0.0.1:8000/ws/events` for live agent status, waveform state changes, and approval notifications.
