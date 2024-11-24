import numpy as np
import psycopg2
from sklearn.feature_extraction.text import TfidfVectorizer
import faiss  # Facebook AI Similarity Search

class CompetitionSearcher:
    def __init__(self, db_url):
        self.conn = psycopg2.connect(db_url)
        self.cursor = self.conn.cursor()
        self.feature_vectors = None
        self.vectorizer = None
        self.index = None
        self.data = None

    def fetch_competitions(self):
        """Fetch competitions data from the database."""
        self.cursor.execute("SELECT sport_name, sport_composition, ekp_number, date_start, date_end, city, discipline, competition_class, country, max_people_count, genders_and_ages FROM competitions")
        self.data = self.cursor.fetchall()

    def create_feature_vectors(self):
        """Create feature vectors using TF-IDF."""
        combined_data = [" ".join(map(str, entry)) for entry in self.data]
        self.vectorizer = TfidfVectorizer()
        self.feature_vectors = self.vectorizer.fit_transform(combined_data).toarray()

    def build_index(self):
        """Build a FAISS index for the feature vectors."""
        d = self.feature_vectors.shape[1]  # Dimensionality of the vectors
        self.index = faiss.IndexFlatL2(d)  # Index for searching using Euclidean distance
        self.index.add(np.array(self.feature_vectors).astype('float32'))  # Add vectors to the index

    def search_competitions_by_keywords(self, keywords_str: str):
        """Search competitions based on keywords."""
        keywords = [keyword.strip() for keyword in keywords_str.split(',') if keyword.strip()]
        
        if not keywords:
            print("No keywords provided for search.")
            return []

        query_str = " ".join(keywords)
        query_vector = self.vectorizer.transform([query_str]).toarray().astype('float32')

        k = 5  # Number of nearest neighbors
        distances, indices = self.index.search(query_vector, k)

        results = []
        for idx in indices[0]:
            if idx != -1:  # Check if the index is valid
                self.cursor.execute("SELECT * FROM competitions WHERE ekp_number = %s", (self.data[idx][2],))  # Use ekp_number to get full information
                results.append(self.cursor.fetchone())

        return results

    def close(self):
        """Close the database connection."""
        self.cursor.close()
        self.conn.close()
