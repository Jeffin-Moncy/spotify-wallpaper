from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
import os
from spotify_utils import get_spotify_metadata
from wallpaper_utils import generate_wallpaper, clean_old_wallpapers
from uuid import uuid4
from time import time
import uuid
from flask import send_file, request
import datetime
import csv

# Create the Flask app
app = Flask(__name__)
app.secret_key = "super-secret"  # Needed for flash messages

# Directory where generated wallpapers are stored
OUTPUT_DIR = "static/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Home page: handles both GET (show form) and POST (generate wallpaper)
@app.route("/", methods=["GET", "POST"])
def index():
    clean_old_wallpapers()  # Clean up old wallpapers each time the page is loaded

    if request.method == "POST":
        link = request.form.get("link")  # Get the Spotify link from the form
        old_filenames = request.form.get("filenames")  # (optional) old files

        if link:
            data = get_spotify_metadata(link)  # Fetch metadata from Spotify
            if not data:
                flash("Couldn't fetch data. Check the link and try again.", "error")
                return redirect(url_for("index"))

            base_name = uuid.uuid4().hex  # Unique name for the wallpaper
            filenames = generate_wallpaper(data, base_name=base_name)  # Generate wallpaper(s)
            return render_template("result.html", filenames=filenames, link=link, meta=data)

    # If GET or no valid POST, show the main page
    return render_template("index.html")

# Route to serve generated wallpaper images directly
@app.route("/output/<filename>")
def wallpaper(filename):
    return send_from_directory(OUTPUT_DIR, filename)

# Route to handle download requests (POST)
@app.route("/download", methods=["POST"])
def download():
    filename = request.form.get("filename")
    if not filename:
        return "Invalid request", 400

    # Log the download for analytics/ML purposes
    log_path = "download_log.csv"
    log_entry = {
        "filename": filename,
        "timestamp": datetime.datetime.now().isoformat(),
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent")
    }

    file_exists = os.path.exists(log_path)
    with open(log_path, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=log_entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_entry)

    # Send the actual image file as a download
    full_path = os.path.join("static", "output", filename)
    return send_file(full_path, as_attachment=True)

# Run the app if this file is executed directly
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, host="0.0.0.0", port=5000)

# if __name__ == "__main__":
#     app.run(debug=True)
