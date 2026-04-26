#!/usr/bin/env bash
# Category 2: requires stdin input.
echo "What is your name?"
read -r name
echo "Hello, $name!"

echo "Pick a number:"
read -r n
echo "Doubled: $((n * 2))"

echo "Type 'yes' to confirm:"
read -r answer
if [[ "$answer" == "yes" ]]; then
    echo "Confirmed."
else
    echo "Got '$answer', expected 'yes'."
fi
