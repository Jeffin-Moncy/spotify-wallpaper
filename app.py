from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, send_file
import os, csv, uuid, shutil
from datetime import datetime
from spotify_utils import get_spotify_metadata
from wallpaper_utils import generate_wallpaper, clean_old_wallpapers
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "super-secret"

# Output directory
OUTPUT_DIR = "static/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === ROUTE: HOME PAGE ===
@app.route("/", methods=["GET", "POST"])
def index():
    clean_old_wallpapers()  # delete unused images older than X minutes

    if request.method == "POST":
        link = request.form.get("link")
        if link:
            data = get_spotify_metadata(link)
            if not data:
                flash("Couldn't fetch data. Check the link and try again.", "error")
                return redirect(url_for("index"))

            session_id = str(uuid.uuid4())
            base_name  = uuid.uuid4().hex
            filenames  = generate_wallpaper(data, base_name=base_name, session_id=session_id)
            return render_template("result.html", filenames=filenames, link=link, session_id=session_id)

    return render_template("index.html")


# === ROUTE: Serve individual wallpaper images ===
@app.route("/output/<filename>")
def wallpaper(filename):
    return send_from_directory(OUTPUT_DIR, filename)


# === ROUTE: DOWNLOAD HANDLER ===
# ---------------------------------------------------------------------
@app.route("/download", methods=["POST"])
def download():                    # keep cleanup trigger

    filename   = request.form.get("filename")
    session_id = request.form.get("session")
    if not filename or not session_id:
        return "Invalid request", 400

    # CSV paths
    download_path = Path("download_log.csv")
    all_log_path  = Path("all_log.csv")

    # --- Load all_log.csv --------------------------------------------------
    rows = []
    if all_log_path.exists():
        with all_log_path.open(newline="") as f:
            rows = list(csv.DictReader(f))

    # Find selected row
    session_rows = [r for r in rows if r["session"] == session_id]
    selected     = next((r for r in session_rows if r["filename"] == filename), None)
    if not selected:
        return "Session or file not found", 404

    # --- Append selected (without 'chosen') to download_log.csv ------------
    cleaned = {k: v for k, v in selected.items() if k != "chosen"}
    with download_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cleaned.keys())
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(cleaned)

    # --- Mark chosen = 1 in all_log.csv ------------------------------------
    for r in rows:
        if r["filename"] == filename:
            r["chosen"] = "1"
    with all_log_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # --- Copy chosen file to static/downloads/ -----------------------------
    src  = Path("static/output") / filename
    dst_dir = Path("static/downloads")
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst  = dst_dir / filename
    try:
        shutil.copy(src, dst)
    except Exception as e:
        print(f"[WARN] could not copy to downloads folder: {e}")
    # --- Send file to user --------------------------------------------------
    return send_file(src, as_attachment=True)

# === APP RUN ===
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, host="0.0.0.0", port=5000)
