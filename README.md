# 🎬 SmartRecs — AI Movie Recommendation Web App

![SmartRecs Login Preview](static/images/smartrec.jpg)

SmartRecs is a Flask web app that helps users rate movies and get personalized recommendations using a hybrid ML engine (content-based + collaborative filtering).

## ✨ Features
- 🔐 User auth (register/login/logout)
- ⭐ Rate movies with 1–5 stars
- 🤖 Hybrid recommendations tailored per user
- 🎞️ Movie details with genre, year, and trailer modal
- 🔎 Search + filter on Rate and Recommendations pages
- 🌙 Clean dark UI

## 🧠 How recommendations work
1. **Content-based filtering**: TF-IDF on genres + cosine similarity.
2. **Collaborative filtering**: user-user similarity from ratings matrix.
3. **Hybrid score**:

```text
final_score = 0.5 * content_score + 0.5 * collaborative_score
```

## 🏗️ Tech stack
- **Backend**: Flask
- **ML/Data**: pandas, numpy, scikit-learn
- **DB**: SQLite
- **Frontend**: Jinja templates + Bootstrap + custom CSS
- **Prod server**: gunicorn

## 📁 Project structure
```text
SmartRecs-AI-Movies/
├── app.py
├── recommender.py
├── models.py
├── requirements.txt
├── Procfile
├── railway.toml
├── data/
├── static/
│   ├── css/style.css
│   └── images/
└── templates/
```

## 🚀 Run locally
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open: `http://127.0.0.1:5000`

## 🌐 Deploy to Railway (recommended, easiest)
Railway is a very easy option for this Flask project and is already prepared in this repo (`Procfile` + `railway.toml`).

---
Made with ❤️ + 🍿 by SmartRecs.
