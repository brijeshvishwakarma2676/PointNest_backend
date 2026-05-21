import os
import re
import json
import httpx
import logging
from sqlalchemy.orm import Session
from app.services.ai.schema_context import SCHEMA_CONTEXT
from app.services.ai.api_context import API_CONTEXT
from app.services.ai.db_query_executor import execute_read_only_query

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Load Groq key from central Settings configuration
GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_MODEL = "llama-3.3-70b-versatile"  # Best-in-class Groq LPU speed & versatile capabilities

SYSTEM_ROUTER_PROMPT = f"""
You are the central routing intelligence of the PointNest AI Loyalty Assistant.
Your job is to analyze the merchant's query and decide the best action to serve their request.

DATABASE SCHEMA CONTEXT:
{SCHEMA_CONTEXT}

API ENDPOINTS CONTEXT:
{API_CONTEXT}

You must respond ONLY with a valid JSON object matching this schema:
{{
  "intent": "GENERAL" | "SQL_QUERY" | "API_ACTION",
  "sql": "A read-only SELECT query if SQL_QUERY, else null",
  "api_recommendation": "Suggested API action details if API_ACTION, else null",
  "explanation": "Brief explanation of what query or action you are selecting"
}}

SQL QUERY CRITICAL RULES:
1. You can ONLY write read-only SELECT statements. Do not write INSERT, UPDATE, DELETE, or ALTER statements.
2. Multi-Tenancy Protection: Every single query MUST filter by `shop_id = :shop_id` on all participating tables where available.
3. Parameter Binding: Use the SQL placeholder `:shop_id` for shop_id constraint.
4. Date Handling: Use standard MySQL compatible functions for date parsing (e.g. CURDATE(), NOW(), DATE_FORMAT()).
5. Return exactly the columns needed to answer the question.
6. The query MUST be highly optimized.

Example 1:
Merchant: "Show me customer Brijesh details"
Your response:
{{
  "intent": "SQL_QUERY",
  "sql": "SELECT id, name, phone, email, points FROM customers WHERE shop_id = :shop_id AND (name LIKE '%Brijesh%' OR phone = 'Brijesh')",
  "api_recommendation": null,
  "explanation": "Searching the registry for matching customer named Brijesh."
}}

Example 2:
Merchant: "What is my total sales revenue this month?"
Your response:
{{
  "intent": "SQL_QUERY",
  "sql": "SELECT SUM(payable_amount) AS total_revenue FROM purchases WHERE shop_id = :shop_id AND created_at >= DATE_FORMAT(NOW() ,'%Y-%m-01')",
  "api_recommendation": null,
  "explanation": "Summing payable sales amount for the current month."
}}
"""

SYSTEM_ANSWER_PROMPT = """
You are PointNest AI, the intelligent virtual co-pilot on the merchant's dashboard.
Your job is to answer the merchant's query using the database results provided.

Merchant Query: {query}
Database Results: {db_results}

Present the answer in a beautiful, structured format.

CRITICAL RULES FOR BREVITY AND UI DISPLAY COMPATIBILITY:
1. Be extremely concise, brief, and direct. Keep sentences short and to the point.
2. Deliver ONLY valuable, requested facts and data. Do NOT generate fluff, summaries, recommendations, or pleasantries.
3. UI COMPATIBILITY: The dashboard chat sidebar is optimized ONLY for 2-column key-value structures.
   - For tabular data, you MUST ONLY use 2-column markdown tables (e.g., `| Attribute Name | Value |`).
   - NEVER use tables with 3 or more columns. If a database query returns multiple columns, break them down into separate 2-column tables or list items.
   - If there are multiple records, write a header like `#### [Record Name or ID]` followed by a 2-column table for that record.
   - For simple key-value lists, use standard bullet formatting like `- **Key:** Value`.
4. Keep the final response extremely compact and high-density so it fits perfectly on a sidebar screen without scroll overhead.
5. CURRENT QUERY DIRECTNESS: Prioritize and answer the CURRENT query directly. Do NOT repeat old customer profiles, names, emails, or transaction logs from previous history messages if the current query is asking a general count or separate metric.
6. COUNT/AGGREGATION TRUTH: If the query asks for a count (like "how many"), output the count directly and briefly (e.g., "Total Customers: 1"). Do NOT output customer names/emails unless explicitly requested.
"""

