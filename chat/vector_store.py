import os
import sqlite3
import json
import numpy as np # type: ignore
from django.conf import settings # type: ignore
import google.generativeai as genai # type: ignore


class CourseVectorStore:
    def __init__(self):
        db_path = os.path.join(settings.BASE_DIR, "chat", "native_vector_db.sqlite3")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
        
        # Configure Gemini
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if api_key:
            genai.configure(api_key=api_key)

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                course_id INTEGER,
                lecture_id INTEGER,
                title TEXT,
                document TEXT,
                embedding_json TEXT,
                timestamp_start REAL DEFAULT NULL,
                timestamp_end REAL DEFAULT NULL,
                display_time TEXT DEFAULT NULL,
                video_url TEXT DEFAULT NULL,
                content_type TEXT DEFAULT 'text'
            )
        ''')
        # Migrate existing tables that may not have the new columns
        existing_cols = [
            row[1] for row in cursor.execute("PRAGMA table_info(embeddings)").fetchall()
        ]
        migrations = [
            ("timestamp_start", "REAL DEFAULT NULL"),
            ("timestamp_end",   "REAL DEFAULT NULL"),
            ("display_time",    "TEXT DEFAULT NULL"),
            ("video_url",       "TEXT DEFAULT NULL"),
            ("content_type",    "TEXT DEFAULT 'text'"),
        ]
        for col_name, col_def in migrations:
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE embeddings ADD COLUMN {col_name} {col_def}")
        
        self.conn.commit()

    def _get_embedding(self, text: str):
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    def _chunk_text(self, text: str, max_words=200):
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_words):
            chunks.append(" ".join(words[i:i + max_words]))
        return chunks
        
    def _cosine_similarity(self, v1, v2):
        dot_product = np.dot(v1, v2)
        norm_a = np.linalg.norm(v1)
        norm_b = np.linalg.norm(v2)
        if norm_a == 0 or norm_b == 0:
            return 0
        return dot_product / (norm_a * norm_b)

    def add_lecture_content(self, course_id: int, lecture_id: int, title: str, content_text: str):
        """Add plain text content (syllabus, article) to vector store."""
        if not content_text.strip():
            return
            
        chunks = self._chunk_text(content_text)
        cursor = self.conn.cursor()
        
        for i, chunk in enumerate(chunks):
            embedding = self._get_embedding(chunk)
            if embedding:
                doc_id = f"course_{course_id}_lecture_{lecture_id}_chunk_{i}"
                cursor.execute('''
                    INSERT OR REPLACE INTO embeddings 
                    (id, course_id, lecture_id, title, document, embedding_json, content_type)
                    VALUES (?, ?, ?, ?, ?, ?, 'text')
                ''', (doc_id, course_id, lecture_id, title, chunk, json.dumps(embedding)))
                
        self.conn.commit()

    def add_transcript_chunk(
        self,
        course_id: int,
        lecture_id: int,
        title: str,
        text: str,
        start_seconds: float,
        end_seconds: float,
        display_time: str,
        video_url: str,
    ):
        """
        Add a video transcript chunk with timestamp metadata to the vector store.
        Uses a unique ID based on lecture and timestamp to allow re-indexing.
        """
        if not text.strip():
            return False
            
        embedding = self._get_embedding(text)
        if not embedding:
            return False
        
        # Use timestamp-based ID so re-indexing replaces old data cleanly
        doc_id = f"course_{course_id}_lecture_{lecture_id}_ts_{int(start_seconds)}"
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO embeddings 
            (id, course_id, lecture_id, title, document, embedding_json,
             timestamp_start, timestamp_end, display_time, video_url, content_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'transcript')
        ''', (
            doc_id, course_id, lecture_id, title, text,
            json.dumps(embedding),
            start_seconds, end_seconds, display_time, video_url
        ))
        self.conn.commit()
        return True

    def delete_lecture_transcript(self, course_id: int, lecture_id: int):
        """Remove all transcript chunks for a lecture (before re-indexing)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM embeddings WHERE course_id=? AND lecture_id=? AND content_type='transcript'",
            (course_id, lecture_id)
        )
        self.conn.commit()

    def query_course_context(self, course_id: int, query_text: str, n_results=5) -> list[dict]:
        """
        Query the vector store and return ranked context chunks with metadata.
        
        Returns:
            List of dicts:
            {
                "title": str,
                "document": str,
                "similarity": float,
                "content_type": "text" | "transcript",
                "timestamp_start": float | None,
                "display_time": str | None,     # "MM:SS"
                "video_url": str | None,
                "lecture_id": int | None,
            }
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM embeddings LIMIT 1")
        if not cursor.fetchone():
            return []

        try:
            query_embedding = genai.embed_content(
                model="models/gemini-embedding-001",
                content=query_text,
                task_type="retrieval_query"
            )['embedding']
            q_vec = np.array(query_embedding)
            
            cursor.execute(
                """SELECT lecture_id, title, document, embedding_json,
                          timestamp_start, timestamp_end, display_time, video_url, content_type
                   FROM embeddings WHERE course_id = ?""",
                (course_id,)
            )
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                (lec_id, title, document, emb_json,
                 ts_start, ts_end, disp_time, vid_url, c_type) = row
                doc_vec = np.array(json.loads(emb_json))
                sim = self._cosine_similarity(q_vec, doc_vec)
                results.append({
                    "similarity": sim,
                    "title": title,
                    "document": document,
                    "content_type": c_type or "text",
                    "timestamp_start": ts_start,
                    "timestamp_end": ts_end,
                    "display_time": disp_time,
                    "video_url": vid_url,
                    "lecture_id": lec_id,
                })
                
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:n_results]

        except Exception as e:
            print(f"Query error: {e}")
            return []

    def query_course_context_as_text(self, course_id: int, query_text: str, n_results=4) -> str:
        """
        Legacy plain-text version — kept for backward compatibility.
        Returns formatted string without timestamp info.
        """
        results = self.query_course_context(course_id, query_text, n_results)
        if not results:
            return ""
        blocks = [f"--- Context from '{r['title']}' ---\n{r['document']}" for r in results]
        return "\n\n".join(blocks)


def get_vector_store():
    return CourseVectorStore()
