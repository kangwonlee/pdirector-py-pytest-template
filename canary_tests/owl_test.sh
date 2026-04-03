#!/usr/bin/env bash
# begin canary_tests/owl_test.sh
#
# Owl test — integration test for prompt-only grader containers.
# Runs canary samples INSIDE the just-built container using the
# classroom-prompt-reusable.yml Docker recipe, then checks pass/fail
# expectations.
#
# Adapted for prompt-only two-volume architecture:
#   - workspace (ro): prompt.md
#   - output (rw):    exercise.py (injected sample)
#
# Usage: . owl_test.sh <image_url> [homework_dir]
#
#   image_url    — GHCR image URL (e.g., ghcr.io/.../eca-director-pytest-NNN:abc1234)
#   homework_dir — (optional) cloned -homework- repo directory for realistic workspace

set -u

IMAGE_URL="${1:?Usage: owl_test.sh <image_url> [homework_dir]}"
HOMEWORK_DIR="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

passed=0
failed=0
errors=()

# Discover samples — same convention as test_samples.py
for sample_dir in "$SCRIPT_DIR"/sample*/; do
  [ -d "$sample_dir" ] || continue

  for script in "$sample_dir"/exercise*.py; do
    [ -f "$script" ] || continue
    filename="$(basename "$script")"
    stem="${filename%.py}"

    # Skip non-sample files
    [[ "$stem" == test_* ]] && continue
    [[ "$stem" == __init__ ]] && continue

    # Determine expectation from filename suffix
    if [[ "$stem" == *-pass ]]; then
      expect_rc=0
      expect_label="PASS"
    elif [[ "$stem" == *-fail ]]; then
      expect_rc=1
      expect_label="FAIL"
    else
      continue
    fi

    sample_name="$(basename "$sample_dir")/$filename"
    echo "--- Owl test: $sample_name (expect $expect_label) ---"

    # Prepare workspace (prompt.md) and output (exercise.py)
    workspace="$(mktemp -d)"
    output_dir="$(mktemp -d)"

    # Copy homework repo contents if available (realistic workspace)
    if [ -n "$HOMEWORK_DIR" ] && [ -d "$HOMEWORK_DIR" ]; then
      cp -r "$HOMEWORK_DIR"/. "$workspace"/
    fi

    # Inject prompt.md into workspace
    if [ -f "$sample_dir/prompt.md" ]; then
      cp "$sample_dir/prompt.md" "$workspace/prompt.md"
    else
      # Create a minimal dummy prompt so prompt_exists test passes
      echo "# Prompt" > "$workspace/prompt.md"
      echo "" >> "$workspace/prompt.md"
      echo "## Task Description" >> "$workspace/prompt.md"
      echo "Canary test dummy prompt." >> "$workspace/prompt.md"
    fi

    # Inject sample as exercise.py into output dir
    cp "$script" "$output_dir/exercise.py"

    # Copy sibling files from sample dir (supporting multi-file samples)
    for sibling in "$sample_dir"/*; do
      [ -f "$sibling" ] || continue
      [ "$sibling" = "$script" ] && continue
      sib_name="$(basename "$sibling")"
      [[ "$sib_name" == test_* ]] && continue
      [[ "$sib_name" == __init__.py ]] && continue
      [[ "$sib_name" == prompt.md ]] && continue
      cp "$sibling" "$output_dir/"
    done

    # Run grader in container — replicates classroom-prompt-reusable.yml recipe
    # Two volumes: workspace (ro) for prompt, output (rw) for exercise.py
    set +e
    docker run --rm \
      --user 1001:1001 \
      --network none \
      --volume "$workspace:/app/workspace:ro" \
      --volume "$output_dir:/output:rw" \
      --env STUDENT_CODE_FOLDER=/output \
      "$IMAGE_URL" \
      python3 -m pytest /tests/ -v --tb=short \
      -k "not git_log and not window_capture"
    actual_rc=$?

    # Check result
    if [ "$expect_rc" -eq 0 ] && [ "$actual_rc" -eq 0 ]; then
      echo "OK: $sample_name expected pass, got pass"
      passed=$((passed + 1))
    elif [ "$expect_rc" -eq 1 ] && [ "$actual_rc" -ne 0 ]; then
      echo "OK: $sample_name expected fail, got fail (rc=$actual_rc)"
      passed=$((passed + 1))
    else
      echo "MISMATCH: $sample_name expected $expect_label but got rc=$actual_rc"
      errors+=("$sample_name")
      failed=$((failed + 1))
    fi

    # Cleanup
    rm -rf "$workspace" "$output_dir"
    echo ""
  done
done

# Summary
echo "=== Owl Test Summary ==="
echo "Passed:  $passed"
echo "Failed:  $failed"

if [ "$((passed + failed))" -eq 0 ]; then
  echo "WARNING: No samples found in canary_tests/sample*/"
  echo "Owl test skipped — no samples to validate."
  exit 0
fi

if [ "$failed" -gt 0 ]; then
  echo "FAILED samples:"
  for e in "${errors[@]}"; do
    echo "  - $e"
  done
  exit 1
fi

echo "All owl tests passed."
exit 0

# end canary_tests/owl_test.sh
