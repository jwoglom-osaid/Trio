#!/bin/bash
if [ "$(git rev-list --count @{u}..HEAD 2>/dev/null)" -gt 0 ]; then
    echo "Has unpushed commits. Are you sure?"
    read || exit 1
fi

gh workflow run build_trio.yml --ref dev -f skip_upstream_sync=false --repo jwoglom-osaid/Trio

