"""
Visualization API endpoint.
Generates Plotly chart specifications from query results.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

try:
    from visualizer.plotly_generator import generate_plotly_chart
except ModuleNotFoundError:
    from backend.visualizer.plotly_generator import generate_plotly_chart

router = APIRouter()


class VisualizeRequest(BaseModel):
    """Request for visualization generation."""
    chart_config: Dict[str, Any]
    results: List[Dict[str, Any]]
    columns: List[str]


class VisualizeResponse(BaseModel):
    """Response with Plotly chart specification."""
    success: bool
    chart: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/visualize", response_model=VisualizeResponse)
async def visualize_endpoint(request: VisualizeRequest):
    """
    Generate Plotly chart specification from data.
    
    Args:
        request: Chart config, results, and columns
        
    Returns:
        Plotly chart JSON specification
    """
    try:
        # Validate inputs
        if not request.results:
            return VisualizeResponse(
                success=False,
                error="No data provided for visualization"
            )
        
        if not request.columns:
            return VisualizeResponse(
                success=False,
                error="No columns provided"
            )
        
        # Generate Plotly chart
        chart = generate_plotly_chart(
            chart_config=request.chart_config,
            results=request.results,
            columns=request.columns
        )
        
        return VisualizeResponse(
            success=True,
            chart=chart
        )
        
    except Exception as e:
        return VisualizeResponse(
            success=False,
            error=f"Visualization generation failed: {str(e)}"
        )
