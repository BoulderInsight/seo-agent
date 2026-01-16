"""Main routes for the application."""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    """Render the home page with analysis form."""
    return render_template("home.html")


@main_bp.route("/history")
def history():
    """Render the analysis history page."""
    from app.services.storage import get_all_analyses

    analyses = get_all_analyses()
    return render_template("history.html", analyses=analyses)
