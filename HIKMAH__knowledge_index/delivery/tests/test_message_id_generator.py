# test_message_id_generator.py — ID uniqueness and parse tests (Wave 2)
#
# Wave 2 will implement the following test cases:
#
# test_message_id_format:
#   - generate() returns string starting with "MSG-"
#   - Length is 30 characters (MSG-18chars-8chars)
#   - Contains exactly 2 hyphens (3 parts)
#   - Random suffix is uppercase hex
#
# test_message_id_uniqueness:
#   - Generate 10,000 IDs, verify zero collisions
#   - len(set(ids)) == len(ids)
#
# test_message_id_sortability:
#   - Generate 100 IDs with 1ms sleep between each
#   - sorted(ids) == ids (lexicographic == chronological)
#
# test_parse_round_trip:
#   - generate() → parse() → verify message_id field matches original
#   - verify timestamp_utc is a datetime object with tzinfo=UTC
#
# test_parse_timestamp_accuracy:
#   - Generate ID, record time before/after, parse timestamp
#   - Verify parsed timestamp is within ±1 second of recorded time
#
# test_parse_invalid_format:
#   - parse("invalid") → ValueError
#   - parse("") → ValueError
#   - parse("MSG-") → ValueError (too few parts)
#   - parse("MSG-12345678-ABCDEFGH") → ValueError (timestamp not 18 chars)
#   - parse("MSG-123456789012345678-XXXXXXXX") → ValueError (non-hex random)
#
# test_parse_invalid_timestamp_values:
#   - parse("MSG-20261399093045123-A7F2E8CD") → ValueError (month=99 invalid)
#
# test_no_pii_in_message_id:
#   - Verify generate() output contains only MSG prefix, digits, and hex chars
#   - No letters from persona names, no readable text
