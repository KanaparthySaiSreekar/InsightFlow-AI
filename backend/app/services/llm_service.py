from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import json


class LLMService:
    """Service for interacting with different LLM providers."""

    def __init__(self, provider: str, api_key: str):
        """Initialize LLM service with provider and API key."""
        self.provider = provider
        self.api_key = api_key
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the appropriate LLM based on provider."""
        if self.provider == "openai":
            return ChatOpenAI(
                model="gpt-4o",
                api_key=self.api_key,
                temperature=0,
            )
        elif self.provider == "google":
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=self.api_key,
                temperature=0,
            )
        elif self.provider == "anthropic":
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=self.api_key,
                temperature=0,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def generate_schema(self, schema_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate semantic schema from table metadata."""
        schema_prompt = f"""You are a data analyst. Analyze the following database schema and sample data, then generate a semantic description.

Database Information:
{json.dumps(schema_info, indent=2)}

Generate a JSON response with:
1. "tables": A list of table descriptions including:
   - "table_name": The name of the table
   - "description": What this table represents
   - "columns": List of column descriptions with:
     - "name": Column name
     - "type": Data type
     - "description": What this column represents
     - "example_values": A few example values
2. "relationships": Any apparent relationships between tables
3. "insights": Initial insights about the data

Return ONLY valid JSON, no other text."""

        messages = [
            SystemMessage(content="You are a data analyst expert at understanding database schemas."),
            HumanMessage(content=schema_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content

            # Try to parse the JSON
            schema_json = json.loads(content)
            return {"success": True, "schema": schema_json}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Failed to parse JSON: {str(e)}", "raw_response": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def text_to_sql(
        self,
        user_query: str,
        schema_json: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Convert natural language query to SQL."""
        # Build context from schema
        schema_context = json.dumps(schema_json, indent=2)

        # Build chat history context
        history_context = ""
        if chat_history:
            history_context = "\n\nPrevious conversation:\n"
            for msg in chat_history[-5:]:  # Last 5 messages for context
                history_context += f"{msg['role']}: {msg['content']}\n"

        sql_prompt = f"""You are a SQL expert. Convert the user's natural language question into a DuckDB SQL query.

Database Schema:
{schema_context}
{history_context}

User Question: {user_query}

Rules:
1. Return ONLY the SQL query, nothing else
2. Use DuckDB SQL syntax
3. Include appropriate WHERE clauses, JOINs, and aggregations as needed
4. If the question asks for visualization data, structure the query accordingly
5. Use LIMIT when appropriate to avoid huge result sets
6. For date/time operations, use DuckDB's date functions

Return ONLY the SQL query, no explanations or markdown."""

        messages = [
            SystemMessage(content="You are a SQL expert specialized in DuckDB queries."),
            HumanMessage(content=sql_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            sql_query = response.content.strip()

            # Clean up the SQL (remove markdown code blocks if present)
            if sql_query.startswith("```sql"):
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            elif sql_query.startswith("```"):
                sql_query = sql_query.replace("```", "").strip()

            return {"success": True, "sql": sql_query}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fix_sql_error(
        self,
        original_sql: str,
        error_message: str,
        schema_json: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Attempt to fix a SQL query based on error message (Self-healing)."""
        schema_context = json.dumps(schema_json, indent=2)

        fix_prompt = f"""The following SQL query failed with an error. Fix it.

Database Schema:
{schema_context}

Failed SQL Query:
{original_sql}

Error Message:
{error_message}

Return ONLY the corrected SQL query, nothing else."""

        messages = [
            SystemMessage(content="You are a SQL debugging expert."),
            HumanMessage(content=fix_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            sql_query = response.content.strip()

            # Clean up the SQL
            if sql_query.startswith("```sql"):
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            elif sql_query.startswith("```"):
                sql_query = sql_query.replace("```", "").strip()

            return {"success": True, "sql": sql_query}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def interpret_results(
        self,
        user_query: str,
        sql_query: str,
        query_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate a natural language interpretation of query results."""
        results_preview = json.dumps(query_results[:10], indent=2)  # First 10 rows

        interpret_prompt = f"""Interpret the following query results for the user.

User's Question: {user_query}

SQL Query Used:
{sql_query}

Query Results (first 10 rows):
{results_preview}

Total Rows: {len(query_results)}

Provide:
1. A concise natural language answer to the user's question
2. Key insights from the data
3. Recommended visualization type (bar, line, pie, scatter, table) based on the data

Return a JSON object with:
{{
    "answer": "Natural language answer",
    "insights": ["insight 1", "insight 2"],
    "visualization_type": "bar|line|pie|scatter|table"
}}

Return ONLY valid JSON."""

        messages = [
            SystemMessage(content="You are a data analyst expert at interpreting query results."),
            HumanMessage(content=interpret_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()

            # Parse JSON
            interpretation = json.loads(content)
            return {"success": True, "interpretation": interpretation}
        except json.JSONDecodeError as e:
            # Fallback to simple answer
            return {
                "success": True,
                "interpretation": {
                    "answer": f"Found {len(query_results)} results.",
                    "insights": [],
                    "visualization_type": "table",
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
