"""Analysis routes for the application."""

import uuid

from flask import Blueprint, Response, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from app.services.rate_limiter import analysis_rate_limiter, rate_limit

analysis_bp = Blueprint("analysis", __name__)

# In-memory storage for analysis progress
analysis_progress: dict[str, dict] = {}


@analysis_bp.route("/analyze", methods=["POST"])
@rate_limit(analysis_rate_limiter)
def analyze():
    """Start a new analysis."""
    url = request.form.get("url", "").strip()
    mode = request.form.get("mode", "single")
    max_pages = int(request.form.get("max_pages", 10))
    csv_file = request.files.get("keyword_csv")

    # Validation
    if not url:
        return render_template("error.html", error="URL is required"), 400

    if not url.startswith(("http://", "https://")):
        return render_template("error.html", error="URL must start with http:// or https://"), 400

    if max_pages < 1 or max_pages > 50:
        return render_template("error.html", error="Max pages must be between 1 and 50"), 400

    # Parse CSV if provided
    keyword_data = None
    if csv_file and csv_file.filename:
        filename = secure_filename(csv_file.filename)
        if not filename.endswith(".csv"):
            return render_template("error.html", error="Only CSV files are accepted"), 400

        from app.services.csv_parser import parse_keyword_csv

        try:
            keyword_data = parse_keyword_csv(csv_file)
        except ValueError as e:
            return render_template("error.html", error=f"CSV parsing error: {e}"), 400

    # Create analysis ID and start
    analysis_id = str(uuid.uuid4())
    analysis_progress[analysis_id] = {
        "status": "starting",
        "step": "Initializing...",
        "progress": 0,
    }

    # Run analysis in background (for now, synchronous)
    from app.models import AnalysisMode
    from app.services.orchestrator import run_analysis

    try:
        analysis_mode = AnalysisMode.FULL_SITE if mode == "full" else AnalysisMode.SINGLE_PAGE
        result = run_analysis(
            url=url,
            mode=analysis_mode,
            max_pages=max_pages if mode == "full" else 1,
            keyword_data=keyword_data,
            progress_callback=lambda step, pct: update_progress(analysis_id, step, pct),
        )

        # Store result
        from app.services.storage import save_analysis

        result.id = analysis_id
        save_analysis(result)

        return redirect(url_for("analysis.results", analysis_id=analysis_id))

    except Exception as e:
        return render_template("error.html", error=f"Analysis failed: {str(e)}"), 500


def update_progress(analysis_id: str, step: str, progress: int):
    """Update analysis progress."""
    if analysis_id in analysis_progress:
        analysis_progress[analysis_id] = {
            "status": "running",
            "step": step,
            "progress": progress,
        }


@analysis_bp.route("/progress/<analysis_id>")
def get_progress(analysis_id: str):
    """Get analysis progress."""
    if analysis_id not in analysis_progress:
        return jsonify({"status": "not_found"}), 404

    return jsonify(analysis_progress[analysis_id])


@analysis_bp.route("/results/<analysis_id>")
def results(analysis_id: str):
    """Display analysis results."""
    from app.services.storage import get_analysis

    result = get_analysis(analysis_id)
    if not result:
        return render_template("error.html", error="Analysis not found"), 404

    from app.services.report_generator import generate_html_report

    report_html = generate_html_report(result)

    return render_template(
        "results.html",
        result=result,
        report_html=report_html,
    )


@analysis_bp.route("/download/<analysis_id>/<format>")
def download(analysis_id: str, format: str):
    """Download analysis report."""
    from app.services.storage import get_analysis

    result = get_analysis(analysis_id)
    if not result:
        return render_template("error.html", error="Analysis not found"), 404

    from datetime import datetime
    from urllib.parse import urlparse

    domain = urlparse(result.url).netloc.replace(".", "_")
    date_str = datetime.now().strftime("%Y%m%d")
    base_filename = f"seo_analysis_{domain}_{date_str}"

    if format == "markdown":
        from app.services.report_generator import generate_markdown_report

        content = generate_markdown_report(result)
        return Response(
            content,
            mimetype="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={base_filename}.md"},
        )

    elif format == "html":
        from app.services.report_generator import generate_html_report

        content = generate_html_report(result)
        return Response(
            content,
            mimetype="text/html",
            headers={"Content-Disposition": f"attachment; filename={base_filename}.html"},
        )

    elif format == "csv":
        from app.services.report_generator import generate_csv_export

        content = generate_csv_export(result)
        return Response(
            content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={base_filename}_keywords.csv"},
        )

    elif format == "pdf":
        from app.services.report_generator import generate_pdf_report

        content = generate_pdf_report(result)
        return Response(
            content,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={base_filename}_full_report.pdf"},
        )

    return render_template("error.html", error="Invalid format"), 400


@analysis_bp.route("/delete/<analysis_id>", methods=["POST"])
def delete(analysis_id: str):
    """Delete an analysis."""
    from app.services.storage import delete_analysis

    delete_analysis(analysis_id)
    return redirect(url_for("main.history"))
