from __future__ import annotations

import json
import os
import re
from collections import Counter
from functools import lru_cache
from urllib.parse import quote_plus, urlencode
from urllib.request import urlopen

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
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

POSTER_MAP = {
    "inception": "https://image.tmdb.org/t/p/w500/8IB2e4r4oVhHnANbnm7O3Tj6tF8.jpg",
    "interstellar": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
    "the matrix": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
    "the dark knight": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
    "arrival": "https://image.tmdb.org/t/p/w500/x2FJsf1ElAgr63Y3PNPtJrcmpoe.jpg",
    "avatar": "https://image.tmdb.org/t/p/w500/kyeqWdyUXW608qlYkRqosgbbJyK.jpg",
    "the prestige": "https://upload.wikimedia.org/wikipedia/en/d/d2/Prestige_poster.jpg",
    "blade runner 2049": "https://image.tmdb.org/t/p/w500/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg",
    "guardians of the galaxy": "https://image.tmdb.org/t/p/w500/r7vmZjiyZw9rpJMQJdXpjgiCOk9.jpg",
    "shutter island": "https://image.tmdb.org/t/p/w500/4GDy0PHYX3VRXUtwK5ysFbg3kEx.jpg",
    "mad max: fury road": "https://image.tmdb.org/t/p/w500/hA2ple9q4qnwxp3hKVNhroipsir.jpg",
    "the shawshank redemption": "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg",
    "pulp fiction": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
    "the godfather": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
    "whiplash": "https://image.tmdb.org/t/p/w500/7fn624j5lj3xTme2SgiLCeuedmO.jpg",
    "the lord of the rings: the fellowship of the ring": "https://image.tmdb.org/t/p/w500/6oom5QYQ2yQTMJIbnvbkBL9cHo6.jpg",
    "the social network": "https://image.tmdb.org/t/p/w500/n0ybibhJtQ5icDqTp8eRytcIHJx.jpg",
    "parasite": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
    "dune": "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
    "spider-man: into the spider-verse": "https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg",
    "the grand budapest hotel": "https://image.tmdb.org/t/p/w500/eWdyYQreja6JGCzqHWXpWHDrrPo.jpg",
    "her": "https://image.tmdb.org/t/p/w500/eCOtqtfvn7mxGl6nfmq4b1exJRc.jpg",
    "la la land": "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0Rf0.jpg",
    "the lion king": "https://image.tmdb.org/t/p/w500/sKCr78MXSLixwmZ8DyJLrpMsd15.jpg",
    "gladiator": "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg",
    "the silence of the lambs": "https://image.tmdb.org/t/p/w500/uS9m8OBk1A8eM9I042bx8XXpqAq.jpg",
    "toy story": "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
    "se7en": "https://image.tmdb.org/t/p/w500/6yoghtyTpznpBik8EngEmJskVUO.jpg",
    "the truman show": "https://image.tmdb.org/t/p/w500/vuza0WqY239yBXOadKlGwJsZJFE.jpg",
    "the departed": "https://image.tmdb.org/t/p/w500/nT97ifVT2J1yMQmeq20Qblg61T.jpg",
    "black panther": "https://image.tmdb.org/t/p/w500/uxzzxijgPIY7slzFvMotPv8wjKA.jpg",
    "coco": "https://image.tmdb.org/t/p/w500/gGEsBPAijhVUFoiNpgZXqRVWJt2.jpg",
    "ford v ferrari": "https://image.tmdb.org/t/p/w500/dR1Ju50iudrOh3YgfwkAU1g2HZe.jpg",
    "knives out": "https://image.tmdb.org/t/p/w500/pThyQovXQrw2m0s9x82twj48Jq4.jpg",
    "the martian": "https://image.tmdb.org/t/p/w500/5BHuvQ6p9kfc091Z8RiFNhCwL4b.jpg",
    "no country for old men": "https://image.tmdb.org/t/p/w500/6d5XOczc226jECq0LIX0siKtgHR.jpg",
    "the imitation game": "https://image.tmdb.org/t/p/w500/zSqJ1qFq8NXFfi7JeIYMlzyR0dx.jpg",
    "inside out": "https://image.tmdb.org/t/p/w500/2H1TmgdfNtsKlU9jKdeNyYL5y8T.jpg",
    "a quiet place": "https://image.tmdb.org/t/p/w500/nAU74GmpUk7t5iklEp3bufwDq4n.jpg",
    "everything everywhere all at once": "https://image.tmdb.org/t/p/w500/w3LxiVYdWWRvEVdn5RYq6jIqkb1.jpg",
}

