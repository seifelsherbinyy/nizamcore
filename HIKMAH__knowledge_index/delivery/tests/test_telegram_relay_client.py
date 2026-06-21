# test_telegram_relay_client.py — relay integration tests with mocks (Wave 2)
#
# Wave 2 will implement the following test cases:
# All tests mock tg_send_message and tg_get_updates (no real Telegram API calls)
#
# test_send_message:
#   - Mock tg_send_message to return {"ok": True, "result": {"message_id": 12345}}
#   - Call send_message(chat_id=123, text="test")
#   - Verify tg_send_message called with (token, 123, "test", parse_mode=None)
#   - Verify returned dict contains result.message_id == 12345
#
# test_send_message_with_parse_mode:
#   - send_message(chat_id=123, text="<b>bold</b>", parse_mode="HTML")
#   - Verify tg_send_message called with parse_mode="HTML"
#
# test_send_message_propagates_runtime_error:
#   - Mock tg_send_message to raise RuntimeError("sendMessage not ok")
#   - Call send_message() → verify RuntimeError propagated
#
# test_get_updates:
#   - Mock tg_get_updates to return sample update list
#   - Call get_updates(offset=0, timeout=25)
#   - Verify tg_get_updates called with (token, 0, 25)
#   - Verify returned list matches mock output
#
# test_get_updates_empty:
#   - Mock tg_get_updates to return []
#   - Call get_updates() → returns empty list
#
# test_get_updates_propagates_conflict:
#   - Mock tg_get_updates to raise GatewayPollingConflict
#   - Call get_updates() → verify GatewayPollingConflict propagated
#
# test_check_reply_to_message_id_with_reply:
#   - update = {"message": {"reply_to_message": {"message_id": 12345}}}
#   - check_reply_to_message_id(update) == 12345
#
# test_check_reply_to_message_id_no_reply:
#   - update = {"message": {"message_id": 99, "text": "hi"}}
#   - check_reply_to_message_id(update) is None
#
# test_check_reply_to_message_id_no_message:
#   - update = {} (no message key)
#   - check_reply_to_message_id(update) is None
#
# test_token_from_explicit_parameter:
#   - TelegramRelayClient(token="abc123").token == "abc123"
#
# test_token_from_environment:
#   - Set TELEGRAM_BOT_TOKEN="env_token"
#   - TelegramRelayClient().token == "env_token"
#
# test_token_missing_raises_value_error:
#   - Unset TELEGRAM_BOT_TOKEN
#   - TelegramRelayClient() → ValueError
#
# test_explicit_token_takes_priority_over_env:
#   - Set TELEGRAM_BOT_TOKEN="env_token"
#   - TelegramRelayClient(token="explicit_token").token == "explicit_token"
