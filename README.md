# SmartRecs - AI Movie Recommendation Web App

SmartRecs is a production-ready Flask web application that delivers personalized movie recommendations using a **hybrid recommender system** combining content-based and collaborative filtering.

## Architecture Overview

SmartRecs uses a layered architecture:

1. **Presentation Layer (Flask + Bootstrap 5)**
   - Templates render Dashboard, Rate Movies, and Recommendations pages.
   - Dark modern UI with responsive components.
2. **Application Layer (Flask routes in `app.py`)**
   - Handles auth, sessions, rating submissions, and recommendation requests.
3. **Recommendation Engine (`recommender.py`)**
   - Generates recommendations using hybrid ML logic.
4. **Data Layer (SQLite + CSV seed data)**
   - SQLite stores users and user-submitted ratings.
   - CSV data seeds movie metadata and baseline collaborative ratings.

### Diagram explanation (textual)

- User interacts with Browser UI.
- Browser sends requests to Flask routes.
- Flask authenticates session and reads/writes SQLite data.
- Flask calls `SmartRecommender`.
- Recommender loads movies and ratings, computes hybrid scores, returns Top 10.
- Flask renders ranked recommendations back to browser.

## Machine Learning Explanation

### 1) Content-Based Filtering
- Uses `TfidfVectorizer` on movie genre strings.
- Converts each movie to a TF-IDF vector.
- Computes `cosine_similarity` between user-rated movies and all movies.
- Weights similarity by normalized user ratings.

### 2) Collaborative Filtering
- Builds a user-item matrix from ratings.
- Computes cosine similarity between users.
- Predicts unseen movie preference based on weighted neighbor ratings.

### 3) Hybrid Filtering
Final score blends both approaches equally:

```text
final_score = 0.5 * content_score + 0.5 * collaborative_score
```

This balances genre affinity (content) with crowd behavior (collaborative).

## Security

- Passwords are hashed using `werkzeug.security.generate_password_hash`.
- Login verification uses `check_password_hash`.
- Session-based authentication secures protected routes.
- No plain text passwords are stored.

## Ethical AI Considerations

- **Bias awareness**: recommendations may reflect skewed source ratings.
- **Cold-start transparency**: new users initially receive weaker personalization.
- **Explainability**: genre and score display helps users understand outputs.
- **Privacy**: only essential user data (username + hashed password + ratings) is stored.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`

## Deployment on Render

1. Push project to GitHub.
2. Create a new **Web Service** on Render.
3. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Add env var:
   - `SECRET_KEY=<strong-random-value>`
5. Ensure persistent disk or bootstrap DB on startup for SQLite file.

## Project Structure

```text
/SmartRecs
    app.py
    recommender.py
    models.py
    requirements.txt
    README.md
    /data
        movies.csv
        ratings.csv
    /static
        /css
            style.css
        /images
            hero-bg.jpg
    /templates
        base.html
        dashboard.html
        login.html
        register.html
        rate.html
        recommendations.html
```
