from fastapi import APIRouter
from fastapi.responses import Response
from app.core.experiment_evaluator import experiment_evaluator

router = APIRouter(prefix="/api/evaluation", tags=["Research Experiments & Evaluation"])


@router.get("/metrics")
def get_evaluation_metrics():
    return {
        "status": "success",
        "data": experiment_evaluator.run_comparative_evaluation()
    }


@router.get("/download-csv")
def download_evaluation_csv():
    csv_data = experiment_evaluator.generate_csv_report()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=emergency_corridor_evaluation_results.csv"
        }
    )

