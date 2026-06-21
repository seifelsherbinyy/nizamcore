# test_delivery_ledger.py — ledger write and query tests (Wave 2)
#
# Wave 2 will implement the following test cases:
#
# test_log_delivery:
#   - Create ledger in tmp_path, call log_delivery() with valid args
#   - Verify JSONL file created, one line, parseable JSON
#   - Verify event_type=="delivery", persona, message_id fields correct
#   - Verify ledger_hash field present and is 16-char hex string
#
# test_log_delivery_failure_status:
#   - log_delivery() with status="failure", error_reason="network_timeout"
#   - Verify status and error_reason fields in ledger entry
#
# test_context_tag_validation_accepts_valid_tags:
#   - All 5 whitelisted tags: technical, health, financial, strategic, personal
#   - Each should succeed without error
#
# test_context_tag_validation_rejects_invalid_tags:
#   - ["raw_data", "pii", "location", "invalid_tag"]
#   - Each should raise ValueError with privacy gate message
#
# test_log_response:
#   - log_response() writes event_type=="response" entry
#   - Verify engagement_latency_seconds, response_time, engagement_status fields
#   - Verify response_text present
#
# test_response_text_truncation:
#   - log_response() with 600-char response_text
#   - Verify stored response_text is truncated to 500 chars
#
# test_log_no_response:
#   - log_no_response() writes event_type=="engagement_window_closed" entry
#   - Verify engagement_status=="no_response"
#
# test_get_deliveries_for_persona:
#   - Log 3 deliveries for AMMAR, 2 for HIKMAH
#   - get_deliveries_for_persona("AMMAR") returns 3 entries
#   - get_deliveries_for_persona("HIKMAH") returns 2 entries
#   - Results are in reverse chronological order (most recent first)
#
# test_get_deliveries_for_persona_limit:
#   - Log 15 deliveries for AMMAR
#   - get_deliveries_for_persona("AMMAR", limit=5) returns exactly 5
#
# test_get_deliveries_empty_file:
#   - Call on non-existent ledger path → returns empty list
#
# test_get_responses_for_message:
#   - Log delivery + response for same message_id
#   - get_responses_for_message(message_id) returns the response entry
#
# test_get_responses_for_message_no_response:
#   - Log delivery only (no response)
#   - get_responses_for_message(message_id) returns None
#
# test_ledger_append_only:
#   - Log 3 entries, read file, verify 3 lines present (no overwrites)
#
# test_ledger_hash_integrity:
#   - Read ledger entry, compute SHA256 of entry without hash field
#   - Verify stored ledger_hash matches computed value (truncated)
