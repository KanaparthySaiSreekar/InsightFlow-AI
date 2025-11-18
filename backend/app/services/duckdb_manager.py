import duckdb
import pandas as pd
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import settings


class DuckDBManager:
    """Manages DuckDB connections and data ingestion."""

    def __init__(self, db_path: str):
        """Initialize DuckDB connection."""
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self.conn = duckdb.connect(self.db_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.conn:
            self.conn.close()

    @staticmethod
    def create_db_for_user(user_id: int, project_id: int) -> str:
        """Create a new DuckDB file for a user's project."""
        db_filename = f"user_{user_id}_project_{project_id}.duckdb"
        db_path = os.path.join(settings.DUCKDB_PATH, db_filename)

        # Create the database file
        conn = duckdb.connect(db_path)
        conn.close()

        return db_path

    def ingest_csv(self, file_path: str, table_name: str = "data") -> Dict[str, Any]:
        """Ingest CSV file into DuckDB."""
        try:
            # Read CSV with pandas for better error handling
            df = pd.read_csv(file_path)

            # Create table from dataframe
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

            return {
                "success": True,
                "table_name": table_name,
                "rows": len(df),
                "columns": list(df.columns),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def ingest_excel(self, file_path: str, table_name: str = "data") -> Dict[str, Any]:
        """Ingest Excel file into DuckDB."""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)

            results = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                safe_table_name = f"{table_name}_{sheet_name.replace(' ', '_')}"

                self.conn.execute(f"DROP TABLE IF EXISTS {safe_table_name}")
                self.conn.execute(f"CREATE TABLE {safe_table_name} AS SELECT * FROM df")

                results.append({
                    "table_name": safe_table_name,
                    "sheet_name": sheet_name,
                    "rows": len(df),
                    "columns": list(df.columns),
                })

            return {"success": True, "tables": results}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def ingest_json(self, file_path: str, table_name: str = "data") -> Dict[str, Any]:
        """Ingest JSON file into DuckDB."""
        try:
            df = pd.read_json(file_path)

            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

            return {
                "success": True,
                "table_name": table_name,
                "rows": len(df),
                "columns": list(df.columns),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_schema_info(self) -> List[Dict[str, Any]]:
        """Get schema information for all tables."""
        tables = self.conn.execute("SHOW TABLES").fetchall()
        schema_info = []

        for table in tables:
            table_name = table[0]
            columns = self.conn.execute(f"DESCRIBE {table_name}").fetchdf()
            sample_data = self.conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchdf()

            schema_info.append({
                "table_name": table_name,
                "columns": columns.to_dict('records'),
                "sample_data": sample_data.to_dict('records'),
                "row_count": self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            })

        return schema_info

    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute a SQL query and return results."""
        try:
            result = self.conn.execute(sql).fetchdf()
            return {
                "success": True,
                "data": result.to_dict('records'),
                "columns": list(result.columns),
                "row_count": len(result),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql,
            }

    def get_table_names(self) -> List[str]:
        """Get all table names in the database."""
        tables = self.conn.execute("SHOW TABLES").fetchall()
        return [table[0] for table in tables]
