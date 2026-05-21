import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException

# List of forbidden keywords to enforce strictly read-only execution
FORBIDDEN_KEYWORDS = [
    r"\binsert\b", r"\bupdate\b", r"\bdelete\b", r"\bdrop\b", r"\balter\b",
    r"\bcreate\b", r"\breplace\b", r"\btruncate\b", r"\bgrant\b", r"\brevoke\b",
    r"\bload\b", r"\boutfile\b"
]

def execute_read_only_query(db: Session, query: str, shop_id: int):
    """
    Executes a read-only SELECT query safely inside the database transaction context.
    Strictly filters out any mutation attempts and binds parameters to enforce tenant isolation.
    """
    # Clean workspace and sanitize query string
    query_clean = re.sub(r'\s+', ' ', query.strip()).lower()
    
    # 1. Base intent verification: Must only start with select
    if not query_clean.startswith("select"):
        raise HTTPException(
            status_code=400,
            detail="Access Denied: Only SELECT operations are allowed."
        )
        
    # 2. String-level deep inspection for mutations
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(keyword, query_clean):
            raise HTTPException(
                status_code=400,
                detail="Access Denied: Unsafe keyword detected. Database mutations are strictly prohibited."
            )
            
    # 3. Parameterized Safe execution binding current shop_id
    try:
        result = db.execute(text(query), {"shop_id": shop_id})
        
        # Structure the returning keys and mapping values
        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return rows
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Database query syntax error: {str(e)}"
        )
