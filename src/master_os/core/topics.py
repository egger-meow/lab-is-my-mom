"""Domain service and command pipeline for Research Topics and Hypothesis Elimination."""
from __future__ import annotations

import json
from typing import Any, Optional

from master_os.core.commands import DomainCommandBus
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore
from master_os.core.models import (
    Topic,
    HypothesisVersion,
    ExplorationPolicy,
    EvidenceLink,
    AdvisorSignal,
    generate_id,
    utc_now,
)


class TopicError(Exception):
    """Base exception for topic domain errors."""


class ConcurrencyConflictError(TopicError):
    """Raised when expected_revision does not match current topic revision."""


class InvalidTransitionError(TopicError):
    """Raised when transition preconditions are not satisfied."""


class PermissionDeniedError(TopicError):
    """Raised when an actor lacks authority for a state transition."""


class TopicCommandService:
    """Manages commands, validations, and optimistic concurrency for Topics."""

    def __init__(
        self,
        db: MasterDatabase,
        commands: DomainCommandBus,
        events: Optional[EventStore] = None,
    ) -> None:
        self.db = db
        self.commands = commands
        self.events = events or EventStore(db)

    def _get_source_id(self) -> str:
        source = self.events.register_source(
            source_type="topic_service",
            name="Research Topic Service",
            external_ref="master-os-topic-service",
            authority_class="user_explicit",
        )
        return source.id

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        row = self.db.fetchone("SELECT * FROM topics WHERE id = ?", (topic_id,))
        if not row:
            return None
        return Topic(
            id=row["id"],
            title=row["title"],
            research_question=row["research_question"],
            status=row["status"],
            revision=row["revision"],
            current_hypothesis_version_id=row["current_hypothesis_version_id"],
            is_primary=bool(row["is_primary"]),
            next_action=row["next_action"],
            blockers=json.loads(row["blockers_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_topics(self) -> list[Topic]:
        rows = self.db.fetchall("SELECT * FROM topics ORDER BY created_at DESC")
        topics = []
        for row in rows:
            topics.append(
                Topic(
                    id=row["id"],
                    title=row["title"],
                    research_question=row["research_question"],
                    status=row["status"],
                    revision=row["revision"],
                    current_hypothesis_version_id=row["current_hypothesis_version_id"],
                    is_primary=bool(row["is_primary"]),
                    next_action=row["next_action"],
                    blockers=json.loads(row["blockers_json"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return topics

    def create_topic_seed(
        self,
        title: str,
        research_question: str,
        source_refs: Optional[list[str]] = None,
        actor: str = "user",
    ) -> Topic:
        topic_id = generate_id("TP-")
        now = utc_now()
        source_id = self._get_source_id()
        payload = {
            "id": topic_id,
            "title": title,
            "research_question": research_question,
            "status": "seed",
            "revision": 1,
            "current_hypothesis_version_id": None,
            "is_primary": False,
            "next_action": "",
            "blockers": [],
            "source_refs": source_refs or [],
            "actor": actor,
            "created_at": now,
            "updated_at": now,
        }
        self.commands.emit(
            event_type="topic.created",
            source_id=source_id,
            payload=payload,
            actor_ref=actor,
            created_by=actor,
        )
        return self.get_topic(topic_id)  # type: ignore

    def add_hypothesis_version(
        self,
        topic_id: str,
        statement: str,
        scope: str = "",
        assumptions: Optional[list[str]] = None,
        source_refs: Optional[list[str]] = None,
        supersedes_id: Optional[str] = None,
        actor: str = "user",
    ) -> HypothesisVersion:
        topic = self.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} does not exist")

        row = self.db.fetchone(
            "SELECT COALESCE(MAX(version), 0) + 1 AS next_v FROM hypothesis_versions WHERE topic_id = ?",
            (topic_id,),
        )
        next_v = row["next_v"] if row else 1

        hyp_id = generate_id("HYP-")
        now = utc_now()
        source_id = self._get_source_id()
        payload = {
            "id": hyp_id,
            "topic_id": topic_id,
            "version": next_v,
            "statement": statement,
            "scope": scope,
            "assumptions": assumptions or [],
            "supersedes_id": supersedes_id,
            "source_refs": source_refs or [],
            "actor": actor,
            "created_at": now,
        }
        self.commands.emit(
            event_type="hypothesis.version_created",
            source_id=source_id,
            payload=payload,
            actor_ref=actor,
            created_by=actor,
        )
        return HypothesisVersion(
            id=hyp_id,
            topic_id=topic_id,
            version=next_v,
            statement=statement,
            scope=scope,
            assumptions=assumptions or [],
            supersedes_id=supersedes_id,
            source_refs=source_refs or [],
            created_at=now,
        )

    def activate_hypothesis_version(
        self,
        topic_id: str,
        version_id: str,
        expected_revision: int,
        actor: str = "user",
    ) -> Topic:
        topic = self.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} does not exist")

        if topic.revision != expected_revision:
            raise ConcurrencyConflictError(
                f"Revision mismatch for topic {topic_id}: current {topic.revision}, expected {expected_revision}"
            )

        hyp_row = self.db.fetchone(
            "SELECT * FROM hypothesis_versions WHERE id = ? AND topic_id = ?",
            (version_id, topic_id),
        )
        if not hyp_row:
            raise ValueError(f"Hypothesis {version_id} does not belong to topic {topic_id}")

        if topic.status in ("selected", "killed") and not actor.startswith("user"):
            raise PermissionDeniedError(
                f"Only human user can activate hypothesis on topic in {topic.status} status"
            )

        new_revision = topic.revision + 1
        source_id = self._get_source_id()
        self.commands.emit(
            event_type="hypothesis.activated",
            source_id=source_id,
            payload={
                "topic_id": topic_id,
                "hypothesis_version_id": version_id,
                "revision": new_revision,
                "actor": actor,
            },
            actor_ref=actor,
            created_by=actor,
        )
        return self.get_topic(topic_id)  # type: ignore

    def revise_policy(
        self,
        topic_id: str,
        hypothesis_version_id: str,
        min_viable_checks: Optional[list[str]] = None,
        falsification_conditions: Optional[list[dict[str, Any]]] = None,
        stop_conditions: Optional[list[dict[str, Any]]] = None,
        budget_caps: Optional[dict[str, Any]] = None,
        actor: str = "user",
    ) -> ExplorationPolicy:
        topic = self.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} does not exist")

        hyp_row = self.db.fetchone(
            "SELECT * FROM hypothesis_versions WHERE id = ? AND topic_id = ?",
            (hypothesis_version_id, topic_id),
        )
        if not hyp_row:
            raise ValueError(f"Hypothesis {hypothesis_version_id} does not belong to topic {topic_id}")

        row = self.db.fetchone(
            "SELECT COALESCE(MAX(version), 0) + 1 AS next_v FROM exploration_policies WHERE topic_id = ? AND hypothesis_version_id = ?",
            (topic_id, hypothesis_version_id),
        )
        next_v = row["next_v"] if row else 1

        policy_id = generate_id("POL-")
        now = utc_now()
        source_id = self._get_source_id()
        payload = {
            "id": policy_id,
            "topic_id": topic_id,
            "hypothesis_version_id": hypothesis_version_id,
            "version": next_v,
            "min_viable_checks": min_viable_checks or [],
            "falsification_conditions": falsification_conditions or [],
            "stop_conditions": stop_conditions or [],
            "budget_caps": budget_caps or {},
            "actor": actor,
            "created_at": now,
        }
        self.commands.emit(
            event_type="topic.policy_revised",
            source_id=source_id,
            payload=payload,
            actor_ref=actor,
            created_by=actor,
        )
        return ExplorationPolicy(
            id=policy_id,
            topic_id=topic_id,
            hypothesis_version_id=hypothesis_version_id,
            version=next_v,
            min_viable_checks=min_viable_checks or [],
            falsification_conditions=falsification_conditions or [],
            stop_conditions=stop_conditions or [],
            budget_caps=budget_caps or {},
            created_at=now,
        )

    def link_evidence(
        self,
        topic_id: str,
        hypothesis_version_id: str,
        stance: str = "inconclusive",
        validation_status: str = "under_review",
        limitations: str = "",
        reason: str = "",
        source_refs: Optional[list[str]] = None,
        finding_id: Optional[str] = None,
        attempt_id: Optional[str] = None,
        supersedes_id: Optional[str] = None,
        actor: str = "user",
    ) -> EvidenceLink:
        topic = self.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} does not exist")

        hyp_row = self.db.fetchone(
            "SELECT * FROM hypothesis_versions WHERE id = ? AND topic_id = ?",
            (hypothesis_version_id, topic_id),
        )
        if not hyp_row:
            raise ValueError(f"Hypothesis {hypothesis_version_id} does not belong to topic {topic_id}")

        evidence_id = generate_id("EVL-")
        now = utc_now()
        source_id = self._get_source_id()
        payload = {
            "id": evidence_id,
            "topic_id": topic_id,
            "hypothesis_version_id": hypothesis_version_id,
            "source_refs": source_refs or [],
            "finding_id": finding_id,
            "attempt_id": attempt_id,
            "stance": stance,
            "validation_status": validation_status,
            "limitations": limitations,
            "reason": reason,
            "supersedes_id": supersedes_id,
            "actor": actor,
            "created_at": now,
        }
        self.commands.emit(
            event_type="evidence.linked",
            source_id=source_id,
            payload=payload,
            actor_ref=actor,
            created_by=actor,
        )
        return EvidenceLink(
            id=evidence_id,
            topic_id=topic_id,
            hypothesis_version_id=hypothesis_version_id,
            source_refs=source_refs or [],
            finding_id=finding_id,
            attempt_id=attempt_id,
            stance=stance,
            validation_status=validation_status,
            limitations=limitations,
            reason=reason,
            supersedes_id=supersedes_id,
            created_at=now,
        )

    def review_evidence(
        self,
        evidence_id: str,
        validation_status: str,
        reason: str = "",
        actor: str = "user",
    ) -> EvidenceLink:
        row = self.db.fetchone("SELECT * FROM evidence_links WHERE id = ?", (evidence_id,))
        if not row:
            raise ValueError(f"EvidenceLink {evidence_id} not found")

        source_id = self._get_source_id()
        payload = {
            "evidence_id": evidence_id,
            "validation_status": validation_status,
            "reason": reason,
            "actor": actor,
        }
        self.commands.emit(
            event_type="evidence.reviewed",
            source_id=source_id,
            payload=payload,
            actor_ref=actor,
            created_by=actor,
        )
        updated = self.db.fetchone("SELECT * FROM evidence_links WHERE id = ?", (evidence_id,))
        return EvidenceLink(
            id=updated["id"],
            topic_id=updated["topic_id"],
            hypothesis_version_id=updated["hypothesis_version_id"],
            source_refs=json.loads(updated["source_refs_json"]),
            finding_id=updated["finding_id"],
            attempt_id=updated["attempt_id"],
            stance=updated["stance"],
            validation_status=updated["validation_status"],
            limitations=updated["limitations"],
            reason=updated["reason"],
            supersedes_id=updated["supersedes_id"],
            created_at=updated["created_at"],
        )

    def set_primary_topic(self, topic_id: str, actor: str = "user") -> None:
        topic = self.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} does not exist")
        source_id = self._get_source_id()
        self.commands.emit(
            event_type="topic.primary_changed",
            source_id=source_id,
            payload={"topic_id": topic_id, "actor": actor},
            actor_ref=actor,
            created_by=actor,
        )

    def transition_status(
        self,
        topic_id: str,
        target_status: str,
        expected_revision: int,
        actor: str = "user",
        rationale: str = "",
        restart_conditions: str = "",
    ) -> Topic:
        topic = self.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} does not exist")

        if topic.revision != expected_revision:
            raise ConcurrencyConflictError(
                f"Revision mismatch for topic {topic_id}: current {topic.revision}, expected {expected_revision}"
            )

        # 1. Authority gate
        is_user = actor.startswith("user")
        if (target_status in ("selected", "killed") or topic.status == "selected") and not is_user:
            raise PermissionDeniedError(
                f"Only human user can transition topic to/from selected or killed (actor: {actor})"
            )

        # 2. Stage transition matrix & preconditions
        valid_statuses = {"seed", "exploring", "viable", "candidate", "selected", "killed"}
        if target_status not in valid_statuses:
            raise InvalidTransitionError(f"Invalid target status: {target_status}")

        if target_status == topic.status:
            return topic

        # Precondition checks
        if target_status == "exploring":
            if not topic.current_hypothesis_version_id:
                raise InvalidTransitionError("Transition to exploring requires active hypothesis version")
            policy_row = self.db.fetchone(
                "SELECT * FROM exploration_policies WHERE topic_id = ? AND hypothesis_version_id = ?",
                (topic_id, topic.current_hypothesis_version_id),
            )
            if not policy_row:
                raise InvalidTransitionError("Transition to exploring requires exploration policy")
            checks = json.loads(policy_row["min_viable_checks_json"])
            if not checks:
                raise InvalidTransitionError("Exploration policy requires at least one min_viable_check")

        elif target_status == "viable":
            if not topic.current_hypothesis_version_id:
                raise InvalidTransitionError("Transition to viable requires active hypothesis version")
            # Must have at least 1 validated supporting evidence link
            evidence_rows = self.db.fetchall(
                """SELECT * FROM evidence_links
                   WHERE topic_id = ? AND hypothesis_version_id = ?
                     AND stance = 'supports' AND validation_status = 'validated'""",
                (topic_id, topic.current_hypothesis_version_id),
            )
            if not evidence_rows:
                raise InvalidTransitionError(
                    "Transition to viable requires at least one validated supporting evidence link"
                )

        elif target_status == "candidate":
            if topic.status != "viable":
                raise InvalidTransitionError("Candidate status can only be reached from viable")
            # Verify hypothesis statement and scope
            hyp = self.db.fetchone(
                "SELECT * FROM hypothesis_versions WHERE id = ?",
                (topic.current_hypothesis_version_id,),
            )
            if not hyp or not hyp["statement"]:
                raise InvalidTransitionError("Candidate status requires hypothesis statement")

        elif target_status == "selected":
            if topic.status != "candidate":
                raise InvalidTransitionError("Selected status can only be reached from candidate")
            if not rationale.strip():
                raise InvalidTransitionError("Transition to selected requires rationale")

        elif target_status == "killed":
            if not rationale.strip():
                raise InvalidTransitionError("Transition to killed requires rationale / stop reason")

        new_revision = topic.revision + 1
        source_id = self._get_source_id()
        self.commands.emit(
            event_type="topic.transitioned",
            source_id=source_id,
            payload={
                "topic_id": topic_id,
                "from_status": topic.status,
                "to_status": target_status,
                "revision": new_revision,
                "actor": actor,
                "rationale": rationale,
                "restart_conditions": restart_conditions,
            },
            actor_ref=actor,
            created_by=actor,
        )
        return self.get_topic(topic_id)  # type: ignore
