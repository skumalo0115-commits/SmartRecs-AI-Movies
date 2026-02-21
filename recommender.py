"""Hybrid movie recommender for SmartRecs.

This module combines:
1) Content-based filtering (TF-IDF on genres)
2) Collaborative filtering (user-user cosine similarity)
3) Hybrid scoring with equal weights
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SmartRecommender:
    def __init__(self, movies_path: str = "data/movies.csv", ratings_path: str = "data/ratings.csv") -> None:
        self.movies_df = pd.read_csv(movies_path)
        self.ratings_df = pd.read_csv(ratings_path)

        # Normalize genre text to a space-delimited form so TF-IDF can tokenize it.
        self.movies_df["genre_text"] = self.movies_df["genres"].str.replace("|", " ", regex=False)

        # STEP 1: Build the TF-IDF matrix for all movie genres.
        # Each movie becomes a vector in genre feature-space.
        self.tfidf = TfidfVectorizer()
        self.genre_matrix = self.tfidf.fit_transform(self.movies_df["genre_text"])

    def build_user_ratings(self, user_id: int, app_ratings_df: pd.DataFrame | None = None) -> pd.DataFrame:
        """Combine static seed ratings with in-app ratings for collaborative filtering."""
        ratings = self.ratings_df.copy()
        if app_ratings_df is not None and not app_ratings_df.empty:
            ratings = pd.concat([ratings, app_ratings_df], ignore_index=True)

        if user_id not in ratings["user_id"].values:
            ratings = pd.concat(
                [ratings, pd.DataFrame([{"user_id": user_id, "movie_id": -1, "rating": 0.0}])],
                ignore_index=True,
            )
        return ratings[ratings["movie_id"] != -1]

    def _content_scores(self, rated_movie_ids: list[int], rated_values: list[float]) -> pd.Series:
        """STEP 2: Content-Based Filtering.

        Compute cosine similarity between user-liked movies and every movie, then
        weight each similarity by the user's normalized rating.
        """
        movie_index = {mid: idx for idx, mid in enumerate(self.movies_df["movie_id"].tolist())}
        scores = np.zeros(len(self.movies_df))

        for movie_id, rating in zip(rated_movie_ids, rated_values):
            if movie_id not in movie_index:
                continue
            idx = movie_index[movie_id]
            sim = cosine_similarity(self.genre_matrix[idx], self.genre_matrix).flatten()
            weight = max(0.0, min(1.0, rating / 5.0))
            scores += sim * weight

        if scores.max() > 0:
            scores = scores / scores.max()

        return pd.Series(scores, index=self.movies_df["movie_id"])

    def _collab_scores(self, user_id: int, merged_ratings: pd.DataFrame) -> pd.Series:
        """STEP 3: Collaborative Filtering.

        Build a user-item matrix, compute user-user cosine similarity, then infer
        scores for unseen movies from similar users' ratings.
        """
        user_item = merged_ratings.pivot_table(index="user_id", columns="movie_id", values="rating", fill_value=0)

        if user_id not in user_item.index:
            return pd.Series(0.0, index=self.movies_df["movie_id"])

        sim_matrix = cosine_similarity(user_item)
        sim_df = pd.DataFrame(sim_matrix, index=user_item.index, columns=user_item.index)
        neighbors = sim_df.loc[user_id].drop(user_id)

        pred_scores: dict[int, float] = {}
        for movie_id in user_item.columns:
            if user_item.loc[user_id, movie_id] > 0:
                continue

            movie_ratings = user_item[movie_id]
            numerator = float((neighbors * movie_ratings).sum())
            denominator = float(np.abs(neighbors).sum())
            pred_scores[movie_id] = numerator / denominator if denominator > 0 else 0.0

        scores = pd.Series(pred_scores)
        if scores.empty:
            return pd.Series(0.0, index=self.movies_df["movie_id"])
        if scores.max() > 0:
            scores = scores / scores.max()

        return scores.reindex(self.movies_df["movie_id"], fill_value=0.0)

    def recommend(self, user_id: int, app_ratings_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """STEP 4: Hybrid recommendation.

        final_score = 0.5 * content_score + 0.5 * collaborative_score
        """
        merged_ratings = self.build_user_ratings(user_id, app_ratings_df)
        user_ratings = merged_ratings[merged_ratings["user_id"] == user_id]

        if user_ratings.empty:
            fallback = self.movies_df.copy()
            fallback["score"] = 0.0
            return fallback.head(top_n)

        content = self._content_scores(user_ratings["movie_id"].tolist(), user_ratings["rating"].tolist())
        collab = self._collab_scores(user_id, merged_ratings)

        hybrid = (0.5 * content) + (0.5 * collab)

        watched_ids = set(user_ratings["movie_id"].tolist())
        results = self.movies_df[~self.movies_df["movie_id"].isin(watched_ids)].copy()
        results["score"] = results["movie_id"].map(hybrid).fillna(0.0)
        results = results.sort_values("score", ascending=False).head(top_n)
        return results
