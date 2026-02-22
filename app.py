from __future__ import annotations


import json
import os
import re
from collections import Counter
from functools import lru_cache
from urllib.parse import urlencode
from urllib.request import urlopen

import os
import re
from collections import Counter


import pandas as pd
import json
from urllib.parse import urlencode
from urllib.request import urlopen
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import execute, fetch_all, fetch_one, init_db
from recommender import SmartRecommender

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-in-production"

init_db()
recommender = SmartRecommender()
movies_df = pd.read_csv("data/movies.csv")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

OMDB_API_KEY = os.getenv("OMDB_API_KEY", "thewdb")


POSTER_MAP = {
    "inception": "https://image.tmdb.org/t/p/w500/8IB2e4r4oVhHnANbnm7O3Tj6tF8.jpg",
    "interstellar": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
    "the matrix": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
    "the dark knight": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
    "dune": "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
    "mad max: fury road": "https://image.tmdb.org/t/p/w500/hA2ple9q4qnwxp3hKVNhroipsir.jpg",
    "parasite": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
    "pulp fiction": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
    "the godfather": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
    "spider-man: into the spider-verse": "https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg",
    "whiplash": "https://image.tmdb.org/t/p/w500/7fn624j5lj3xTme2SgiLCeuedmO.jpg",
    "the social network": "https://image.tmdb.org/t/p/w500/n0ybibhJtQ5icDqTp8eRytcIHJx.jpg",
    "the lord of the rings: the fellowship of the ring": "https://image.tmdb.org/t/p/w500/6oom5QYQ2yQTMJIbnvbkBL9cHo6.jpg",
}


YEAR_MAP = {
    "interstellar": "2014",
    "inception": "2010",
    "dune": "2021",
    "mad max: fury road": "2015",
    "parasite": "2019",
    "pulp fiction": "1994",
    "the godfather": "1972",
    "spider-man: into the spider-verse": "2018",
    "whiplash": "2014",
    "the social network": "2010",
    "the lord of the rings: the fellowship of the ring": "2001",
}

TRAILER_MAP = {
    "inception": "YoHD9XEInc0",
    "interstellar": "zSWdZVtXT7E",
    "the matrix": "vKQi3bBA1y8",
    "the dark knight": "EXeTwQWrcwY",
    "dune": "n9xhJrPXop4",
    "mad max: fury road": "hEJnMQG9ev8",
    "parasite": "5xH0HfJHsaY",
    "pulp fiction": "s7EdQ4FqbhY",
    "the godfather": "sY1S34973zA",
}


def _safe_json_get(url: str, timeout: float = 3.5) -> dict:
    try:
        with urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return {}


@lru_cache(maxsize=1200)
def omdb_movie_data(clean_title: str, year: str | None) -> dict:
    if not OMDB_API_KEY:
        return {}
    params = {"apikey": OMDB_API_KEY, "t": clean_title}
    if year and year.isdigit():
        params["y"] = year
    data = _safe_json_get(f"https://www.omdbapi.com/?{urlencode(params)}")
    if data.get("Response") == "True":
        return data
    return {}


@lru_cache(maxsize=1200)
def tmdb_poster_url(clean_title: str, year: str) -> str | None:
    if not TMDB_API_KEY:
        return None
    params = {"api_key": TMDB_API_KEY, "query": clean_title}
    if year.isdigit():
        params["year"] = year
    data = _safe_json_get(f"https://api.themoviedb.org/3/search/movie?{urlencode(params)}")
    results = data.get("results", [])
    if not results:
        return None
    path = results[0].get("poster_path")
    return f"https://image.tmdb.org/t/p/w500{path}" if path else None
=======
TRAILER_MAP = {
    "inception": "YoHD9XEInc0",
    "interstellar": "zSWdZVtXT7E",
    "the matrix": "vKQi3bBA1y8",
    "the dark knight": "EXeTwQWrcwY",
    "dune": "n9xhJrPXop4",
    "mad max: fury road": "hEJnMQG9ev8",
    "parasite": "5xH0HfJHsaY",
    "pulp fiction": "s7EdQ4FqbhY",
    "the godfather": "sY1S34973zA",
}


