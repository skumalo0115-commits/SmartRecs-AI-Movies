from __future__ import annotations

from collections import Counter

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
    return render_template("login.html", auth_mode=request.args.get("mode", "none"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return redirect(url_for("index", mode="register"))

    username = request.form["username"].strip().lower()
    password = request.form["password"]
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "danger")
        return redirect(url_for("index", mode="register"))

    password_hash = generate_password_hash(password)
    try:
        execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        session["user_id"] = fetch_one("SELECT id FROM users WHERE username = ?", (username,))["id"]
        session["username"] = username
        flash("Welcome to SmartRecs!", "success")
        return redirect(url_for("dashboard"))
    except Exception:
        flash("Username already exists.", "danger")
        return redirect(url_for("index", mode="register"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return redirect(url_for("index", mode="login"))

    username = request.form["username"].strip().lower()
    password = request.form["password"]
    user = fetch_one("SELECT * FROM users WHERE username = ?", (username,))

    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("dashboard"))

    flash("Invalid credentials.", "danger")
    return redirect(url_for("index", mode="login"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("index"))

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
        trending=movies_df.head(10).to_dict(orient="records"),
        active_tab="dashboard",
    )


def get_recommendations(user_id: int):
    app_ratings = load_app_ratings()
    recs = recommender.recommend(user_id, app_ratings, top_n=10)
    return recs.to_dict(orient="records")


@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id: int):
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("index"))

    movie = movies_df[movies_df["movie_id"] == movie_id]
    if movie.empty:
        flash("Movie not found.", "danger")
        return redirect(url_for("dashboard"))
    movie_data = movie.iloc[0].to_dict()
    user_rating = fetch_one("SELECT rating FROM user_ratings WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
    return render_template(
        "movie_detail.html",
        movie=movie_data,
        user_rating=user_rating["rating"] if user_rating else None,
        active_tab="recommendations",
    )


@app.route("/rate", methods=["GET", "POST"])
def rate_movies():
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("index"))

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
        return redirect(url_for("movie_detail", movie_id=movie_id))

    rated_ids = {r["movie_id"] for r in fetch_all("SELECT movie_id FROM user_ratings WHERE user_id = ?", (user_id,))}
    unrated = movies_df[~movies_df["movie_id"].isin(rated_ids)].to_dict(orient="records")
    return render_template("rate.html", movies=unrated, active_tab="rate")


@app.route("/recommendations")
def recommendations():
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("index"))

    return render_template("recommendations.html", recommendations=get_recommendations(user_id), active_tab="recommendations")


if __name__ == "__main__":
    app.run(debug=True)
