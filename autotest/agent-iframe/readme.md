docker rm -f marinabox

docker run -d --name marinabox \
  -p 6901:6081 \
  -p 9222:9222 \
  my-marinabox-browser:latest


verify
docker exec -it marinabox sh -c "netstat -tln | grep 9222"