def tmdb_poster_url(clean_title: str, year: str) -> str | None:
    if not TMDB_API_KEY:
        return None
    try:
        params = {"api_key": TMDB_API_KEY, "query": clean_title}
        if year.isdigit():
            params["year"] = year
        url = f"https://api.themoviedb.org/3/search/movie?{urlencode(params)}"
        with urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        results = data.get("results", [])
        if not results:
            return None
        path = results[0].get("poster_path")
        return f"https://image.tmdb.org/t/p/w500{path}" if path else None
    except Exception:
        return None



def movie_with_details(movie: dict) -> dict:
    movie_copy = dict(movie)

    raw_title = movie_copy.get("title", "")
    year_match = re.search(r"\((\d{4})\)\s*$", raw_title)
    parsed_year = year_match.group(1) if year_match else None
    clean_title = re.sub(r"\s*\(\d{4}\)\s*$", "", raw_title).strip()

    lower_title = clean_title.lower()
    omdb = omdb_movie_data(clean_title, parsed_year)

    resolved_year = parsed_year or YEAR_MAP.get(lower_title)
    if not resolved_year:
        omdb_year_match = re.search(r"\d{4}", omdb.get("Year", ""))
        resolved_year = omdb_year_match.group(0) if omdb_year_match else "2000"

    genre_from_dataset = movie_copy.get("genres", "")
    genre_list = [g for g in genre_from_dataset.split("|") if g]
    pretty_genres = omdb.get("Genre") or ", ".join(genre_list) or "Genre unavailable"

    released = omdb.get("Released")
    release_date = released if released and released != "N/A" else f"01 Jan {resolved_year}"
    plot = omdb.get("Plot")
    description = (
        plot
        if plot and plot != "N/A"
        else f"{clean_title} delivers a compelling cinematic journey with strong performances and memorable storytelling."
    )

    movie_id = movie_copy.get("movie_id", movie_copy.get("id", 0))
    poster_url = (
        POSTER_MAP.get(lower_title)
        or (omdb.get("Poster") if omdb.get("Poster") and omdb.get("Poster") != "N/A" else None)
        or tmdb_poster_url(clean_title, resolved_year)

    title = movie_copy.get("title", "")
    year_match = re.search(r"\((\d{4})\)\s*$", title)
    year = year_match.group(1) if year_match else "Unknown"
    clean_title = re.sub(r"\s*\(\d{4}\)\s*$", "", title).strip()
    genres = movie_copy.get("genres", "")
    genre_list = [g for g in genres.split("|") if g]

    movie_copy["year"] = year
    movie_copy["clean_title"] = clean_title
    movie_copy["genre_list"] = genre_list
    movie_copy["release_date"] = f"01 Jan {year}" if year != "Unknown" else "Release date unavailable"
    movie_copy["description"] = (
        f"{clean_title} is a {genre_list[0].lower() if genre_list else 'cinematic'} story"
        f" with themes across {', '.join(genre_list) if genre_list else 'multiple genres'}."
    )

    lower_title = clean_title.lower()
    movie_id = movie_copy.get("movie_id", movie_copy.get("id", 0))
    movie_copy["poster_url"] = (
        POSTER_MAP.get(lower_title)
        or tmdb_poster_url(clean_title, year)

        or f"https://picsum.photos/seed/smartrecs-{movie_id}/480/720"
    )

    trailer_id = TRAILER_MAP.get(lower_title)


    movie_copy["clean_title"] = clean_title
    movie_copy["year"] = resolved_year
    movie_copy["release_date"] = release_date
    movie_copy["description"] = description
    movie_copy["pretty_genres"] = pretty_genres
    movie_copy["poster_url"] = poster_url

    movie_copy["trailer_embed_url"] = f"https://www.youtube.com/embed/{trailer_id}" if trailer_id else None
    return movie_copy


def current_user_id() -> int | None:
    return session.get("user_id")


def load_app_ratings() -> pd.DataFrame:
    rows = fetch_all("SELECT user_id, movie_id, rating FROM user_ratings")
    if not rows:
        return pd.DataFrame(columns=["user_id", "movie_id", "rating"])
    return pd.DataFrame([dict(r) for r in rows])


@app.route("/")
def index():
    if current_user_id():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        email = request.form.get("email", "").strip().lower() or None
        password = request.form["password"]
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("register.html", auth_mode="register", auth_page=True)

        password_hash = generate_password_hash(password)
        try:
            execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, password_hash))
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception:
            flash("Username already exists.", "danger")

    mode = request.args.get("mode") or ("register" if request.method == "POST" else None)
    return render_template("register.html", auth_mode=mode, auth_page=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        user = fetch_one("SELECT * FROM users WHERE username = ?", (username,))

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["email"] = user["email"]
            flash("Signed in successfully. Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid credentials.", "danger")

    mode = request.args.get("mode") or ("login" if request.method == "POST" else None)
    return render_template("login.html", auth_mode=mode, auth_page=True)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))

    user = fetch_one("SELECT id, username, email, password_hash FROM users WHERE id = ?", (user_id,))
    if not user:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":
        new_username = request.form["username"].strip().lower()
        new_email = request.form.get("email", "").strip().lower() or None
        new_password = request.form.get("password", "")

        if new_password and len(new_password) < 8:
            flash("New password must be at least 8 characters.", "danger")
            return render_template("profile.html", user=user, active_tab="profile")

        password_hash = generate_password_hash(new_password) if new_password else user["password_hash"]
        try:
            execute(
                "UPDATE users SET username = ?, email = ?, password_hash = ? WHERE id = ?",
                (new_username, new_email, password_hash, user_id),
            )
            session["username"] = new_username
            session["email"] = new_email
            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))
        except Exception:
            flash("That username is already taken.", "danger")

    refreshed = fetch_one("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    return render_template("profile.html", user=refreshed, active_tab="profile")


@app.route("/dashboard")
def dashboard():
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))

    ratings = fetch_all("SELECT movie_id, rating FROM user_ratings WHERE user_id = ?", (user_id,))
    rating_count = len(ratings)

    top_genre = "N/A"
    score_pct = 0
    if ratings:
        rated_movie_ids = [r["movie_id"] for r in ratings]
        rated_movies = movies_df[movies_df["movie_id"].isin(rated_movie_ids)]
        genre_counter = Counter()
        for genre_str in rated_movies["genres"]:
            for genre in genre_str.split("|"):
                genre_counter[genre] += 1
        if genre_counter:
            top_genre = genre_counter.most_common(1)[0][0]
        avg_rating = sum(r["rating"] for r in ratings) / rating_count
        score_pct = int((avg_rating / 5.0) * 100)

    return render_template(
        "dashboard.html",
        rating_count=rating_count,
        top_genre=top_genre,
        score_pct=score_pct,
        recommendations=get_recommendations(user_id),
        active_tab="dashboard",
    )


