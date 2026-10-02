# Quick Deploy & Live Test — Minimal Steps

For use **during the talk**: Task 1 and Task 2 (the notebooks) are already built and tested — skip straight to deploying the Task 2 orchestrator to AWS and invoking it live. Full background and troubleshooting are in [SETUP_GUIDE.md](SETUP_GUIDE.md); this file is only the commands.

Run everything from PowerShell, with your AWS credentials already configured (`aws sts get-caller-identity` should succeed).

---

## 0. One-time check before you're on stage

```powershell
cd "c:\Users\adnan\OneDrive\Desktop\code\aws-agentic-lab"
.\.venv\Scripts\Activate.ps1
aws sts get-caller-identity
agentcore --version
```

Confirm [.env](aws-agentic-lab/.env) has a valid, active Bedrock model/inference-profile ID for your account (e.g. `BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6`).

---

## 1. Create the AgentCore project (skip if `AgenticLab/` already exists)

```powershell
agentcore create --name AgenticLab --no-agent
cd AgenticLab
```

## 2. Register the agent

```powershell
agentcore add agent `
  --name BudgetOrchestrator `
  --type byo `
  --code-location ..\agentcore_app `
  --entrypoint agent.py `
  --language Python `
  --framework Strands `
  --model-provider Bedrock
```

## 3. Deploy

```powershell
agentcore validate
agentcore deploy -y
```

Wait for `✓ Deployed to 'default'` and note the printed Runtime ARN.

## 4. Test live, in front of the audience

```powershell
agentcore status

agentcore invoke "I earn $6000 a month, how should I budget it?"

agentcore invoke "How has AAPL performed over the last 5 days?"

agentcore invoke "I earn $6000/month, how should I budget it, and how is AAPL doing this week?"
```

## 5. (Optional) Show observability

```powershell
agentcore logs --since 1h
```

Or open **CloudWatch → GenAI Observability** in the console and show the trace for the invocation you just ran.

---

## After the talk — tear it down

```powershell
..\.venv\Scripts\python.exe ..\scripts\cleanup.py
```

This removes the AgentCore runtime, its ECR repo, its IAM role, the Cognito pool (if created), and the shared `CDKToolkit` bootstrap stack. See [SETUP_GUIDE.md](SETUP_GUIDE.md#8-task-4--clean-up-aws-resources) for manual console verification steps.
