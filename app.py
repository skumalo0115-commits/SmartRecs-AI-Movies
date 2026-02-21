from __future__ import annotations

from collections import Counter
import re

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import execute, fetch_all, fetch_one, init_db
from recommender import SmartRecommender

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-in-production"

init_db()
recommender = SmartRecommender()
movies_df = pd.read_csv("data/movies.csv")

POSTER_MAP = {
    "inception": "https://image.tmdb.org/t/p/w500/8IB2e4r4oVhHnANbnm7O3Tj6tF8.jpg",
    "interstellar": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
    "the matrix": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
    "the dark knight": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
}


def movie_with_details(movie: dict) -> dict:
    movie_copy = dict(movie)
    title = movie_copy.get("title", "")
    year_match = re.search(r"\((\d{4})\)\s*$", title)
    movie_copy["year"] = year_match.group(1) if year_match else "Unknown"
    clean_title = re.sub(r"\s*\(\d{4}\)\s*$", "", title).strip()
    movie_copy["clean_title"] = clean_title
    genres = movie_copy.get("genres", "")
    genre_list = [g for g in genres.split("|") if g]
    movie_copy["genre_list"] = genre_list
    primary = genre_list[0] if genre_list else "cinematic"
    movie_copy["release_date"] = f"01 Jan {movie_copy['year']}" if movie_copy["year"] != "Unknown" else "Release date unavailable"
    movie_copy["description"] = (
        f"{clean_title} follows a compelling {primary.lower()} arc with strong character stakes and cinematic tension. "
        f"This title blends {', '.join(genre_list) if genre_list else 'multiple'} elements into an accessible movie-night pick. "
        f"Recommended for viewers who enjoy immersive storytelling and high replay value."
    )
    movie_id = movie_copy.get("movie_id", movie_copy.get("id", 0))
    movie_copy["poster_url"] = POSTER_MAP.get(clean_title.lower(), f"https://picsum.photos/seed/smartrecs-{movie_id}/480/720")
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
            for g in genre_str.split("|"):
                genre_counter[g] += 1
        if genre_counter:
            top_genre = genre_counter.most_common(1)[0][0]
        avg_rating = sum(r["rating"] for r in ratings) / rating_count
        score_pct = int((avg_rating / 5.0) * 100)

    recs = get_recommendations(user_id)

    return render_template(
        "dashboard.html",
        rating_count=rating_count,
        top_genre=top_genre,
        score_pct=score_pct,
        recommendations=recs,
        active_tab="dashboard",
    )


def get_recommendations(user_id: int):
    app_ratings = load_app_ratings()
    recs = recommender.recommend(user_id, app_ratings, top_n=10)
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
        flash("Rating saved.", "success")
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
