# conftest.py — shared fixtures and mocks for Phase 17 delivery tests
#
# Wave 2 will implement:
#   - MockTelegramRelay: Simulates tg_send_message / tg_get_updates
#   - mock_ledger: Temporary JSONL ledger in tmp_path fixture
#   - sample_update: Factory for Telegram update dicts
#   - sample_reply_update: Factory for update dicts with reply_to_message
#   - SAMPLE_CHAT_ID, SAMPLE_PERSONA, SAMPLE_MESSAGE_ID constants
#
# Pattern follows HIKMAH__knowledge_index/message_generation/tests/conftest.py
# (MockClaude pattern from Phase 16)
