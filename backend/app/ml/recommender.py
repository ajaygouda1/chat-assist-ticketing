import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class EventRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")

    def recommend(self, user_attended_event_ids: list, all_events: list, top_k: int = 4) -> list:
        """
        Content-based recommendation engine.
        Calculates tf-idf vector similarity over event descriptions/categories.
        """
        if not all_events:
            return []
        
        texts = [f"{e.title} {e.category} {e.description} {' '.join(e.tags or [])}" for e in all_events]
        matrix = self.vectorizer.fit_transform(texts)

        attended_indices = [i for i, e in enumerate(all_events) if e.id in user_attended_event_ids]
        
        if not attended_indices:
            # If cold start, return popular/latest events
            return sorted(all_events, key=lambda x: x.available_tickets, reverse=True)[:top_k]

        user_profile = matrix[attended_indices].mean(axis=0)
        user_profile_arr = np.asarray(user_profile)
        
        scores = cosine_similarity(user_profile_arr, matrix)[0]
        
        ranked_indices = np.argsort(-scores)
        recommendations = []
        for idx in ranked_indices:
            e = all_events[idx]
            if e.id not in user_attended_event_ids:
                recommendations.append(e)
                if len(recommendations) >= top_k:
                    break
        return recommendations

recommender = EventRecommender()
