"""
Validation Performance Optimizer

Phase 16: Performance & Optimization (Points 221-230)
- Parallel validation execution
- Caching for document text and LLM responses
- Cost optimization through model selection
- Incremental validation support

Usage:
    optimizer = ValidationOptimizer(api_key)
    results = await optimizer.run_parallel_validation(facts, document_text)
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import time

from config_v2 import (
    VALIDATION_MODEL,
    CATEGORY_VALIDATION_MODEL,
    VALIDATION_CACHE_TTL,
    VALIDATION_STORAGE_DIR,
    MAX_PARALLEL_AGENTS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CACHING (Points 225-227)
# =============================================================================

@dataclass
class CacheEntry:
    """Cache entry with TTL support."""
    key: str
    value: Any
    created_at: datetime
    ttl_seconds: int
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)


class ValidationCache:
    """
    Cache for validation results to avoid redundant LLM calls.

    Caches:
    - Document text parsing results
    - LLM responses for identical prompts
    - Evidence verification results
    """

    def __init__(self, ttl_seconds: int = VALIDATION_CACHE_TTL):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            self._stats["misses"] += 1
            return None

        entry = self._cache[key]

        if entry.is_expired:
            del self._cache[key]
            self._stats["evictions"] += 1
            self._stats["misses"] += 1
            return None

        entry.hit_count += 1
        self._stats["hits"] += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache."""
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            ttl_seconds=ttl_seconds or self.ttl_seconds,
        )

    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl_seconds: Optional[int] = None
    ) -> Any:
        """Get from cache or compute and cache."""
        value = self.get(key)
        if value is not None:
            return value

        value = compute_fn()
        self.set(key, value, ttl_seconds)
        return value

    async def get_or_compute_async(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl_seconds: Optional[int] = None
    ) -> Any:
        """Async version of get_or_compute."""
        value = self.get(key)
        if value is not None:
            return value

        if asyncio.iscoroutinefunction(compute_fn):
            value = await compute_fn()
        else:
            value = compute_fn()

        self.set(key, value, ttl_seconds)
        return value

    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all entries matching pattern prefix."""
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(pattern)]
        for key in keys_to_remove:
            del self._cache[key]
        return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired_keys:
            del self._cache[key]
        self._stats["evictions"] += len(expired_keys)
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "entries": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": hit_rate,
        }


# =============================================================================
# PARALLEL VALIDATION (Points 221-224)
# =============================================================================

@dataclass
class ValidationTask:
    """A validation task to run."""
    task_id: str
    task_type: str  # "evidence", "category", "domain", "cross_domain", "adversarial"
    domain: Optional[str] = None
    category: Optional[str] = None
    facts: List[Dict] = field(default_factory=list)
    document_text: str = ""
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0  # Higher = more important


@dataclass
class ValidationTaskResult:
    """Result from a validation task."""
    task_id: str
    task_type: str
    success: bool
    result: Any
    duration_ms: float
    model_used: str
    tokens_used: int = 0
    cost_estimate: float = 0.0
    error: Optional[str] = None


class ParallelValidator:
    """
    Runs validation tasks in parallel with dependency management.

    Execution order:
    1. Evidence verification (parallel across all facts)
    2. Category validators (parallel across categories)
    3. Domain validation (after categories complete)
    4. Cross-domain (after all domains complete)
    5. Adversarial review (only if domain passed)
    """

    def __init__(
        self,
        api_key: str,
        max_parallel: int = MAX_PARALLEL_AGENTS,
        cache: Optional[ValidationCache] = None
    ):
        self.api_key = api_key
        self.max_parallel = max_parallel
        self.cache = cache or ValidationCache()
        self._semaphore = asyncio.Semaphore(max_parallel)
        self._results: Dict[str, ValidationTaskResult] = {}

    async def run_validation_pipeline(
        self,
        facts: List[Dict],
        document_text: str,
        domains: List[str],
        run_adversarial: bool = True,
        run_cross_domain: bool = True,
    ) -> Dict[str, ValidationTaskResult]:
        """
        Run full validation pipeline with proper ordering.

        Returns dict of task_id -> ValidationTaskResult
        """
        self._results.clear()

        # Phase 1: Evidence verification (parallel)
        logger.info("Starting Phase 1: Evidence verification")
        evidence_tasks = self._create_evidence_tasks(facts, document_text)
        await self._run_tasks_parallel(evidence_tasks)

        # Phase 2: Category validators (parallel per domain)
        logger.info("Starting Phase 2: Category validation")
        for domain in domains:
            domain_facts = [f for f in facts if f.get("domain") == domain]
            category_tasks = self._create_category_tasks(domain, domain_facts, document_text)
            await self._run_tasks_parallel(category_tasks)

        # Phase 3: Domain validation (sequential per domain, parallel across domains)
        logger.info("Starting Phase 3: Domain validation")
        domain_tasks = self._create_domain_tasks(domains, facts, document_text)
        await self._run_tasks_parallel(domain_tasks)

        # Phase 4: Cross-domain (after all domains)
        if run_cross_domain:
            logger.info("Starting Phase 4: Cross-domain validation")
            cross_domain_task = self._create_cross_domain_task(facts, document_text)
            await self._run_task(cross_domain_task)

        # Phase 5: Adversarial review (only if domains passed)
        if run_adversarial:
            # Check if any domains failed
            domain_results = [
                r for task_id, r in self._results.items()
                if r.task_type == "domain"
            ]
            domains_passed = all(
                r.success and r.result.get("requires_rerun", False) is False
                for r in domain_results
            )

            if domains_passed:
                logger.info("Starting Phase 5: Adversarial review")
                adversarial_tasks = self._create_adversarial_tasks(domains, facts, document_text)
                await self._run_tasks_parallel(adversarial_tasks)
            else:
                logger.info("Skipping adversarial review - domain validation requires rerun")

        return self._results

    def _create_evidence_tasks(
        self,
        facts: List[Dict],
        document_text: str
    ) -> List[ValidationTask]:
        """Create evidence verification tasks."""
        return [
            ValidationTask(
                task_id=f"evidence_{f.get('fact_id', i)}",
                task_type="evidence",
                facts=[f],
                document_text=document_text,
                priority=1,
            )
            for i, f in enumerate(facts)
            if f.get("evidence", {}).get("exact_quote")
        ]

    def _create_category_tasks(
        self,
        domain: str,
        facts: List[Dict],
        document_text: str
    ) -> List[ValidationTask]:
        """Create category validation tasks."""
        categories = set(f.get("category") for f in facts if f.get("category"))

        return [
            ValidationTask(
                task_id=f"category_{domain}_{cat}",
                task_type="category",
                domain=domain,
                category=cat,
                facts=[f for f in facts if f.get("category") == cat],
                document_text=document_text,
                priority=2,
            )
            for cat in categories
        ]

    def _create_domain_tasks(
        self,
        domains: List[str],
        facts: List[Dict],
        document_text: str
    ) -> List[ValidationTask]:
        """Create domain validation tasks."""
        return [
            ValidationTask(
                task_id=f"domain_{domain}",
                task_type="domain",
                domain=domain,
                facts=[f for f in facts if f.get("domain") == domain],
                document_text=document_text,
                dependencies=[
                    f"category_{domain}_{f.get('category')}"
                    for f in facts
                    if f.get("domain") == domain and f.get("category")
                ],
                priority=3,
            )
            for domain in domains
        ]

    def _create_cross_domain_task(
        self,
        facts: List[Dict],
        document_text: str
    ) -> ValidationTask:
        """Create cross-domain validation task."""
        return ValidationTask(
            task_id="cross_domain",
            task_type="cross_domain",
            facts=facts,
            document_text=document_text,
            dependencies=[f"domain_{d}" for d in set(f.get("domain") for f in facts)],
            priority=4,
        )

    def _create_adversarial_tasks(
        self,
        domains: List[str],
        facts: List[Dict],
        document_text: str
    ) -> List[ValidationTask]:
        """Create adversarial review tasks."""
        return [
            ValidationTask(
                task_id=f"adversarial_{domain}",
                task_type="adversarial",
                domain=domain,
                facts=[f for f in facts if f.get("domain") == domain],
                document_text=document_text,
                dependencies=[f"domain_{domain}"],
                priority=5,
            )
            for domain in domains
        ]

    async def _run_tasks_parallel(self, tasks: List[ValidationTask]) -> None:
        """Run tasks in parallel respecting semaphore limit."""
        await asyncio.gather(*[self._run_task(task) for task in tasks])

    async def _run_task(self, task: ValidationTask) -> ValidationTaskResult:
        """Run a single validation task."""
        async with self._semaphore:
            start_time = time.time()

            # Check cache first
            cache_key = self._get_cache_key(task)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for task {task.task_id}")
                self._results[task.task_id] = cached
                return cached

            try:
                # Execute based on task type
                if task.task_type == "evidence":
                    result = await self._run_evidence_verification(task)
                elif task.task_type == "category":
                    result = await self._run_category_validation(task)
                elif task.task_type == "domain":
                    result = await self._run_domain_validation(task)
                elif task.task_type == "cross_domain":
                    result = await self._run_cross_domain_validation(task)
                elif task.task_type == "adversarial":
                    result = await self._run_adversarial_review(task)
                else:
                    raise ValueError(f"Unknown task type: {task.task_type}")

                duration_ms = (time.time() - start_time) * 1000

                task_result = ValidationTaskResult(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    success=True,
                    result=result,
                    duration_ms=duration_ms,
                    model_used=self._get_model_for_task(task),
                )

            except Exception as e:
                logger.error(f"Task {task.task_id} failed: {e}")
                duration_ms = (time.time() - start_time) * 1000

                task_result = ValidationTaskResult(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    success=False,
                    result=None,
                    duration_ms=duration_ms,
                    model_used=self._get_model_for_task(task),
                    error=str(e),
                )

            # Cache successful results
            if task_result.success:
                self.cache.set(cache_key, task_result)

            self._results[task.task_id] = task_result
            return task_result

    def _get_cache_key(self, task: ValidationTask) -> str:
        """Generate cache key for a task."""
        key_data = {
            "type": task.task_type,
            "domain": task.domain,
            "category": task.category,
            "fact_ids": [f.get("fact_id") for f in task.facts],
            "doc_hash": hashlib.md5(task.document_text.encode()).hexdigest()[:8],
        }
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:16]

    def _get_model_for_task(self, task: ValidationTask) -> str:
        """Get appropriate model for task type (cost optimization)."""
        # Use Haiku for category checkpoints (cheaper)
        if task.task_type == "category":
            return CATEGORY_VALIDATION_MODEL

        # Use Sonnet for domain/cross-domain/adversarial (more thorough)
        return VALIDATION_MODEL

    async def _run_evidence_verification(self, task: ValidationTask) -> Dict:
        """Run evidence verification (no LLM needed)."""
        from tools_v2.evidence_verifier import verify_quote_exists

        fact = task.facts[0]
        quote = fact.get("evidence", {}).get("exact_quote", "")

        if not quote:
            return {"status": "no_evidence", "match_score": 0.0}

        result = verify_quote_exists(quote, task.document_text)

        return {
            "status": result.status,
            "match_score": result.match_score,
            "matched_text": result.matched_text,
        }

    async def _run_category_validation(self, task: ValidationTask) -> Dict:
        """Run category validation."""
        # Placeholder - actual implementation would use CategoryValidator
        return {
            "is_complete": True,
            "confidence": 0.85,
            "missing_items": [],
        }

    async def _run_domain_validation(self, task: ValidationTask) -> Dict:
        """Run domain validation."""
        # Placeholder - actual implementation would use DomainValidator
        return {
            "completeness_score": 0.9,
            "requires_rerun": False,
            "inconsistencies": [],
        }

    async def _run_cross_domain_validation(self, task: ValidationTask) -> Dict:
        """Run cross-domain validation."""
        # Placeholder - actual implementation would use CrossDomainValidator
        return {
            "is_consistent": True,
            "checks": [],
            "llm_findings": [],
        }

    async def _run_adversarial_review(self, task: ValidationTask) -> Dict:
        """Run adversarial review."""
        # Placeholder - actual implementation would use AdversarialReviewer
        return {
            "findings": [],
            "overall_assessment": "No major issues found",
        }


# =============================================================================
# COST OPTIMIZATION (Points 228-230)
# =============================================================================

@dataclass
class CostEstimate:
    """Cost estimate for validation run."""
    total_cost: float
    breakdown: Dict[str, float]
    tokens_used: Dict[str, int]
    model_usage: Dict[str, int]


class CostOptimizer:
    """
    Optimizes validation costs through:
    - Using Haiku for category checkpoints
    - Using Sonnet only for domain/adversarial
    - Skipping adversarial if major issues found
    """

    # Cost per 1M tokens (approximate)
    MODEL_COSTS = {
        "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25},
        "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    }

    def __init__(self):
        self._usage_log: List[Dict] = []

    def log_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_type: str
    ) -> float:
        """Log model usage and return cost estimate."""
        if model not in self.MODEL_COSTS:
            return 0.0

        costs = self.MODEL_COSTS[model]
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        total_cost = input_cost + output_cost

        self._usage_log.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "task_type": task_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": total_cost,
        })

        return total_cost

    def get_cost_estimate(self) -> CostEstimate:
        """Get total cost estimate from usage log."""
        total_cost = 0.0
        breakdown = {}
        tokens_used = {"input": 0, "output": 0}
        model_usage = {}

        for entry in self._usage_log:
            total_cost += entry["cost"]
            task_type = entry["task_type"]
            breakdown[task_type] = breakdown.get(task_type, 0) + entry["cost"]
            tokens_used["input"] += entry["input_tokens"]
            tokens_used["output"] += entry["output_tokens"]
            model = entry["model"]
            model_usage[model] = model_usage.get(model, 0) + 1

        return CostEstimate(
            total_cost=total_cost,
            breakdown=breakdown,
            tokens_used=tokens_used,
            model_usage=model_usage,
        )

    def should_skip_adversarial(
        self,
        domain_results: Dict[str, Any]
    ) -> bool:
        """
        Check if adversarial review should be skipped.

        Skip if:
        - Domain validation requires rerun (major issues found)
        - Completeness score is very low
        """
        for domain, result in domain_results.items():
            if result.get("requires_rerun", False):
                logger.info(f"Skipping adversarial for {domain} - requires rerun")
                return True

            if result.get("completeness_score", 1.0) < 0.5:
                logger.info(f"Skipping adversarial for {domain} - low completeness")
                return True

        return False

    def select_model(self, task_type: str, complexity: str = "normal") -> str:
        """
        Select appropriate model based on task type and complexity.

        Cost optimization strategy:
        - category: Always Haiku (simple checks)
        - evidence: No LLM needed
        - domain: Sonnet for thorough review
        - adversarial: Sonnet (needs sophisticated reasoning)
        - cross_domain: Sonnet (complex multi-domain analysis)
        """
        if task_type == "category":
            return CATEGORY_VALIDATION_MODEL
        elif task_type == "evidence":
            return "none"  # No LLM needed
        else:
            return VALIDATION_MODEL


# =============================================================================
# INCREMENTAL VALIDATION (Point 227)
# =============================================================================

class IncrementalValidator:
    """
    Supports incremental validation for large documents.

    Only re-validates:
    - New facts
    - Modified facts
    - Facts with unresolved flags
    """

    def __init__(self, cache: ValidationCache):
        self.cache = cache
        self._validated_facts: Dict[str, str] = {}  # fact_id -> hash of content

    def get_facts_needing_validation(
        self,
        facts: List[Dict],
        force_revalidate: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get list of facts that need validation.

        Returns facts that are:
        - New (not previously validated)
        - Modified (content hash changed)
        - In force_revalidate list
        """
        needs_validation = []
        force_set = set(force_revalidate or [])

        for fact in facts:
            fact_id = fact.get("fact_id")
            content_hash = self._compute_fact_hash(fact)

            # Force revalidate
            if fact_id in force_set:
                needs_validation.append(fact)
                continue

            # New fact
            if fact_id not in self._validated_facts:
                needs_validation.append(fact)
                continue

            # Modified fact
            if self._validated_facts[fact_id] != content_hash:
                needs_validation.append(fact)
                continue

        logger.info(
            f"Incremental validation: {len(needs_validation)}/{len(facts)} facts need validation"
        )

        return needs_validation

    def mark_validated(self, fact: Dict) -> None:
        """Mark a fact as validated."""
        fact_id = fact.get("fact_id")
        content_hash = self._compute_fact_hash(fact)
        self._validated_facts[fact_id] = content_hash

    def _compute_fact_hash(self, fact: Dict) -> str:
        """Compute hash of fact content for change detection."""
        # Hash key fields that affect validation
        key_fields = {
            "item": fact.get("item"),
            "details": fact.get("details"),
            "evidence": fact.get("evidence"),
        }
        return hashlib.md5(json.dumps(key_fields, sort_keys=True).encode()).hexdigest()


