#!/usr/bin/env bash
cd /opt/vertexjd
echo "=== arranque app / seed ==="
docker compose logs vertexlocation 2>&1 | grep -iE "backend iniciado|seed|sirviendo|application startup|uvicorn running" | head
echo "=== health ==="
docker compose exec -T vertexlocation python -c 'import urllib.request; print(urllib.request.urlopen("http://localhost:8000/health").read().decode())'
echo "=== login admin (VertexTemp2026) ==="
docker compose exec -T vertexlocation python -c 'import urllib.request,json; d=json.dumps({"email":"cijj1969@gmail.com","password":"VertexTemp2026"}).encode(); req=urllib.request.Request("http://localhost:8000/api/auth/login-json",data=d,headers={"Content-Type":"application/json"}); r=urllib.request.urlopen(req); print("HTTP",r.status,"-> login OK")'
echo "=== SPA index.html ==="
docker compose exec -T vertexlocation python -c 'import urllib.request; h=urllib.request.urlopen("http://localhost:8000/login").read().decode(); print("index.html OK" if "root" in h else "NO")'
