from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, send_file, abort
import os, uuid
from pathlib import Path
from spotify_utils import get_spotify_metadata
from wallpaper_utils import generate_wallpaper, clean_old_wallpapers


# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Output directory
OUTPUT_DIR = "static/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === ROUTE: HOME PAGE ===
@app.route("/", methods=["GET", "POST"])
def index():
    clean_old_wallpapers()

    if request.method == "POST":
        link = request.form.get("link")
        if link:
            data = get_spotify_metadata(link)
            if not data:
                flash("Couldn't fetch data. Check the link and try again.", "error")
                return redirect(url_for("index"))

            filenames = generate_wallpaper(data)
            return render_template("result.html", filenames=filenames, link=link)

    return render_template("index.html")


# === ROUTE: Serve individual wallpaper images ===
@app.route("/output/<filename>")
def wallpaper(filename):
    return send_from_directory(OUTPUT_DIR, filename)

# === ROUTE: Download Route ===
@app.route("/download/<filename>")
def download_image(filename):
    path = Path(OUTPUT_DIR) / filename
    if not path.exists():
        abort(404)
    return send_file(path, as_attachment=True)


# === APP RUN ===
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, host="0.0.0.0", port=5000)
