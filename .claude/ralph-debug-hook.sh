#!/bin/bash
# Debug wrapper for Ralph Loop stop hook
# Logs everything to .claude/ralph-hook-debug.log

LOG=".claude/ralph-hook-debug.log"
echo "=== HOOK FIRED $(date -u) ===" >> "$LOG"
echo "PWD: $(pwd)" >> "$LOG"
echo "STATE FILE EXISTS: $(test -f .claude/ralph-loop.local.md && echo YES || echo NO)" >> "$LOG"

# Read stdin (hook input)
HOOK_INPUT=$(cat)
echo "HOOK_INPUT: $HOOK_INPUT" >> "$LOG"

# Check state file
RALPH_STATE_FILE=".claude/ralph-loop.local.md"
if [[ ! -f "$RALPH_STATE_FILE" ]]; then
  echo "RESULT: No state file, allowing exit" >> "$LOG"
  exit 0
fi

echo "STATE FILE CONTENTS:" >> "$LOG"
cat "$RALPH_STATE_FILE" >> "$LOG"

# Parse frontmatter
FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$RALPH_STATE_FILE")
ITERATION=$(echo "$FRONTMATTER" | grep '^iteration:' | sed 's/iteration: *//')
MAX_ITERATIONS=$(echo "$FRONTMATTER" | grep '^max_iterations:' | sed 's/max_iterations: *//')
COMPLETION_PROMISE=$(echo "$FRONTMATTER" | grep '^completion_promise:' | sed 's/completion_promise: *//' | sed 's/^"\(.*\)"$/\1/')

echo "PARSED: iteration=$ITERATION max=$MAX_ITERATIONS promise=$COMPLETION_PROMISE" >> "$LOG"

# Validate
if [[ ! "$ITERATION" =~ ^[0-9]+$ ]]; then
  echo "ERROR: iteration not numeric: '$ITERATION'" >> "$LOG"
  rm "$RALPH_STATE_FILE"
  exit 0
fi
if [[ ! "$MAX_ITERATIONS" =~ ^[0-9]+$ ]]; then
  echo "ERROR: max_iterations not numeric: '$MAX_ITERATIONS'" >> "$LOG"
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Check max iterations
if [[ $MAX_ITERATIONS -gt 0 ]] && [[ $ITERATION -ge $MAX_ITERATIONS ]]; then
  echo "RESULT: Max iterations reached" >> "$LOG"
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Get transcript
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path' 2>>"$LOG")
echo "TRANSCRIPT_PATH: $TRANSCRIPT_PATH" >> "$LOG"
echo "TRANSCRIPT EXISTS: $(test -f "$TRANSCRIPT_PATH" && echo YES || echo NO)" >> "$LOG"

if [[ -z "$TRANSCRIPT_PATH" ]] || [[ "$TRANSCRIPT_PATH" == "null" ]] || [[ ! -f "$TRANSCRIPT_PATH" ]]; then
  echo "ERROR: Transcript not found or null" >> "$LOG"
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Check for assistant messages
if ! grep -q '"role":"assistant"' "$TRANSCRIPT_PATH"; then
  echo "ERROR: No assistant messages in transcript" >> "$LOG"
  # Also try with spaces
  if ! grep -q '"role": "assistant"' "$TRANSCRIPT_PATH"; then
    echo "ERROR: No assistant messages (even with spaces)" >> "$LOG"
    rm "$RALPH_STATE_FILE"
    exit 0
  fi
fi

# Get last assistant message
LAST_LINE=$(grep '"role":"assistant"' "$TRANSCRIPT_PATH" | tail -1)
if [[ -z "$LAST_LINE" ]]; then
  LAST_LINE=$(grep '"role": "assistant"' "$TRANSCRIPT_PATH" | tail -1)
fi
echo "LAST_LINE length: ${#LAST_LINE}" >> "$LOG"

# Parse with jq
LAST_OUTPUT=$(echo "$LAST_LINE" | jq -r '.message.content | map(select(.type == "text")) | map(.text) | join("\n")' 2>>"$LOG")
JQ_EXIT=$?
echo "JQ_EXIT: $JQ_EXIT" >> "$LOG"
echo "LAST_OUTPUT length: ${#LAST_OUTPUT}" >> "$LOG"

if [[ $JQ_EXIT -ne 0 ]]; then
  echo "ERROR: jq parse failed" >> "$LOG"
  rm "$RALPH_STATE_FILE"
  exit 0
fi

if [[ -z "$LAST_OUTPUT" ]]; then
  echo "ERROR: Empty last output" >> "$LOG"
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Check completion promise
if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  PROMISE_TEXT=$(echo "$LAST_OUTPUT" | perl -0777 -pe 's/.*?<promise>(.*?)<\/promise>.*/$1/s; s/^\s+|\s+$//g; s/\s+/ /g' 2>/dev/null || echo "")
  echo "PROMISE_TEXT: '$PROMISE_TEXT'" >> "$LOG"
  if [[ -n "$PROMISE_TEXT" ]] && [[ "$PROMISE_TEXT" = "$COMPLETION_PROMISE" ]]; then
    echo "RESULT: Promise matched! Completing loop." >> "$LOG"
    rm "$RALPH_STATE_FILE"
    exit 0
  fi
fi

# Continue loop
NEXT_ITERATION=$((ITERATION + 1))
PROMPT_TEXT=$(awk '/^---$/{i++; next} i>=2' "$RALPH_STATE_FILE")
echo "PROMPT_TEXT: '$PROMPT_TEXT'" >> "$LOG"

if [[ -z "$PROMPT_TEXT" ]]; then
  echo "ERROR: Empty prompt text" >> "$LOG"
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Update iteration
TEMP_FILE="${RALPH_STATE_FILE}.tmp.$$"
sed "s/^iteration: .*/iteration: $NEXT_ITERATION/" "$RALPH_STATE_FILE" > "$TEMP_FILE"
mv "$TEMP_FILE" "$RALPH_STATE_FILE"

SYSTEM_MSG="🔄 Ralph iteration $NEXT_ITERATION | To stop: output <promise>$COMPLETION_PROMISE</promise> (ONLY when TRUE)"

echo "RESULT: Blocking exit, feeding iteration $NEXT_ITERATION" >> "$LOG"

jq -n \
  --arg prompt "$PROMPT_TEXT" \
  --arg msg "$SYSTEM_MSG" \
  '{
    "decision": "block",
    "reason": $prompt,
    "systemMessage": $msg
  }'

exit 0
