#!/bin/bash
# Sync new learning notes from UnderStanding → LearningNotes and git push
set -e

SRC="/Volumes/Motus_SSD/mac_mini/ClawdBot_Github/openclaw/UnderStanding/"
DEST="/Volumes/Motus_SSD/CommunitySharing/Agent_Exploration/LearningNotes/"

# Copy new/updated files (skip .git, this script, and Readme.md)
rsync -av --ignore-existing --include='*.md' --exclude='*' --exclude='.git' "$SRC" "$DEST"

cd "$DEST"

# Check if there are changes
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "No new files to push."
  exit 0
fi

git add -A
git commit -m "sync: add new learning notes $(date +%Y-%m-%d)"
git push origin main
echo "Pushed new learning notes."
