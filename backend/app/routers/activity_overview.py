from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db

router = APIRouter(prefix="/activities", tags=["Activity Overview"])


@router.get("/overview")
def get_activity_overview(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by activity status"),
    lead_name: Optional[str] = Query(None, description="Filter by lead name"),
    date_from: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    limit: int = Query(50, description="Limit number of records"),
    offset: int = Query(0, description="Offset for pagination"),
):
    """
    Fetch summarized activity data from PostgreSQL view 'activity_overview_view'.
    """
    try:
        query = "SELECT * FROM activity_overview_view WHERE 1=1"
        params = {}

        if status:
            query += " AND LOWER(activity_status) = LOWER(:status)"
            params["status"] = status
        if lead_name:
            query += " AND LOWER(lead_name) LIKE LOWER(:lead_name)"
            params["lead_name"] = f"%{lead_name}%"
        if date_from:
            query += " AND created_on >= :date_from"
            params["date_from"] = date_from
        if date_to:
            query += " AND created_on <= :date_to"
            params["date_to"] = date_to

        query += " ORDER BY created_on DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        result = db.execute(text(query), params)
        records = [dict(row._mapping) for row in result]

        return {
            "total_records": len(records),
            "filters": {
                "status": status,
                "lead_name": lead_name,
                "date_from": date_from,
                "date_to": date_to,
            },
            "data": records,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching overview: {str(e)}")
