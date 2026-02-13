#!/bin/bash
# Demo Validation Runner
# Waits for pipeline completion, then runs comprehensive validation

PIPELINE_OUTPUT="/private/tmp/claude-502/-Users-JB-Documents-IT-IT-DD-Test-2/tasks/bc50a93.output"
PROJECT_DIR="/Users/JB/Documents/IT/IT DD Test 2/9.5/it-diligence-agent 2"

cd "$PROJECT_DIR"

echo "=== DEMO VALIDATION RUNNER ==="
echo "Monitoring pipeline: $PIPELINE_OUTPUT"
echo ""

# Wait for pipeline completion (check every 30 seconds)
while true; do
    if tail -50 "$PIPELINE_OUTPUT" 2>/dev/null | grep -q "Reasoning complete for organization"; then
        echo "✅ Pipeline complete! All 6 domains finished."
        break
    fi

    # Show current status
    CURRENT=$(tail -5 "$PIPELINE_OUTPUT" 2>/dev/null | grep -E "(Starting|complete)" | tail -1 | sed 's/.*- //')
    echo "[$(date +%H:%M:%S)] Status: $CURRENT"
    sleep 30
done

echo ""
echo "=== PHASE 2: RUNNING VALIDATION ==="
echo ""

# Find latest facts file
FACTS_FILE=$(ls -t output/runs/*/facts/facts.json 2>/dev/null | head -1)
if [ -z "$FACTS_FILE" ]; then
    echo "❌ ERROR: No facts.json found"
    exit 1
fi
echo "Facts file: $FACTS_FILE"

# Get latest deal_id from database
DEAL_ID=$(sqlite3 data/diligence.db "SELECT deal_id FROM deals ORDER BY created_at DESC LIMIT 1" 2>/dev/null | tr -d '\n')
if [ -z "$DEAL_ID" ]; then
    echo "⚠️  WARNING: No deal_id found, will extract from facts file"
    DEAL_ID=$(grep -o '"deal_id"[[:space:]]*:[[:space:]]*"[^"]*"' "$FACTS_FILE" | head -1 | cut -d'"' -f4)
fi
echo "Deal ID: $DEAL_ID"

# Run validation
echo ""
echo "Running validation..."
python validate_automation.py \
    --facts "$FACTS_FILE" \
    --db data/diligence.db \
    --deal-id "$DEAL_ID" \
    --json-output /tmp/demo_validation.json \
    --md-output /tmp/demo_validation.md \
    --verbose

VALIDATION_EXIT=$?

echo ""
echo "=== VALIDATION COMPLETE ==="
echo "Exit code: $VALIDATION_EXIT"
echo "JSON output: /tmp/demo_validation.json"
echo "Markdown output: /tmp/demo_validation.md"
echo ""

if [ $VALIDATION_EXIT -eq 0 ]; then
    echo "✅ All validations passed!"
elif [ $VALIDATION_EXIT -eq 2 ]; then
    echo "⚠️  Warnings detected (no critical failures)"
else
    echo "❌ Critical failures detected"
fi

exit $VALIDATION_EXIT