YEAR_MAP = {
    "inception": "2010",
    "interstellar": "2014",
    "the matrix": "1999",
    "the dark knight": "2008",
    "arrival": "2016",
    "avatar": "2009",
    "the prestige": "2006",
    "blade runner 2049": "2017",
    "guardians of the galaxy": "2014",
    "shutter island": "2010",
    "mad max: fury road": "2015",
    "the shawshank redemption": "1994",
    "pulp fiction": "1994",
    "the godfather": "1972",
    "whiplash": "2014",
    "the lord of the rings: the fellowship of the ring": "2001",
    "the social network": "2010",
    "parasite": "2019",
    "dune": "2021",
    "spider-man: into the spider-verse": "2018",
    "the grand budapest hotel": "2014",
    "her": "2013",
    "la la land": "2016",
    "the lion king": "1994",
    "gladiator": "2000",
    "the silence of the lambs": "1991",
    "toy story": "1995",
    "se7en": "1995",
    "the truman show": "1998",
    "the departed": "2006",
    "black panther": "2018",
    "coco": "2017",
    "ford v ferrari": "2019",
    "knives out": "2019",
    "the martian": "2015",
    "no country for old men": "2007",
    "the imitation game": "2014",
    "inside out": "2015",
    "a quiet place": "2018",
    "everything everywhere all at once": "2022",
}

TRAILER_MAP = {
    "inception": "YoHD9XEInc0",
    "interstellar": "zSWdZVtXT7E",
    "the matrix": "vKQi3bBA1y8",
    "the dark knight": "EXeTwQWrcwY",
    "arrival": "tFMo3UJ4B4g",
    "avatar": "5PSNL1qE6VY",
    "the prestige": "RLtaA9fFNXU",
    "blade runner 2049": "gCcx85zbxz4",
    "guardians of the galaxy": "d96cjJhvlMA",
    "shutter island": "5iaYLCiq5RM",
    "mad max: fury road": "hEJnMQG9ev8",
    "the shawshank redemption": "PLl99DlL6b4",
    "pulp fiction": "s7EdQ4FqbhY",
    "the godfather": "UaVTIH8mujA",
    "whiplash": "7d_jQycdQGo",
    "the lord of the rings: the fellowship of the ring": "V75dMMIW2B4",
    "the social network": "lB95KLmpLR4",
    "parasite": "5xH0HfJHsaY",
    "dune": "n9xhJrPXop4",
    "spider-man: into the spider-verse": "g4Hbz2jLxvQ",
    "the grand budapest hotel": "1Fg5iWmQjwk",
    "her": "WzV6mXIOVl4",
    "la la land": "0pdqf4P9MB8",
    "the lion king": "4sj1MT05lAA",
    "gladiator": "owK1qxDselE",
    "the silence of the lambs": "W6Mm8Sbe__o",
    "toy story": "v-PjgYDrg70",
    "se7en": "znmZoVkCjpI",
    "the truman show": "dlnmQbPGuls",
    "the departed": "iojhqm0JTW4",
    "black panther": "xjDjIWPwcPU",
    "coco": "Rvr68u6k5sI",
    "ford v ferrari": "zyYgDtY2AMY",
    "knives out": "qGqiHJTsRkQ",
    "the martian": "ej3ioOneTy8",
    "no country for old men": "38A__WT3-o0",
    "the imitation game": "nuPZUUED5uk",
    "inside out": "seMwpP0yeu4",
    "a quiet place": "WR7cc5t7tv8",
    "everything everywhere all at once": "wxN1T1uxQ2g",
}

