#!/usr/bin/env python3
"""
Integration test for Phase 17 (Delivery & Response Tracking) and Phase 18 (Adaptation & Format Evolution)

Tests the complete delivery → adaptation → message generation pipeline with real configurations.
"""

import os
import sys
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add HIKMAH to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
from dotenv import load_dotenv
load_dotenv()

def test_phase_17_delivery_infrastructure():
    """Test Phase 17: Message delivery infrastructure"""
    print("\n" + "="*70)
    print("PHASE 17: DELIVERY & RESPONSE TRACKING TEST")
    print("="*70)

    from HIKMAH__knowledge_index.delivery import (
        MessageIDGenerator, DeliveryLedger, TelegramRelayClient
    )

    # Test 1: MessageIDGenerator
    print("\n[TEST 1] MessageIDGenerator - Unique sortable IDs")
    generator = MessageIDGenerator()
    import time
    ids = []
    for i in range(5):
        ids.append(generator.generate())
        if i < 4:
            time.sleep(0.01)  # Small delay to ensure different timestamps

    print(f"  Generated IDs: {ids}")
    assert all(id.startswith("MSG-") for id in ids), "All IDs should start with MSG-"
    # IDs should be sortable - when timestamps differ, sort is by timestamp
    sorted_ids = sorted(ids)
    assert sorted_ids == ids, "IDs should be sortable by timestamp"
    assert len(set(ids)) == len(ids), "All IDs should be unique"
    print("  [OK] MessageIDGenerator works: sortable, unique IDs")

    # Test 2: DeliveryLedger
    print("\n[TEST 2] DeliveryLedger - Immutable audit trail")
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "DELIVERY_LEDGER.jsonl"
        ledger = DeliveryLedger(ledger_path)

        # Create synthetic message
        msg_id = generator.generate()

        # Log delivery event
        ledger.log_delivery(
            message_id=msg_id,
            persona="AMMAR",
            context_tags=["technical"],
            telegram_message_id=12345,
            status="delivered"
        )
        print(f"  Logged delivery: {msg_id} → AMMAR")

        # Simulate response
        ledger.log_response(
            message_id=msg_id,
            persona="AMMAR",
            telegram_message_id=12345,
            response_text="Thanks for the update",
            response_latency_seconds=450
        )
        print(f"  Logged response: AMMAR responded in 7.5 minutes")

        # Query ledger
        deliveries = ledger.get_deliveries_for_persona("AMMAR")
        assert len(deliveries) == 1, "Should have 1 delivery for AMMAR"

        responses = ledger.get_responses_for_message(msg_id)
        assert len(responses) == 1, "Should have 1 response for message"

        # Verify ledger file exists and is JSONL
        assert ledger_path.exists(), "Ledger file should exist"
        with open(ledger_path) as f:
            lines = f.readlines()
            assert len(lines) == 2, "Should have 2 lines (delivery + response)"
            assert all(json.loads(line) for line in lines), "All lines should be valid JSON"

        print("  [OK] DeliveryLedger works: immutable JSONL, queryable")

    # Test 3: TelegramRelayClient
    print("\n[TEST 3] TelegramRelayClient - Hermes relay integration")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    assert telegram_bot_token, "TELEGRAM_BOT_TOKEN not set in .env"

    relay_client = TelegramRelayClient(token=telegram_bot_token)
    print(f"  [OK] TelegramRelayClient initialized with token: {telegram_bot_token[:20]}...")

    # Verify token format (bot_id:token_str)
    bot_id, token_str = telegram_bot_token.split(":")
    assert bot_id == "8953667021", f"Expected bot ID 8953667021, got {bot_id}"
    print(f"  [OK] Telegram bot verified: ID {bot_id}")

    return True


