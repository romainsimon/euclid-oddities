#!/usr/bin/env bash
# Publish the current finds and reviews: GitHub (this repo) and spacesim.co/euclid-oddities.
# Usage (Git Bash on the Windows PC): bash site/publish.sh "short description of what changed"
set -euo pipefail
MSG="${1:?give a one-line description}"
REPO=/d/dev/euclid-oddities
TRACKD=/d/dev/research-trackd/tools/claudestronomy/trackd
SPACESIM_WT=/d/dev/spacesim-wt/oddities
NODE22=/c/Users/Romain/AppData/Roaming/nvm/v22.19.0
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"

# 1. Export finds from the research pipeline (catalogue checks are cached), then build checks
"$TRACKD/.venv/Scripts/python" "$TRACKD/fexport.py" "$REPO/site/data"
python -c "import json,sys; d=json.load(open('$(cygpath -m "$REPO")/site/data/finds.json',encoding='utf-8')); assert d['finds'], 'no finds'; print(len(d['finds']), 'finds')"

# 2. GitHub: commit and push this repository
git -C "$REPO" add site
git -C "$REPO" diff --cached --quiet || git -C "$REPO" commit -qm "$MSG

$TRAILER"
git -C "$REPO" push -q origin main

# 3. SpaceSim: fresh branch from origin/main, regenerate, sync the changelog boundary, test, push to main
git -C "$SPACESIM_WT" fetch -q origin
git -C "$SPACESIM_WT" checkout -q -B claude/euclid-oddities origin/main
MSYS_NO_PATHCONV=1 python "$REPO/site/build.py" "$(cygpath -m "$SPACESIM_WT")/public/euclid-oddities" --base /euclid-oddities
git -C "$SPACESIM_WT" add public/euclid-oddities
if git -C "$SPACESIM_WT" diff --cached --quiet; then echo "spacesim: nothing changed"; exit 0; fi
git -C "$SPACESIM_WT" commit -qm "Euclid Oddities: $MSG

$TRAILER"
X=$(git -C "$SPACESIM_WT" rev-parse HEAD); N=$(git -C "$SPACESIM_WT" rev-list --count "$X")
OLD=$(python -c "import json; print(json.load(open('$(cygpath -m "$SPACESIM_WT")/public/assets/changelog.json',encoding='utf-8'))['source']['lastCommit'])")
sed -i "s/\"commitCount\": [0-9]*,/\"commitCount\": $N,/; s/$OLD/$X/g" "$SPACESIM_WT/public/assets/changelog.json"
(cd "$SPACESIM_WT" && PATH="$NODE22:$PATH" ./node_modules/.bin/vitest run src/changelog.test.ts src/roadmap.test.ts src/appRoutes.test.ts src/favicon.test.ts)
git -C "$SPACESIM_WT" add public/assets/changelog.json
git -C "$SPACESIM_WT" commit -qm "Sync the changelog source boundary with the Euclid Oddities update

$TRAILER"
git -C "$SPACESIM_WT" push -q origin claude/euclid-oddities:main
echo "pushed; Coolify deploys main. Check https://spacesim.co/euclid-oddities in a few minutes."
