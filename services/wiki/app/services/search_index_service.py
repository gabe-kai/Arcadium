"""Search index service for wiki pages"""

import re
import uuid
from typing import Dict, List, Optional

from app import db
from app.models.index_entry import IndexEntry
from app.models.page import Page
from app.utils.markdown_service import parse_frontmatter


class SearchIndexService:
    """Service for managing search indexing of wiki pages"""

    @staticmethod
    def index_page(
        page_id: uuid.UUID, content: str, title: str = None
    ) -> List[IndexEntry]:
        """
        Index a page for search (full-text and keywords).
        Removes old index entries and creates new ones.

        Args:
            page_id: ID of the page to index
            content: Markdown content of the page
            title: Optional page title (if not provided, will fetch from page)

        Returns:
            List of created IndexEntry instances
        """
        # Get page if title not provided
        if not title:
            page = db.session.get(Page, page_id)
            if not page:
                raise ValueError(f"Page not found: {page_id}")
            title = page.title

        # Remove old index entries
        IndexEntry.query.filter_by(page_id=page_id).delete()

        # Parse frontmatter if present
        frontmatter, markdown_content = parse_frontmatter(content)

        # Combine title and content for indexing
        full_text = f"{title}\n{markdown_content}"

        # Create full-text index entries
        fulltext_entries = SearchIndexService._create_fulltext_entries(
            page_id, full_text
        )

        # Extract and create keyword entries
        keyword_entries = SearchIndexService._create_keyword_entries(page_id, full_text)

        # Get manual keywords from frontmatter
        manual_keywords = frontmatter.get("keywords", [])
        if isinstance(manual_keywords, str):
            manual_keywords = [k.strip() for k in manual_keywords.split(",")]

        manual_entries = SearchIndexService._create_manual_keyword_entries(
            page_id, manual_keywords
        )

        # Combine all entries
        all_entries = fulltext_entries + keyword_entries + manual_entries

        # Save to database
        for entry in all_entries:
            db.session.add(entry)
        db.session.commit()

        return all_entries

    @staticmethod
    def _create_fulltext_entries(page_id: uuid.UUID, text: str) -> List[IndexEntry]:
        """
        Create full-text index entries from page content.
        Indexes all significant words with their positions.

        Args:
            page_id: ID of the page
            text: Text content to index

        Returns:
            List of IndexEntry instances for full-text search
        """
        entries = []

        # Tokenize text (simple word extraction)
        words = SearchIndexService._tokenize(text)

        # Create index entries for each unique word with context
        word_positions = {}
        for i, word in enumerate(words):
            if word not in word_positions:
                word_positions[word] = []
            word_positions[word].append(i)

        # Create entries with context
        for word, positions in word_positions.items():
            # Get context around first occurrence
            first_pos = positions[0]
            context_start = max(0, first_pos - 5)
            context_end = min(len(words), first_pos + 6)
            context = " ".join(words[context_start:context_end])

            entry = IndexEntry(
                page_id=page_id,
                term=word.lower(),
                context=context,
                position=first_pos,
                is_keyword=False,
                is_manual=False,
            )
            entries.append(entry)

        return entries

    @staticmethod
    def _extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text using simple TF-IDF-like approach.
        For now, uses frequency-based extraction (can be enhanced with TF-IDF later).

        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to extract

        Returns:
            List of extracted keywords
        """
        # Tokenize and count word frequencies
        words = SearchIndexService._tokenize(text)

        # Filter out common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
        }

        # Count word frequencies (excluding stop words and short words)
        word_freq = {}
        for word in words:
            word_lower = word.lower()
            if len(word_lower) > 3 and word_lower not in stop_words:
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

        # Sort by frequency and take top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]

        return keywords

    @staticmethod
    def _create_manual_keyword_entries(
        page_id: uuid.UUID, keywords: List[str]
    ) -> List[IndexEntry]:
        """
        Create index entries for manually tagged keywords.

        Args:
            page_id: ID of the page
            keywords: List of keyword strings

        Returns:
            List of IndexEntry instances for manual keywords
        """
        entries = []

        for keyword in keywords:
            if not keyword or not keyword.strip():
                continue

            keyword = keyword.strip().lower()

            entry = IndexEntry(
                page_id=page_id,
                term=keyword,
                context=f"Manually tagged keyword: {keyword}",
                position=None,  # Keywords don't have positions
                is_keyword=True,
                is_manual=True,
            )
            entries.append(entry)

        return entries

    @staticmethod
    def _create_keyword_entries(page_id: uuid.UUID, text: str) -> List[IndexEntry]:
        """
        Create index entries for auto-extracted keywords.

        Args:
            page_id: ID of the page
            text: Text content to extract keywords from

        Returns:
            List of IndexEntry instances for keywords
        """
        entries = []

        # Extract keywords
        keywords = SearchIndexService._extract_keywords(text)

        for keyword in keywords:
            entry = IndexEntry(
                page_id=page_id,
                term=keyword,
                context=f"Auto-extracted keyword: {keyword}",
                position=None,  # Keywords don't have positions
                is_keyword=True,
                is_manual=False,
            )
            entries.append(entry)

        return entries

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        Tokenize text into words.
        Simple implementation - can be enhanced with NLP libraries later.

        Args:
            text: Text to tokenize

        Returns:
            List of words
        """
        # Remove markdown syntax
        text = re.sub(r"[#*_`\[\]()]", " ", text)
        text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)  # Remove image links
        text = re.sub(r"\[.*?\]\(.*?\)", " ", text)  # Remove regular links

        # Split into words
        words = re.findall(r"\b\w+\b", text.lower())

        return words

    @staticmethod
    def search(
        query: str,
        limit: int = 20,
        section: Optional[str] = None,
        include_drafts: bool = False,
        user_role: str = "viewer",
        user_id: Optional[uuid.UUID] = None,
    ) -> List[Dict]:
        """
        Search pages by query string.
        Uses both full-text and keyword matching.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            section: Optional section filter
            include_drafts: Whether to include draft pages
            user_role: Role of requesting user (for draft filtering)
            user_id: Optional user ID (for draft filtering)

        Returns:
            List of result dictionaries with page info and relevance score
        """
        if not query or not query.strip():
            return []

        query_terms = SearchIndexService._tokenize(query)
        if not query_terms:
            return []

        # Find matching index entries
        # Since tokenize already lowercases both query and indexed terms,
        # we can use exact matching with in_() for multiple terms
        # This is the original approach that should work reliably
        matching_entries = IndexEntry.query.filter(
            IndexEntry.term.in_(query_terms)
        ).all()

        # Group by page and calculate relevance
        page_scores = {}
        for entry in matching_entries:
            page_id = entry.page_id

            if page_id not in page_scores:
                page_scores[page_id] = {"page_id": page_id, "score": 0, "matches": []}

            # Check if this is an exact match or partial match
            entry_term_lower = entry.term.lower()
            is_exact_match = any(entry_term_lower == term for term in query_terms)

            # Calculate score based on match type
            if entry.is_keyword:
                # Keywords are more important
                base_score = 10
            else:
                # Full-text matches
                base_score = 1

            # Boost exact matches
            if is_exact_match:
                page_scores[page_id]["score"] += base_score * 2
            else:
                # Partial match gets lower score
                page_scores[page_id]["score"] += base_score

            page_scores[page_id]["matches"].append(
                {
                    "term": entry.term,
                    "context": entry.context,
                    "is_keyword": entry.is_keyword,
                    "is_manual": entry.is_manual,
                }
            )

        # Sort by score and get top results
        sorted_results = sorted(
            page_scores.values(), key=lambda x: x["score"], reverse=True
        )[:limit]

        # Fetch page details with filtering
        results = []
        for result in sorted_results:
            page = db.session.get(Page, result["page_id"])
            if not page:
                continue

            # Filter by section
            if section and page.section != section:
                continue

            # Filter drafts and archived pages based on permissions
            if page.status == "draft":
                if not include_drafts:
                    continue
                # Check if user can see this draft
                if user_role not in ["writer", "admin"]:
                    continue
                if user_role == "writer" and user_id and page.created_by != user_id:
                    continue

            # Exclude archived pages from search results (they're hidden)
            if page.status == "archived":
                continue

            # Get snippet from first match context
            snippet = ""
            if result["matches"]:
                snippet = result["matches"][0].get("context", "")[:200]

            # Normalize score to 0-1 range for relevance_score
            max_score = (
                max([r["score"] for r in sorted_results]) if sorted_results else 1
            )
            relevance_score = (
                min(result["score"] / max_score, 1.0) if max_score > 0 else 0.0
            )

            results.append(
                {
                    "page_id": str(page.id),
                    "title": page.title,
                    "slug": page.slug,
                    "section": page.section,
                    "status": page.status,
                    "snippet": snippet,
                    "relevance_score": round(relevance_score, 2),
                    "score": result.get("score", 0),
                    "matches": result.get("matches", []),
                }
            )

        return results

    @staticmethod
    def search_by_keyword(keyword: str) -> List[Page]:
        """
        Search pages by specific keyword.

        Args:
            keyword: Keyword to search for

        Returns:
            List of Page instances that have this keyword
        """
        keyword = keyword.lower().strip()

        entries = IndexEntry.query.filter_by(term=keyword, is_keyword=True).all()

        page_ids = {entry.page_id for entry in entries}

        if not page_ids:
            return []

        return Page.query.filter(Page.id.in_(page_ids)).all()

    @staticmethod
    def get_page_keywords(page_id: uuid.UUID) -> List[str]:
        """
        Get all keywords (auto and manual) for a page.

        Args:
            page_id: ID of the page

        Returns:
            List of keyword strings
        """
        entries = IndexEntry.query.filter_by(page_id=page_id, is_keyword=True).all()

        return [entry.term for entry in entries]

    @staticmethod
    def add_manual_keyword(page_id: uuid.UUID, keyword: str) -> IndexEntry:
        """
        Add a manual keyword to a page.

        Args:
            page_id: ID of the page
            keyword: Keyword to add

        Returns:
            Created IndexEntry instance
        """
        keyword = keyword.lower().strip()

        # Check if keyword already exists
        existing = IndexEntry.query.filter_by(
            page_id=page_id, term=keyword, is_keyword=True
        ).first()

        if existing:
            # Update to manual if not already
            if not existing.is_manual:
                existing.is_manual = True
                existing.context = f"Manually tagged keyword: {keyword}"
                db.session.commit()
            return existing

        # Create new entry
        entry = IndexEntry(
            page_id=page_id,
            term=keyword,
            context=f"Manually tagged keyword: {keyword}",
            position=None,
            is_keyword=True,
            is_manual=True,
        )
        db.session.add(entry)
        db.session.commit()

        return entry

    @staticmethod
    def remove_keyword(page_id: uuid.UUID, keyword: str) -> bool:
        """
        Remove a keyword from a page.

        Args:
            page_id: ID of the page
            keyword: Keyword to remove

        Returns:
            True if keyword was removed, False if not found
        """
        keyword = keyword.lower().strip()

        entry = IndexEntry.query.filter_by(
            page_id=page_id, term=keyword, is_keyword=True
        ).first()

        if entry:
            db.session.delete(entry)
            db.session.commit()
            return True

        return False

    @staticmethod
    def reindex_all() -> int:
        """
        Reindex all pages in the database.

        Returns:
            Number of pages reindexed
        """
        pages = Page.query.all()
        count = 0

        for page in pages:
            try:
                SearchIndexService.index_page(page.id, page.content, page.title)
                count += 1
            except Exception as e:
                # Log error but continue
                print(f"Error indexing page {page.id}: {e}")

        return count

    @staticmethod
    def get_index_stats() -> Dict:
        """
        Get statistics about the search index.

        Returns:
            Dictionary with index statistics
        """
        total_entries = IndexEntry.query.count()
        keyword_entries = IndexEntry.query.filter_by(is_keyword=True).count()
        manual_keywords = IndexEntry.query.filter_by(
            is_keyword=True, is_manual=True
        ).count()
        fulltext_entries = IndexEntry.query.filter_by(is_keyword=False).count()
        unique_terms = db.session.query(IndexEntry.term).distinct().count()
        indexed_pages = db.session.query(IndexEntry.page_id).distinct().count()

        return {
            "total_entries": total_entries,
            "keyword_entries": keyword_entries,
            "manual_keywords": manual_keywords,
            "fulltext_entries": fulltext_entries,
            "unique_terms": unique_terms,
            "indexed_pages": indexed_pages,
        }

    @staticmethod
    def get_master_index(
        letter: Optional[str] = None, section: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get master index organized by first letter of page titles.

        Args:
            letter: Optional filter by starting letter (case-insensitive)
            section: Optional filter by section name

        Returns:
            Dictionary with letters as keys and lists of page info as values
        """
        # Build query for pages (exclude archived and drafts)
        query = Page.query.filter_by(status="published")

        # Filter by section if provided
        if section:
            query = query.filter_by(section=section)

        # Get all published pages
        pages = query.order_by(Page.title).all()

        # Organize by first letter
        index = {}
        for page in pages:
            if not page.title:
                continue

            first_letter = page.title[0].upper()

            # Filter by letter if provided
            if letter and first_letter != letter.upper():
                continue

            if first_letter not in index:
                index[first_letter] = []

            index[first_letter].append(
                {
                    "page_id": str(page.id),
                    "title": page.title,
                    "slug": page.slug,
                    "section": page.section,
                }
            )

        return index