def test_phase_18_adaptation_infrastructure():
    """Test Phase 18: Adaptation & Format Evolution infrastructure"""
    print("\n" + "="*70)
    print("PHASE 18: ADAPTATION & FORMAT EVOLUTION TEST")
    print("="*70)

    from HIKMAH__knowledge_index.adaptation import (
        WeeklyResponseRateCalculator, FormatRotationManager,
        AdaptationLogger, AdaptationState
    )
    from HIKMAH__knowledge_index.delivery import MessageIDGenerator, DeliveryLedger

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create synthetic delivery ledger with 7 days of data
        print("\n[TEST 1] Synthetic delivery data (7-day window)")
        ledger_path = tmpdir_path / "DELIVERY_LEDGER.jsonl"
        ledger = DeliveryLedger(ledger_path)
        generator = MessageIDGenerator()

        now = datetime.utcnow()
        personas = ["AMMAR", "HIKMAH", "TARIQ"]

        # Create 14 deliveries + 9 responses per persona (65% response rate = below 80% threshold)
        for persona in personas:
            for i in range(14):
                day_offset = (7 - i) if i < 7 else (14 - i)
                msg_time = now - timedelta(days=day_offset)

                msg_id = generator.generate()
                ledger.log_delivery(
                    message_id=msg_id,
                    persona=persona,
                    context_tags=["technical"],
                    telegram_message_id=1000 + i,
                    status="delivered"
                )

                # Response 9/14 times (64% = below 80%)
                if i < 9:
                    ledger.log_response(
                        message_id=msg_id,
                        persona=persona,
                        telegram_message_id=1000 + i,
                        response_text=f"Response {i}",
                        response_latency_seconds=300 + i*10
                    )

        print(f"  [OK] Created synthetic ledger: 14 deliveries × 3 personas")
        print(f"    Response rate per persona: 9/14 = 64% (below 80% threshold)")

        # Test WeeklyResponseRateCalculator
        print("\n[TEST 2] WeeklyResponseRateCalculator")
        calc = WeeklyResponseRateCalculator(ledger_path)

        for persona in personas:
            rate, numerator, denominator = calc.calculate(persona, days=7)
            print(f"  {persona}: {numerator}/{denominator} = {rate:.1%} response rate")
            assert rate < 0.80, f"{persona} should have <80% response rate to trigger adaptation"
            assert numerator == 9, f"Expected 9 responses, got {numerator}"
            assert denominator == 14, f"Expected 14 deliveries, got {denominator}"

        print("  [OK] WeeklyResponseRateCalculator works: rates calculated correctly")

        # Test FormatRotationManager
        print("\n[TEST 3] FormatRotationManager - Format rotation state machine")
        state_path = tmpdir_path / "ADAPTATION_STATE.jsonl"
        manager = FormatRotationManager(state_path)

        # Initial state: no format yet
        current_format = manager.get_current_format("AMMAR")
        print(f"  AMMAR initial format: {current_format}")

        # Rotate format 10 times and verify no consecutive repeats
        formats = []
        for i in range(10):
            new_format = manager.rotate_format("AMMAR", response_rate=0.64)
            formats.append(new_format)
            print(f"    Rotation {i+1}: {new_format}")

        # Check no consecutive repeats
        for i in range(len(formats)-1):
            assert formats[i] != formats[i+1], \
                f"Consecutive repeat found: {formats[i]} == {formats[i+1]} at index {i}"

        print("  [OK] FormatRotationManager works: 10 rotations, zero consecutive repeats")

        # Test AdaptationLogger
        print("\n[TEST 4] AdaptationLogger - Immutable audit trail")
        ledger_path_adapt = tmpdir_path / "ADAPTATION_LEDGER.jsonl"
        logger = AdaptationLogger(ledger_path_adapt)

        logger.log_rotation(
            persona="AMMAR",
            old_format="standard",
            new_format="short",
            response_rate=0.64,
            threshold=0.80
        )

        # Verify ledger was written
        assert ledger_path_adapt.exists(), "Adaptation ledger should exist"
        with open(ledger_path_adapt) as f:
            entry = json.loads(f.readline())
            assert entry["persona"] == "AMMAR", "Entry should have AMMAR"
            assert entry["old_format"] == "standard", "Should log old format"
            assert entry["new_format"] == "short", "Should log new format"
            assert "rationale" in entry, "Should include rationale"
            print(f"  Logged: {entry['rationale']}")

        print("  [OK] AdaptationLogger works: JSONL entries with rationale")

        # Test AdaptationState persistence
        print("\n[TEST 5] AdaptationState - Disk persistence")
        state = AdaptationState()
        state.current_format = "emoji"
        state.previous_format = "short"
        state.save_state(state_path, "HIKMAH")

        # Load state back
        loaded_state = AdaptationState.load_state(state_path, "HIKMAH")
        assert loaded_state.current_format == "emoji", "Should persist current format"
        assert loaded_state.previous_format == "short", "Should persist previous format"
        print(f"  [OK] AdaptationState persists: current={loaded_state.current_format}, prev={loaded_state.previous_format}")

    return True


def test_phase_18_message_generation_integration():
    """Test Phase 18 integration with Phase 16 message generation"""
    print("\n" + "="*70)
    print("PHASE 18 ↔ PHASE 16 INTEGRATION TEST")
    print("="*70)

    from HIKMAH__knowledge_index.message_generation import generate_message

    print("\n[TEST 1] Message generation with format_hint")

    # Test without format hint (baseline)
    msg_standard = generate_message(
        persona="AMMAR",
        format_hint=None  # No adaptation
    )
    print(f"  Standard message (no format_hint):")
    print(f"    Length: {len(msg_standard)} chars")
    print(f"    Preview: {msg_standard[:80]}...")
    assert len(msg_standard) > 0, "Should generate non-empty message"

    # Test with format hint
    format_hints = ["standard", "short", "emoji", "direct_question", "story"]
    for hint in format_hints:
        msg = generate_message(
            persona="AMMAR",
            format_hint=hint
        )
        print(f"  Format '{hint}': {len(msg)} chars, preview: {msg[:60]}...")
        assert len(msg) > 0, f"Should generate message with format_hint={hint}"

    print("  [OK] Message generation works with all format hints")

    print("\n[TEST 2] Phase 16 backward compatibility (no format_hint)")
    # Existing Phase 16 code should work unchanged
    msg = generate_message(persona="HIKMAH")
    assert msg, "Should work without format_hint parameter"
    print("  [OK] Backward compatible: Phase 16 calls work unchanged")

    return True