EXACT_DESCRIPTIONS = {
    "inception": "A thief who steals corporate secrets through dream-sharing technology is tasked with planting an idea into a CEO's mind.",
    "interstellar": "In a dying future Earth, a team of explorers travels through a wormhole in search of a new home for humanity.",
    "the matrix": "A hacker discovers reality is a simulation and joins a rebellion fighting the machines controlling humanity.",
    "the dark knight": "Batman faces the Joker, an anarchic criminal mastermind who pushes Gotham toward chaos.",
    "arrival": "A linguist is recruited to communicate with mysterious aliens whose arrival could change humanity's future.",
    "avatar": "A marine on Pandora is torn between following orders and protecting the Na'vi people he comes to love.",
    "the prestige": "Two rival magicians in Victorian London become obsessed with outdoing each other at any cost.",
    "blade runner 2049": "A new blade runner uncovers a secret that leads him to track down former blade runner Rick Deckard.",
    "guardians of the galaxy": "A band of misfits teams up to stop a powerful villain and unexpectedly becomes heroes.",
    "shutter island": "A U.S. Marshal investigating a disappearance at a remote asylum uncovers disturbing truths.",
    "mad max: fury road": "In a post-apocalyptic wasteland, Max joins Furiosa in a high-octane escape from a tyrant.",
    "the shawshank redemption": "An imprisoned banker forms an enduring friendship and quietly plans a path to freedom.",
    "pulp fiction": "Interwoven stories of crime in Los Angeles follow hitmen, a boxer, and desperate thieves.",
    "the godfather": "The aging patriarch of a crime dynasty hands power to his reluctant son, Michael Corleone.",
    "whiplash": "A driven jazz drummer is pushed to his limits by a ruthless and demanding music instructor.",
    "the lord of the rings: the fellowship of the ring": "A hobbit and a fellowship begin a perilous quest to destroy a powerful ring.",
    "the social network": "The rise of Facebook sparks legal battles and fractured friendships around founder Mark Zuckerberg.",
    "parasite": "A poor family infiltrates a wealthy household, setting off a darkly comic chain of events.",
    "dune": "Paul Atreides arrives on Arrakis and is drawn into a battle over destiny, power, and survival.",
    "spider-man: into the spider-verse": "Teen Miles Morales becomes Spider-Man and joins spider-heroes from other dimensions.",
    "the grand budapest hotel": "A legendary concierge and his lobby boy become entangled in a stolen painting and family fortune.",
    "her": "A lonely writer falls in love with an advanced operating system designed to evolve emotionally.",
    "la la land": "An aspiring actress and a jazz musician fall in love while chasing their dreams in Los Angeles.",
    "the lion king": "After tragedy strikes, a lion cub must embrace his destiny as king of the Pride Lands.",
    "gladiator": "A betrayed Roman general becomes a gladiator and seeks vengeance against a corrupt emperor.",
    "the silence of the lambs": "An FBI trainee seeks help from imprisoned killer Hannibal Lecter to catch another serial murderer.",
    "toy story": "A cowboy doll's world is shaken when a flashy new space ranger becomes his owner's favorite toy.",
    "se7en": "Two detectives hunt a serial killer whose crimes are inspired by the seven deadly sins.",
    "the truman show": "A man slowly realizes his entire life is a television show broadcast to the world.",
    "the departed": "An undercover cop and a mole in the police race to expose each other in Boston's crime war.",
    "black panther": "T'Challa returns to Wakanda to rule as king while facing threats to his nation and legacy.",
    "coco": "A young boy journeys to the Land of the Dead to uncover his family's musical past.",
    "ford v ferrari": "Designer Carroll Shelby and driver Ken Miles build a race car to challenge Ferrari at Le Mans.",
    "knives out": "Detective Benoit Blanc investigates the suspicious death of a wealthy mystery novelist.",
    "the martian": "Stranded on Mars, astronaut Mark Watney fights to survive while NASA works to bring him home.",
    "no country for old men": "Violence erupts after a hunter finds drug money and is pursued by a relentless hitman.",
    "the imitation game": "Alan Turing leads efforts to crack Nazi Enigma codes during World War II.",
    "inside out": "A young girl's emotions navigate upheaval after her family moves to a new city.",
    "a quiet place": "A family must live in silence to avoid deadly creatures that hunt by sound.",
    "everything everywhere all at once": "A laundromat owner is pulled into a multiverse-spanning battle tied to family and identity.",
}

DEFAULT_DESCRIPTIONS = {
    row["title"].lower(): f"{row['title']} is a {row['genres'].replace('|', ', ')} film with memorable performances and storytelling."
    for _, row in movies_df.iterrows()
}


def _safe_json_get(url: str, timeout: float = 1.2) -> dict:
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
    return data if data.get("Response") == "True" else {}


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


