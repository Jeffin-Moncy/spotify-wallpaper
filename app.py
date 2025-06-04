from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, send_file, session, abort
import os, csv, uuid, shutil
from datetime import datetime
from spotify_utils import get_spotify_metadata
from wallpaper_utils import generate_wallpaper, clean_old_wallpapers
from cache_utils import get_cached_metadata, save_to_cache
from pathlib import Path
import pandas as pd
import glob
from dotenv import load_dotenv

# Initialize Flask app
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
ADMIN_PASSCODE = os.getenv("ADMIN_PASSCODE")

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
            from cache_utils import get_cached_metadata, save_to_cache

            data = get_cached_metadata(link)
            if not data:
                data = get_spotify_metadata(link)
                if not data:
                    flash("Couldn't fetch data. Check the link and try again.", "error")
                    return redirect(url_for("index"))
                save_to_cache(link, data)

            session_id = str(uuid.uuid4())
            base_name  = uuid.uuid4().hex
            filenames  = generate_wallpaper(data, base_name=base_name, session_id=session_id)
            return render_template("result.html", filenames=filenames, link=link, session_id=session_id)

    return render_template("index.html")

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('passcode') == ADMIN_PASSCODE:
            session['admin'] = True
            return redirect('/admin/stats')
        else:
            return render_template('login.html', error="Wrong passcode")
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/admin/login')



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

@app.route('/admin/stats')
def admin_stats():
    if not session.get('admin'):
        return redirect('/admin/login')

    try:
        all_log_df = pd.read_csv('all_log.csv')
    except FileNotFoundError:
        all_log_df = pd.DataFrame(columns=["No data"])

    try:
        download_df = pd.read_csv('download_log.csv')
    except FileNotFoundError:
        download_df = pd.DataFrame(columns=["No data"])

    # Fix variable name mismatch
    outputs = get_image_list('output')       # folder: static/output/
    downloads = get_image_list('downloads')  # folder: static/downloads/

    return render_template(
        'admin_stats.html',
        all_log=all_log_df.to_dict(orient='records'),
        all_log_columns=all_log_df.columns,
        download=download_df.to_dict(orient='records'),
        download_columns=download_df.columns,
        outputs=outputs,
        downloads=downloads
    )

@app.route('/admin/download/<filename>')
def download_file(filename):
    allowed_files = ['all_log.csv', 'download_log.csv']
    if filename not in allowed_files:
        return abort(404)
    return send_file(filename, as_attachment=True)

def get_image_list(folder):
    path = os.path.join('static', folder)
    extensions = ('*.png', '*.jpg', '*.jpeg', '*.webp', '*.gif')
    
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(path, ext)))

    # Sort files by modified time, newest first
    files.sort(key=os.path.getmtime, reverse=True)

    # Convert to URL paths
    files = [f"/{file.replace(os.sep, '/')}" for file in files]
    return files


# === APP RUN ===
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, host="0.0.0.0", port=5000)
