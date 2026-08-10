from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SemanticSearchEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))

    def search(self, query: str, events: list, top_k: int = 5) -> list:
        """
        Fuzzy natural language vector search over event catalogue.
        """
        if not events or not query:
            return events[:top_k]

        texts = [f"{e.title} {e.category} {e.description} {e.location} {' '.join(e.tags or [])}" for e in events]
        matrix = self.vectorizer.fit_transform(texts)
        query_vec = self.vectorizer.transform([query])

        scores = cosine_similarity(query_vec, matrix)[0]
        ranked_indices = scores.argsort()[::-1]

        results = []
        for idx in ranked_indices:
            if scores[idx] > 0.01:
                results.append(events[idx])
            if len(results) >= top_k:
                break
        return results if results else events[:top_k]

semantic_search = SemanticSearchEngine()
