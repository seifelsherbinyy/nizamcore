"""
Activity merge strategy for knowledge index refresh.

Provides merge_activity_into_index() function that safely merges new activity from Drive
into persona indices while preserving stalled_work[] and completions[].

Design principles:
1. New topics added to topics[] with status "active" if not already present
2. Existing topics: Update last_activity timestamp only if newer (never backdate)
3. Completed topics: Preserve in completions[]; never move back to topics[] even if new activity appears
4. Stalled work: Update days_stalled by recalculating from stalled_since, preserve original stalled_since timestamp
5. Activity history: Append new events in chronological order (never overwrite)
6. Post-merge validation: Call validate_index_schema() to ensure integrity

Functions:
    merge_activity_into_index(index, activity_data, persona): Merge activity into index
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from HIKMAH__knowledge_index.index.schema import validate_index_schema


def merge_activity_into_index(index: Dict, activity_data: Dict, persona: str) -> Dict:
    """
    Safely merge new activity from Drive into persona index.

    Implements 5 merge rules:
    1. New topics: Add to topics[] with status "active" if not already present
    2. Existing topics: Update last_activity timestamp only if newer (don't backdate)
    3. Completed topics: Preserve in completions[]; DO NOT move back to topics[] even if new activity appears
    4. Stalled work: Update days_stalled by recalculating from stalled_since, preserve original stalled_since timestamp
    5. Activity history: Append new events in chronological order (never overwrite)

    Args:
        index: Current PersonaIndexDict for this persona
        activity_data: New activity from Drive (dict with 'topics' and 'events' keys)
        persona: Persona name (for validation)

    Returns:
        Updated index dict (with merged activity)

    Raises:
        ValueError: If post-merge validation fails

    Example:
        >>> index = {"version": "1.0", "persona": "AMMAR", "topics": [], ...}
        >>> activity = {"topics": [{"id": "...", "name": "New Topic", ...}], "events": [...]}
        >>> updated = merge_activity_into_index(index, activity, "AMMAR")
    """

    # Create a deep copy to avoid mutating original
    merged_index = {
        "version": index.get("version"),
        "persona": index.get("persona"),
        "initialized_at": index.get("initialized_at"),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "topics": list(index.get("topics", [])),
        "completions": list(index.get("completions", [])),
        "activity_history": list(index.get("activity_history", [])),
        "stalled_work": list(index.get("stalled_work", [])),
        "context_snapshots": list(index.get("context_snapshots", [])),
        "metadata": dict(index.get("metadata", {}))
    }

    # Handle empty activity gracefully
    if not activity_data or not isinstance(activity_data, dict):
        is_valid, error_msg = validate_index_schema(merged_index)
        if not is_valid:
            raise ValueError(f"Schema validation failed after merge: {error_msg}")
        return merged_index

    # Merge new topics (Rule 1 & 2)
    new_topics = activity_data.get("topics", [])
    existing_topic_ids = {topic.get("id") for topic in merged_index["topics"]}
    completed_topic_ids = {comp.get("id") for comp in merged_index["completions"]}

    for new_topic in new_topics:
        topic_id = new_topic.get("id") or str(uuid.uuid4())
        topic_name = new_topic.get("name", "Untitled")

        # Rule 3: Never move completed topics back to active
        if topic_id in completed_topic_ids:
            continue

        # Rule 1: Add new topics
        if topic_id not in existing_topic_ids:
            new_topic_entry = {
                "id": topic_id,
                "name": topic_name,
                "status": "active",
                "created_at": new_topic.get("created_at", datetime.now(timezone.utc).isoformat()),
                "last_activity": new_topic.get("last_activity", datetime.now(timezone.utc).isoformat()),
                "context_tags": new_topic.get("context_tags", []),
                "confidence": new_topic.get("confidence", 0.7),
                "key_accomplishments": new_topic.get("key_accomplishments", []),
                "blockers": new_topic.get("blockers", []),
                "notes": new_topic.get("notes", "")
            }
            merged_index["topics"].append(new_topic_entry)
            existing_topic_ids.add(topic_id)

        # Rule 2: Update last_activity if newer
        else:
            for i, topic in enumerate(merged_index["topics"]):
                if topic.get("id") == topic_id:
                    new_last_activity = new_topic.get("last_activity")
                    current_last_activity = topic.get("last_activity")

                    if new_last_activity and new_last_activity > current_last_activity:
                        merged_index["topics"][i]["last_activity"] = new_last_activity
                    break

    # Merge activity events (Rule 5: append only)
    new_events = activity_data.get("events", [])
    for event in new_events:
        # Avoid duplicate events: check if event already in history
        event_ts = event.get("ts")
        event_type = event.get("event_type")
        event_desc = event.get("description")

        is_duplicate = any(
            h.get("ts") == event_ts and h.get("event_type") == event_type and h.get("description") == event_desc
            for h in merged_index["activity_history"]
        )

        if not is_duplicate:
            merged_index["activity_history"].append({
                "ts": event_ts,
                "event_type": event_type,
                "topic_id": event.get("topic_id"),
                "description": event_desc
            })

    # Sort activity history by timestamp
    merged_index["activity_history"].sort(key=lambda e: e.get("ts", ""))

    # Rule 4: Update stalled_work days_stalled (recalculate from stalled_since)
    for i, stalled in enumerate(merged_index["stalled_work"]):
        stalled_since = stalled.get("stalled_since")
        if stalled_since:
            stalled_dt = datetime.fromisoformat(stalled_since.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            days_stalled = (now - stalled_dt).days
            merged_index["stalled_work"][i]["days_stalled"] = days_stalled

    # Validate schema before returning
    is_valid, error_msg = validate_index_schema(merged_index)
    if not is_valid:
        raise ValueError(f"Schema validation failed after merge: {error_msg}")

    return merged_index
