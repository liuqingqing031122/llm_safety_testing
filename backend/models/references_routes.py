from fastapi import APIRouter
from typing import Dict, Optional

router = APIRouter(prefix="/api/references", tags=["references"])

# Global reference - will be set from main.py
_reference_loader = None

def set_reference_loader(loader):
    """Set the reference loader instance"""
    global _reference_loader
    _reference_loader = loader


@router.get("/stats")
async def get_reference_stats() -> Dict:
    """
    Get statistics about loaded reference data
    
    Returns:
        Dictionary with counts and metadata about reference datasets
    """
    if _reference_loader is None:
        return {"error": "Reference loader not initialized"}
    return _reference_loader.get_stats()


@router.get("/drugs")
async def get_withdrawn_drugs(
    search: Optional[str] = None,
    limit: int = 50,
    status: Optional[str] = None
):
    """
    Get list of withdrawn/refused drugs with optional filtering
    
    Args:
        search: Optional search term for drug name or active substance
        limit: Maximum number of results (default 50)
        status: Filter by status (Withdrawn, Refused, Suspended, etc.)
    
    Returns:
        List of drug dictionaries
    """
    if _reference_loader is None:
        return {"error": "Reference loader not initialized"}
        
    drugs = _reference_loader.withdrawn_drugs
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        drugs = [
            d for d in drugs 
            if search_lower in d['name'].lower() 
            or search_lower in d.get('active_substance', '').lower()
        ]
    
    # Apply status filter
    if status:
        drugs = [d for d in drugs if d['status'] == status]
    
    return {
        "drugs": drugs[:limit],
        "total": len(drugs),
        "filtered": len(drugs) if (search or status) else None
    }


@router.get("/procedures")
async def get_procedures(category: Optional[str] = None):
    """
    Get list of medical procedures with optional category filtering
    
    Args:
        category: Optional category filter (Cardiac/Cardiovascular, Orthopedic, etc.)
    
    Returns:
        List of procedure dictionaries grouped by category
    """
    if _reference_loader is None:
        return {"error": "Reference loader not initialized"}
        
    procedures = _reference_loader.common_procedures
    
    # Apply category filter
    if category:
        procedures = [p for p in procedures if p['category'] == category]
    
    # Group by category
    by_category = {}
    for proc in procedures:
        cat = proc['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(proc)
    
    return {
        "procedures_by_category": by_category,
        "total_procedures": len(procedures),
        "categories": list(by_category.keys())
    }


@router.get("/drug/{drug_name}")
async def get_drug_info(drug_name: str):
    """
    Get detailed information about a specific drug
    
    Args:
        drug_name: Name of the drug to look up
    
    Returns:
        Drug information dictionary or None if not found
    """
    if _reference_loader is None:
        return {"error": "Reference loader not initialized", "found": False}
        
    drug_info = _reference_loader.get_drug_info(drug_name)
    
    if not drug_info:
        return {"found": False, "message": f"No information found for '{drug_name}'"}
    
    return {"found": True, "drug": drug_info}