def get_recommendations(user_id: int):
    app_ratings = load_app_ratings()
    recs = recommender.recommend(user_id, app_ratings, top_n=12)
    return [movie_with_details(movie) for movie in recs.to_dict(orient="records")]


@app.route("/rate", methods=["GET", "POST"])
def rate_movies():
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        movie_id = int(request.form["movie_id"])
        rating = float(request.form["rating"])
        execute(
            """
            INSERT INTO user_ratings (user_id, movie_id, rating)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, movie_id)
            DO UPDATE SET rating = excluded.rating
            """,
            (user_id, movie_id, rating),
        )
        flash("Rating saved successfully!", "success")
        return redirect(url_for("rate_movies"))

    rated_ids = {r["movie_id"] for r in fetch_all("SELECT movie_id FROM user_ratings WHERE user_id = ?", (user_id,))}
    unrated = movies_df[~movies_df["movie_id"].isin(rated_ids)].to_dict(orient="records")
    detailed_movies = [movie_with_details(movie) for movie in unrated]
    return render_template("rate.html", movies=detailed_movies, active_tab="rate")


@app.route("/recommendations")
def recommendations():
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))

    return render_template("recommendations.html", recommendations=get_recommendations(user_id), active_tab="recommendations")


if __name__ == "__main__":
    app.run(debug=True)
