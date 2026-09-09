import json
from pathlib import Path
from typing import Dict, Any, List

from app.core.config import settings
from app.core.logging import logger
from app.rag.hybrid_retriever import HybridRetriever


class RAGEvaluator:
    """
    Offline quantitative evaluator for retrieval accuracy and citation correctness.
    Measures Recall@1, Recall@3, Recall@5, MRR, and groundedness without external cloud LLMs.
    """

    def __init__(self, retriever: HybridRetriever, golden_dataset_path: str = "data/golden_qa.json"):
        self.retriever = retriever
        self.dataset_path = settings.resolve_path(golden_dataset_path)

    def evaluate(self) -> Dict[str, Any]:
        """Runs complete evaluation against the golden test suite."""
        if not self.dataset_path.exists():
            logger.error(f"Golden dataset not found at {self.dataset_path}")
            return {"error": "Dataset missing"}

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            test_cases = json.load(f)

        total_cases = len(test_cases)
        recall_at_1 = 0
        recall_at_3 = 0
        recall_at_5 = 0
        reciprocal_ranks = []
        source_matches = 0
        keyword_coverages = []

        details = []

        for case in test_cases:
            q_id = case["id"]
            question = case["question"]
            expected_topic = case["expected_topic"].lower()
            expected_source = case.get("expected_source", "")
            expected_keywords = [k.lower() for k in case.get("expected_keywords", [])]

            # Query retriever top 5
            retrieved = self.retriever.retrieve(question, top_k=5)

            found_rank = 0
            retrieved_titles = []
            retrieved_sources = []
            aggregated_text = ""

            for rank_idx, r in enumerate(retrieved, start=1):
                title = r["title"].lower()
                summary = r["summary"].lower()
                retrieved_titles.append(r["title"])
                retrieved_sources.append(r["source"])
                aggregated_text += f" {title} {summary}"

                # Check if expected topic matches in title or first line
                if expected_topic in title or expected_topic in summary[:120]:
                    if found_rank == 0:
                        found_rank = rank_idx

            # Track recalls
            if found_rank == 1:
                recall_at_1 += 1
            if 1 <= found_rank <= 3:
                recall_at_3 += 1
            if 1 <= found_rank <= 5:
                recall_at_5 += 1

            # Reciprocal rank
            rr = 1.0 / found_rank if found_rank > 0 else 0.0
            reciprocal_ranks.append(rr)

            # Check source authority matching
            if expected_source and expected_source in retrieved_sources[:found_rank if found_rank > 0 else 1]:
                source_matches += 1

            # Keyword groundedness coverage
            matched_kw = sum(1 for kw in expected_keywords if kw in aggregated_text)
            coverage = (matched_kw / len(expected_keywords)) if expected_keywords else 1.0
            keyword_coverages.append(coverage)

            details.append({
                "id": q_id,
                "question": question,
                "expected_topic": expected_topic,
                "found_rank": found_rank,
                "top_retrieved": retrieved_titles[:3],
                "keyword_coverage": round(coverage, 2)
            })

        metrics = {
            "total_queries": total_cases,
            "recall_at_1": round(recall_at_1 / total_cases, 4) if total_cases > 0 else 0.0,
            "recall_at_3": round(recall_at_3 / total_cases, 4) if total_cases > 0 else 0.0,
            "recall_at_5": round(recall_at_5 / total_cases, 4) if total_cases > 0 else 0.0,
            "mrr": round(sum(reciprocal_ranks) / total_cases, 4) if total_cases > 0 else 0.0,
            "mean_groundedness": round(sum(keyword_coverages) / total_cases, 4) if total_cases > 0 else 0.0,
            "source_citation_accuracy": round(source_matches / total_cases, 4) if total_cases > 0 else 0.0,
            "details": details
        }

        logger.info(
            f"RAG Evaluation Results: Recall@1={metrics['recall_at_1']:.2f}, "
            f"Recall@5={metrics['recall_at_5']:.2f}, MRR={metrics['mrr']:.2f}, "
            f"Groundedness={metrics['mean_groundedness']:.2f}"
        )
        return metrics


if __name__ == "__main__":
    retriever = HybridRetriever()
    evaluator = RAGEvaluator(retriever)
    report = evaluator.evaluate()
    print(json.dumps(report, indent=2))
