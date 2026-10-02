"""AgentCore Runtime entrypoint — hosts the Task 2 multi-agent orchestrator in production.

Deploy with:
    agentcore add agent --name BudgetOrchestrator --type byo \
        --code-location ./agentcore_app --entrypoint agent.py --language Python \
        --framework Strands --model-provider Bedrock
    agentcore deploy -y
"""
import os

import yfinance as yf
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")

app = BedrockAgentCoreApp()
model = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION)


@tool
def apply_50_30_20_rule(monthly_income: float) -> dict:
    """Split monthly income into needs (50%), wants (30%), and savings (20%)."""
    return {
        "needs": round(monthly_income * 0.5, 2),
        "wants": round(monthly_income * 0.3, 2),
        "savings": round(monthly_income * 0.2, 2),
    }


budget_agent = Agent(
    model=model,
    tools=[apply_50_30_20_rule],
    system_prompt="You help users budget using the 50/30/20 rule.",
)


@tool
def budget_assistant(query: str) -> str:
    """Use this tool for any budgeting, spending, or savings questions."""
    return str(budget_agent(query))


@tool
def get_stock_summary(ticker: str) -> dict:
    """Fetch recent price info for a stock ticker using yfinance."""
    data = yf.Ticker(ticker)
    hist = data.history(period="5d")
    return {
        "ticker": ticker,
        "last_close": float(hist["Close"].iloc[-1]) if not hist.empty else None,
    }


financial_agent = Agent(
    model=model,
    tools=[get_stock_summary],
    system_prompt="You analyze stocks, portfolios, and market trends using live data tools.",
)


@tool
def financial_analysis_assistant(query: str) -> str:
    """Use this tool for stock, portfolio, or market analysis questions."""
    return str(financial_agent(query))


orchestrator = Agent(
    model=model,
    tools=[budget_assistant, financial_analysis_assistant],
    system_prompt=(
        "You are a financial orchestrator. Route budgeting questions to budget_assistant "
        "and investing/stock questions to financial_analysis_assistant. Synthesize a single "
        "clear answer for the user."
    ),
)


@app.entrypoint
def invoke(payload: dict) -> dict:
    prompt = payload.get("prompt", "")
    result = orchestrator(prompt)
    return {"result": str(result)}


if __name__ == "__main__":
    app.run()