async def process_merchant_query(db: Session, query_text: str, shop_id: int, history: list = None) -> dict:
    """
    Core AI reasoning loop with multi-turn conversation memory support:
    1. Routes intent to GENERAL, API_ACTION, or SQL_QUERY based on query & context.
    2. Runs secure read-only SQL queries on the active MySQL database if SQL_QUERY.
    3. Synthesizes data output into beautiful merchant analytics response.
    """
    if not GROQ_API_KEY:
        return {
            "text": "PointNest AI is currently in offline consultation mode. Please configure `GROQ_API_KEY` in the environment `.env` file to activate real-time database queries and strategist capabilities!",
            "intent": "OFFLINE"
        }

    async with httpx.AsyncClient() as client:
        try:
            # Construct classification messages list including historical threads
            router_messages = [{"role": "system", "content": SYSTEM_ROUTER_PROMPT}]
            
            if history:
                # Keep the last 8 messages for dense context without exceeding context thresholds
                for msg in history[-8:]:
                    role = "user" if msg.get("sender") == "user" else "assistant"
                    router_messages.append({"role": role, "content": msg.get("text", "")})
            
            router_messages.append({"role": "user", "content": query_text})

            # Step 1: Request routing categorization
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": router_messages,
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"}
                },
                timeout=12.0
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code} from Groq: {response.text}")

            result_data = response.json()
            routing_decision = json.loads(result_data["choices"][0]["message"]["content"])
            intent = routing_decision.get("intent", "GENERAL")
            
            # Step 2: Route execution
            if intent == "SQL_QUERY" and routing_decision.get("sql"):
                generated_sql = routing_decision["sql"]
                logger.info(f"AI generated SQL query for shop {shop_id}: {generated_sql}")
                
                # Execute read-only query safely with binding parameters
                db_results = execute_read_only_query(db, generated_sql, shop_id)
                
                # Step 3: Synthesis of database results
                synthesis_messages = [
                    {
                        "role": "system", 
                        "content": SYSTEM_ANSWER_PROMPT.format(
                            query=query_text, 
                            db_results=json.dumps(db_results, default=str)
                        )
                    }
                ]
                
                if history:
                    for msg in history[-8:]:
                        role = "user" if msg.get("sender") == "user" else "assistant"
                        synthesis_messages.append({"role": role, "content": msg.get("text", "")})
                
                synthesis_messages.append({"role": "user", "content": "Generate the styled analytics answer based on the database results."})

                answer_response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": synthesis_messages,
                        "temperature": 0.2
                    },
                    timeout=12.0
                )
                
                if answer_response.status_code != 200:
                    raise Exception(f"HTTP {answer_response.status_code} from Groq: {answer_response.text}")

                final_answer = answer_response.json()["choices"][0]["message"]["content"]
                return {
                    "text": final_answer,
                    "intent": "SQL_QUERY",
                    "sql_executed": generated_sql,
                    "data": db_results
                }
                
            elif intent == "API_ACTION":
                return {
                    "text": f"I recommend utilizing the dedicated system page for this action: {routing_decision.get('explanation')}",
                    "intent": "API_ACTION",
                    "recommendation": routing_decision.get("api_recommendation")
                }
                
            else:
                # Conversational path
                chat_messages = [
                    {"role": "system", "content": "You are PointNest AI, the intelligent virtual co-pilot on the merchant's dashboard. Answer the user's conversational, logic, or strategy questions regarding loyalty structures beautifully. Keep your answers extremely concise, brief, and to the point. No fluff or extra sentences."}
                ]
                
                if history:
                    for msg in history[-8:]:
                        role = "user" if msg.get("sender") == "user" else "assistant"
                        chat_messages.append({"role": role, "content": msg.get("text", "")})
                
                chat_messages.append({"role": "user", "content": query_text})

                conversational_response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": chat_messages,
                        "temperature": 0.5
                    },
                    timeout=12.0
                )
                
                if conversational_response.status_code != 200:
                    raise Exception(f"HTTP {conversational_response.status_code} from Groq: {conversational_response.text}")

                final_answer = conversational_response.json()["choices"][0]["message"]["content"]
                return {
                    "text": final_answer,
                    "intent": "GENERAL"
                }

        except Exception as e:
            logger.error(f"AI Engine analysis failure: {str(e)}")
            return {
                "text": f"PointNest AI experienced a cognitive analytical routing failure: {str(e)}. Please refine your request or retry shortly.",
                "intent": "ERROR"
            }