def movie_with_details(movie: dict) -> dict:
    movie_copy = dict(movie)
    raw_title = movie_copy.get("title", "")
    year_match = re.search(r"\((\d{4})\)\s*$", raw_title)
    parsed_year = year_match.group(1) if year_match else None
    clean_title = re.sub(r"\s*\(\d{4}\)\s*$", "", raw_title).strip()
    lower_title = clean_title.lower()

    resolved_year = parsed_year or YEAR_MAP.get(lower_title, "2000")
    omdb = omdb_movie_data(clean_title, resolved_year)

    genres = movie_copy.get("genres", "")
    genre_list = [g for g in genres.split("|") if g]
    pretty_genres = omdb.get("Genre") or ", ".join(genre_list) or "Genre unavailable"

    release_date = omdb.get("Released")
    if not release_date or release_date == "N/A":
        release_date = f"01 Jan {resolved_year}"

    plot = omdb.get("Plot")
    description = plot if plot and plot != "N/A" else EXACT_DESCRIPTIONS.get(lower_title, DEFAULT_DESCRIPTIONS.get(lower_title, clean_title))
    description = re.sub(r"\b(.+?)\s+\1\b", r"\1", description, flags=re.IGNORECASE)

    movie_id = movie_copy.get("movie_id", movie_copy.get("id", 0))
    poster_url = (
    (omdb.get("Poster") if omdb.get("Poster") and omdb.get("Poster") != "N/A" else None)
    or tmdb_poster_url(clean_title, resolved_year)
    or POSTER_MAP.get(lower_title)
    or f"https://picsum.photos/seed/smartrecs-{movie_id}/480/720"
)
    
    trailer_id = TRAILER_MAP.get(lower_title)
    fallback_query = quote_plus(f"{clean_title} official trailer")

    movie_copy["clean_title"] = clean_title
    movie_copy["year"] = resolved_year
    movie_copy["release_date"] = release_date
    movie_copy["description"] = description
    movie_copy["pretty_genres"] = pretty_genres
    movie_copy["poster_url"] = poster_url or f"https://picsum.photos/seed/smartrecs-{movie_id}/480/720"

    movie_copy["trailer_embed_url"] = (
        f"https://www.youtube.com/embed/{trailer_id}"
        if trailer_id
        else f"https://www.youtube.com/embed?listType=search&list={fallback_query}"
    )
    return movie_copy




def filter_movies(movies: list[dict], query: str, year: str, genre: str) -> list[dict]:
    search = (query or "").strip().lower()
    year_filter = (year or "").strip()
    genre_filter = (genre or "").strip().lower()

    def matches(movie: dict) -> bool:
        title = str(movie.get("clean_title") or movie.get("title") or "").lower()
        movie_year = str(movie.get("year") or "")
        movie_genres = str(movie.get("pretty_genres") or movie.get("genres") or "").replace("|", ",").lower()

        if search and search not in title:
            return False
        if year_filter and year_filter != movie_year:
            return False
        if genre_filter and genre_filter not in movie_genres:
            return False
        return True

    return [movie for movie in movies if matches(movie)]

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
            user = fetch_one("SELECT id, username, email FROM users WHERE username = ?", (username,))
            if user:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["email"] = user["email"]
            flash("Registration successful. Welcome to SmartRecs!", "success")
            return redirect(url_for("dashboard"))
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


def _ratings_signature(user_id: int) -> str:
    rows = fetch_all("SELECT movie_id, rating FROM user_ratings WHERE user_id = ? ORDER BY movie_id", (user_id,))
    return "|".join(f"{r['movie_id']}:{r['rating']}" for r in rows)


@lru_cache(maxsize=256)
def _cached_recommendations(user_id: int, signature: str):
    app_ratings = load_app_ratings()
    recs = recommender.recommend(user_id, app_ratings, top_n=12)
    return [movie_with_details(movie) for movie in recs.to_dict(orient="records")]


def get_recommendations(user_id: int):
    return _cached_recommendations(user_id, _ratings_signature(user_id))


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
        _cached_recommendations.cache_clear()
        flash("Rating saved successfully!", "success")
        return redirect(url_for("rate_movies"))

    search = request.args.get("search", "")
    year = request.args.get("year", "")
    genre = request.args.get("genre", "")

    rated_ids = {r["movie_id"] for r in fetch_all("SELECT movie_id FROM user_ratings WHERE user_id = ?", (user_id,))}
    unrated = movies_df[~movies_df["movie_id"].isin(rated_ids)].to_dict(orient="records")
    detailed_movies = [movie_with_details(movie) for movie in unrated]
    filtered_movies = filter_movies(detailed_movies, search, year, genre)
    return render_template("rate.html", movies=filtered_movies, active_tab="rate", search=search, year=year, genre=genre)


@app.route("/recommendations")
def recommendations():
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))

    search = request.args.get("search", "")
    year = request.args.get("year", "")
    genre = request.args.get("genre", "")

    recommendations_list = get_recommendations(user_id)
    filtered_recommendations = filter_movies(recommendations_list, search, year, genre)

    return render_template(
        "recommendations.html",
        recommendations=filtered_recommendations,
        active_tab="recommendations",
        search=search,
        year=year,
        genre=genre,
    )


if __name__ == "__main__":
    app.run(debug=True)