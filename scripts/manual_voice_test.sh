#!/bin/bash
# Manual voice loop testing guide

set -e

echo "=== Manual Voice Loop Testing Guide ==="
echo ""
echo "This script guides you through manual testing of the Jarvis voice loop."
echo "Make sure you have:"
echo "  - Tool Broker running (python -m tool_broker.main)"
echo "  - Audio hardware connected"
echo "  - Whisper models downloaded"
echo ""
echo "Press Enter to continue..."
read

# Test 1: Wake word
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Wake Word Detection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Action: Say 'Hey Jarvis' clearly"
echo "Expected: Chime sound, state → ATTENDING"
echo ""
echo "Result: [ ] Pass  [ ] Fail"
echo ""
echo "Press Enter when ready to continue..."
read

# Test 2: Basic command
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Basic Command Processing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Action: Say 'Hey Jarvis' then 'What time is it?'"
echo "Expected: Time response via TTS, state → LISTENING"
echo ""
echo "Result: [ ] Pass  [ ] Fail"
echo ""
echo "Press Enter when ready to continue..."
read

# Test 3: Device control
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Device Control"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Action: Say 'Hey Jarvis' then 'Turn on the living room light'"
echo "Expected: Tool call executed, confirmation TTS"
echo ""
echo "Result: [ ] Pass  [ ] Fail"
echo ""
echo "Press Enter when ready to continue..."
read

# Test 4: Barge-in
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Barge-in Interrupt"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Action: Trigger a long response, then say 'Hey Jarvis' mid-speech"
echo "Expected: TTS stops immediately, state → ATTENDING"
echo ""
echo "Result: [ ] Pass  [ ] Fail"
echo ""
echo "Press Enter when ready to continue..."
read

# Test 5: Silence handling
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 5: Silence Handling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Action: Say 'Hey Jarvis' but remain silent"
echo "Expected: After ~5s, returns to LISTENING"
echo ""
echo "Result: [ ] Pass  [ ] Fail"
echo ""
echo "Press Enter when ready to continue..."
read

# Test 6: Error recovery
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 6: Error Recovery"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Action: Stop Tool Broker, then trigger a command"
echo "Expected: Error message via TTS, returns to LISTENING"
echo ""
echo "Result: [ ] Pass  [ ] Fail"
echo ""

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Manual Testing Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Please document any failures and attach logs."