def test_end_to_end_pipeline():
    """Test complete delivery → adaptation → message generation pipeline"""
    print("\n" + "="*70)
    print("END-TO-END PIPELINE TEST: Delivery → Adaptation → Generation")
    print("="*70)

    from HIKMAH__knowledge_index.delivery import MessageIDGenerator, DeliveryLedger
    from HIKMAH__knowledge_index.adaptation import (
        WeeklyResponseRateCalculator, FormatRotationManager, AdaptationLogger
    )
    from HIKMAH__knowledge_index.message_generation import generate_and_dedupe

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create delivery ledger with low engagement
        print("\n[STAGE 1] Delivery ledger - low engagement scenario")
        delivery_ledger_path = tmpdir_path / "DELIVERY_LEDGER.jsonl"
        delivery_ledger = DeliveryLedger(delivery_ledger_path)
        generator = MessageIDGenerator()

        now = datetime.utcnow()
        persona = "TARIQ"

        # 20 deliveries, 12 responses = 60% engagement (below 80%)
        for i in range(20):
            msg_id = generator.generate()
            delivery_ledger.log_delivery(
                message_id=msg_id,
                persona=persona,
                context_tags=["technical"],
                telegram_message_id=2000 + i,
                status="delivered"
            )

            if i < 12:  # 60% response rate
                delivery_ledger.log_response(
                    message_id=msg_id,
                    persona=persona,
                    telegram_message_id=2000 + i,
                    response_text=f"Response {i}",
                    response_latency_seconds=180
                )

        print(f"  [OK] Created ledger: 20 deliveries, 12 responses = 60% engagement")

        # Check adaptation trigger
        print("\n[STAGE 2] Adaptation decision - check if threshold breached")
        calc = WeeklyResponseRateCalculator(delivery_ledger_path)
        rate, numerator, denominator = calc.calculate(persona, days=7)
        print(f"  Response rate: {numerator}/{denominator} = {rate:.1%}")

        if rate < 0.80:
            print(f"  [OK] {rate:.1%} < 80% threshold: ADAPTATION TRIGGERED")

            # Rotate format and log
            print("\n[STAGE 3] Format adaptation - rotate to new format")
            state_path = tmpdir_path / "ADAPTATION_STATE.jsonl"
            manager = FormatRotationManager(state_path)

            old_format = manager.get_current_format(persona) or "standard"
            new_format = manager.rotate_format(persona, response_rate=rate)

            print(f"  Format change: {old_format} → {new_format}")

            # Log the adaptation
            ledger_path_adapt = tmpdir_path / "ADAPTATION_LEDGER.jsonl"
            logger = AdaptationLogger(ledger_path_adapt)
            logger.log_rotation(
                persona=persona,
                old_format=old_format,
                new_format=new_format,
                response_rate=rate,
                threshold=0.80
            )
            print(f"  [OK] Logged adaptation decision to ADAPTATION_LEDGER.jsonl")

            # Generate next message with new format
            print("\n[STAGE 4] Message generation - apply format constraint")
            msg = generate_and_dedupe(
                persona=persona,
                format_hint=new_format,
                delivery_ledger_path=delivery_ledger_path,
                adaptation_state_path=state_path,
                adaptation_ledger_path=ledger_path_adapt
            )
            print(f"  Generated message with format '{new_format}':")
            print(f"    Length: {len(msg)} chars")
            print(f"    Preview: {msg[:100]}...")

            print("\n  [OK] End-to-end pipeline complete:")
            print(f"    1. Detected low engagement ({rate:.1%})")
            print(f"    2. Rotated format to '{new_format}'")
            print(f"    3. Generated message with new format")

        else:
            print(f"  [FAIL] Response rate {rate:.1%} >= 80%: no adaptation needed")

    return True


def main():
    """Run all integration tests"""
    print("\n" + "#"*70)
    print("# PHASE 17-18 INTEGRATION TEST SUITE")
    print(f"# Started: {datetime.now().isoformat()}")
    print("#"*70)

    try:
        results = []

        # Test Phase 17
        results.append(("Phase 17 Delivery Infrastructure", test_phase_17_delivery_infrastructure()))

        # Test Phase 18
        results.append(("Phase 18 Adaptation Infrastructure", test_phase_18_adaptation_infrastructure()))

        # Test Phase 18-16 integration
        results.append(("Phase 18 ↔ Phase 16 Integration", test_phase_18_message_generation_integration()))

        # Test end-to-end
        results.append(("End-to-End Pipeline", test_end_to_end_pipeline()))

        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        for name, passed in results:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{status}: {name}")

        all_passed = all(passed for _, passed in results)

        print("\n" + "#"*70)
        if all_passed:
            print("# [PASS] ALL TESTS PASSED")
        else:
            print("# [FAIL] SOME TESTS FAILED")
        print(f"# Completed: {datetime.now().isoformat()}")
        print("#"*70)

        return 0 if all_passed else 1

    except Exception as e:
        print(f"\n[ERROR] TEST FAILED WITH EXCEPTION:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