# =============================================================================
# VALIDATION OPTIMIZER (Main Entry Point)
# =============================================================================

class ValidationOptimizer:
    """
    Main entry point for optimized validation.

    Combines:
    - Parallel execution
    - Caching
    - Cost optimization
    - Incremental validation
    """

    def __init__(self, api_key: str, max_parallel: int = MAX_PARALLEL_AGENTS):
        self.cache = ValidationCache()
        self.parallel_validator = ParallelValidator(api_key, max_parallel, self.cache)
        self.cost_optimizer = CostOptimizer()
        self.incremental_validator = IncrementalValidator(self.cache)

    async def validate(
        self,
        facts: List[Dict],
        document_text: str,
        domains: List[str],
        incremental: bool = True,
        force_revalidate: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run optimized validation pipeline.

        Args:
            facts: List of facts to validate
            document_text: Source document text
            domains: List of domains to validate
            incremental: Use incremental validation (skip unchanged facts)
            force_revalidate: List of fact IDs to force revalidate

        Returns:
            Validation results with cost estimate
        """
        start_time = time.time()

        # Incremental: only validate changed facts
        if incremental:
            facts_to_validate = self.incremental_validator.get_facts_needing_validation(
                facts, force_revalidate
            )
        else:
            facts_to_validate = facts

        # Skip adversarial if not needed (cost optimization)
        run_adversarial = True  # Will be set based on domain results

        # Run parallel validation
        results = await self.parallel_validator.run_validation_pipeline(
            facts_to_validate,
            document_text,
            domains,
            run_adversarial=run_adversarial,
            run_cross_domain=True,
        )

        # Mark validated facts
        for fact in facts_to_validate:
            self.incremental_validator.mark_validated(fact)

        # Calculate cost
        cost_estimate = self.cost_optimizer.get_cost_estimate()

        duration_ms = (time.time() - start_time) * 1000

        return {
            "results": results,
            "cost_estimate": cost_estimate,
            "duration_ms": duration_ms,
            "facts_validated": len(facts_to_validate),
            "facts_skipped": len(facts) - len(facts_to_validate),
            "cache_stats": self.cache.get_stats(),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        return {
            "cache": self.cache.get_stats(),
            "cost": self.cost_optimizer.get_cost_estimate().__dict__,
        }
