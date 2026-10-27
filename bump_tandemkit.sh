(cd TandemKit && git fetch origin dev && git pull origin dev)
(git add TandemKit && git commit -m 'bump TandemKit' && (echo 'Push?' && read && git push && (echo 'Build?' && read && ./trigger_build.sh)))
