sat@4090:~/ntn-stack$ make build-n
🔨 構建所有 NTN Stack 服務...
make[1]: Entering directory '/home/sat/ntn-stack'
🔨 構建 NetStack 服務 (不使用緩存)...
make[2]: Entering directory '/home/sat/ntn-stack/netstack'
📥 拉取所有必要的第三方映像檔...
  - 拉取 Open5GS 核心網映像...
docker pull gradiant/open5gs:2.7.5
2.7.5: Pulling from gradiant/open5gs
c8e1eb8ab3b0: Pull complete
010a3d2c1a11: Pull complete
2d6c193323c8: Pull complete
58e522ac0097: Pull complete
4f4fb700ef54: Pull complete
c86549530c35: Pull complete
429e8ab36c4c: Pull complete
2cc0054207e0: Pull complete
Digest: sha256:75277742fc8a4a82cb406a9ea38e05d2c5ff8f6af1cdc756ed2f37fc74f02629
Status: Downloaded newer image for gradiant/open5gs:2.7.5
docker.io/gradiant/open5gs:2.7.5
  - 拉取 MongoDB 映像...
docker pull mongo:6.0
6.0: Pulling from library/mongo
1d387567261e: Pull complete
cb1edaf5aca0: Pull complete
781fa937b95e: Pull complete
bbd31fa309aa: Pull complete
15f41c5f7970: Pull complete
c06eb34d1366: Pull complete
e99ae3adf2c3: Pull complete
668d08fc8c9b: Pull complete
Digest: sha256:e6ea23317a13da9c83b5adae237c85ecd93a7079bb41997d409484ed7b5677bb
Status: Downloaded newer image for mongo:6.0
docker.io/library/mongo:6.0
  - 拉取 Redis 映像...
docker pull redis:7-alpine
7-alpine: Pulling from library/redis
0368fd46e3c6: Pull complete
4c55286bbede: Pull complete
5e28347af205: Pull complete
311eca34042e: Pull complete
e6fe6f07e192: Pull complete
a2cadbfeca72: Pull complete
4f4fb700ef54: Pull complete
a976ed7e7808: Pull complete
Digest: sha256:bb186d083732f669da90be8b0f975a37812b15e913465bb14d845db72a4e3e08
Status: Downloaded newer image for redis:7-alpine
docker.io/library/redis:7-alpine
  - 拉取 PostgreSQL 映像...
docker pull postgres:16-alpine
16-alpine: Pulling from library/postgres
9824c27679d3: Pull complete
ad66e73d9475: Pull complete
e62b35ad5ef0: Pull complete
d0075eb78730: Pull complete
f9996286154d: Pull complete
0ff154fa3401: Pull complete
ca2e0665c045: Pull complete
68fd2dbe7703: Pull complete
e155013fa2b9: Pull complete
27e0d631c908: Pull complete
5f5cf5fab12d: Pull complete
Digest: sha256:7c688148e5e156d0e86df7ba8ae5a05a2386aaec1e2ad8e6d11bdf10504b1fb7
Status: Downloaded newer image for postgres:16-alpine
docker.io/library/postgres:16-alpine
✅ 所有第三方映像檔拉取完成
🏗️ 建置 NetStack 所有相關映像 (不使用快取)...
  - 建置核心網 API 映像 (production 階段)...
docker build -t netstack-api:latest -f docker/Dockerfile --target production . --no-cache
[+] Building 80.3s (17/37)                                                          docker:default
[+] Building 80.4s (17/37)                                                          docker:default
 => [internal] load build definition from Dockerfile                                          0.0s
[+] Building 80.5s (17/37)                                                          docker:default
 => [internal] load build definition from Dockerfile                                          0.0s
 => => transferring dockerfile: 6.69kB                                                        0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim                           0.6s
[+] Building 80.7s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 80.7s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 80.9s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 81.0s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 81.2s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 81.3s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 81.5s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 81.6s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 81.8s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 81.9s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 82.1s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 82.2s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 82.4s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 82.5s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 82.7s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 82.8s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 83.0s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 83.1s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 83.3s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 83.4s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 83.6s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 83.7s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 83.9s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 84.0s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 84.2s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 84.3s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 84.5s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 84.6s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 84.8s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 84.9s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 85.1s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 85.2s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 85.3s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 85.5s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 85.6s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 85.7s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 85.9s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
[+] Building 85.9s (17/37)                                                          docker:default
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
[+] Building 86.1s (18/37)                                                          docker:default
[+] Building 86.1s (19/37)                                                          docker:default
[+] Building 86.3s (19/37)                                                          docker:default
[+] Building 86.4s (19/37)                                                          docker:defaults
[+] Building 86.6s (19/37)                                                          docker:default
[+] Building 86.7s (19/37)                                                          docker:default
[+] Building 86.9s (19/37)                                                          docker:default
[+] Building 87.0s (19/37)                                                          docker:default
[+] Building 87.2s (19/37)                                                          docker:default
[+] Building 87.3s (19/37)                                                          docker:default
[+] Building 87.5s (19/37)                                                          docker:defaults
[+] Building 87.6s (19/37)                                                          docker:default
[+] Building 87.8s (20/37)                                                          docker:default
[+] Building 88.0s (22/37)                                                          docker:default
[+] Building 88.0s (23/37)                                                          docker:defaults
[+] Building 88.1s (27/37)                                                          docker:default
[+] Building 88.3s (30/37)                                                          docker:default
[+] Building 88.3s (31/37)                                                          docker:default
[+] Building 88.5s (31/37)                                                          docker:default
[+] Building 88.5s (31/37)                                                          docker:default
[+] Building 88.7s (32/37)                                                          docker:default
[+] Building 88.8s (32/37)                                                          docker:default
[+] Building 88.8s (33/37)                                                          docker:default
[+] Building 89.1s (36/37)                                                          docker:default
[+] Building 89.1s (37/37)                                                          docker:default
[+] Building 89.3s (37/38)                                                          docker:default
[+] Building 89.4s (37/38)                                                          docker:default
[+] Building 89.6s (37/38)                                                          docker:default
[+] Building 89.7s (37/38)                                                          docker:default
[+] Building 89.9s (37/38)                                                          docker:default
[+] Building 90.0s (37/38)                                                          docker:default
[+] Building 90.2s (37/38)                                                          docker:default
[+] Building 90.3s (37/38)                                                          docker:default
[+] Building 90.5s (37/38)                                                          docker:default
[+] Building 90.6s (37/38)                                                          docker:default
[+] Building 90.8s (37/38)                                                          docker:default
[+] Building 90.9s (37/38)                                                          docker:default
[+] Building 91.1s (37/38)                                                          docker:default
[+] Building 91.2s (37/38)                                                          docker:default
[+] Building 91.4s (37/38)                                                          docker:default
[+] Building 91.5s (37/38)                                                          docker:default
[+] Building 91.7s (37/38)                                                          docker:default
[+] Building 91.8s (37/38)                                                          docker:default
[+] Building 91.8s (37/38)                                                          docker:default
[+] Building 91.9s (38/38) FINISHED                                                 docker:default
 => [internal] load build definition from Dockerfile                                          0.0s
 => => transferring dockerfile: 6.69kB                                                        0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim                           0.6s
 => [internal] load .dockerignore                                                             0.0s
 => => transferring context: 2B                                                               0.0s
 => [internal] load build context                                                             0.2s
 => => transferring context: 70.97MB                                                          0.2s
 => CACHED [builder  1/13] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31  0.0s
 => [builder  2/13] WORKDIR /app                                                              0.2s
 => [production  2/21] RUN groupadd -r netstack && useradd -r -g netstack netstack            0.3s
 => [builder  3/13] RUN apt-get update && apt-get install -y     gcc     g++     curl     w  24.9s
 => [production  3/21] RUN apt-get update && apt-get install -y     curl     netcat-traditio  6.1s
 => [builder  4/13] COPY requirements.txt ./requirements.txt                                  0.0s
 => [builder  5/13] RUN python -m venv /opt/venv                                              1.8s
 => [builder  6/13] RUN pip install --upgrade pip &&     pip config set global.timeout 600 &  1.8s
 => [builder  7/13] RUN pip install --no-cache-dir --default-timeout=600 -r requirements.tx  50.4s
 => [builder  8/13] COPY . .                                                                  0.1s
 => [builder  9/13] COPY tle_data/ /app/tle_data/                                             0.1s
 => [builder 10/13] COPY build_with_phase0_data.py /app/build_with_phase0_data.py             0.0s
 => [builder 11/13] RUN mkdir -p /app/data /app/tle_data /app/logs                            0.2s
 => [builder 12/13] RUN echo "🚀 Phase 0 混合模式：建構時預計算基礎數據..."                                   5.8s 21/21] RUN chmod +x /usr/local/bin/healthcheck.sh /usr/local/bin/docker-entr  0.2s
 => [builder 13/13] RUN echo $(date +%s) > /tmp/netstack_startup_time                         0.2s
 => [production  4/21] COPY --from=builder /opt/venv /opt/venv                                0.9s
 => [production  5/21] COPY --from=builder /app/tle_data /app/tle_data                        0.0s
 => [production  6/21] COPY --from=builder /app/data /app/data                                0.0s
 => [production  7/21] RUN if [ -f /app/data/phase0.env ]; then         while IFS='=' read -  0.2s
 => [production  8/21] WORKDIR /app                                                           0.0s
 => [production  9/21] COPY src/ ./src/                                                       0.1s
 => [production 10/21] COPY netstack_api/ ./netstack_api/                                     0.0s
 => [production 11/21] COPY config/ ./config/                                                 0.0s
 => [production 12/21] COPY docker/upf-extension/ ./docker/upf-extension/                     0.0s
 => [production 13/21] COPY scripts/ ./scripts/                                               0.0s
 => [production 14/21] COPY build_with_phase0_data.py /app/build_with_phase0_data.py          0.0s
 => [production 15/21] RUN mkdir -p /var/log/netstack /app/models /app/results /tmp/matplotl  0.2s
 => [production 16/21] RUN ls -lh /app/data/ && echo "Phase 0 precomputed data validation pa  0.2s
 => [production 17/21] RUN chown -R netstack:netstack /var/log/netstack /app/models /app/res  0.3s
 => [production 18/21] COPY docker/healthcheck.sh /usr/local/bin/healthcheck.sh               0.0s
 => [production 19/21] COPY docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh   0.0s
 => [production 20/21] COPY docker/smart-entrypoint.sh /usr/local/bin/smart-entrypoint.sh     0.0s
 => [production 21/21] RUN chmod +x /usr/local/bin/healthcheck.sh /usr/local/bin/docker-entr  0.2s
 => exporting to image                                                                        2.7s
 => => exporting layers                                                                       2.7s
 => => writing image sha256:22d09a55c65e5f40b89688c98853d6173fbfacefc9ecdb6ff56f636cd16c36c8  0.0s
 => => naming to docker.io/library/netstack-api:latest                                        0.0s
  - NetStack 核心映像建構完成
✅ 所有 NetStack 映像建置完成 (不使用快取)
make[2]: Leaving directory '/home/sat/ntn-stack/netstack'
✅ NetStack 服務構建完成 (不使用緩存)
make[1]: Leaving directory '/home/sat/ntn-stack'
make[1]: Entering directory '/home/sat/ntn-stack'
🔨 構建 SimWorld 服務 (不使用緩存)...
#1 [internal] load local bake definitions
#1 reading from stdin 1.03kB done
#1 DONE 0.0s

#2 [backend internal] load build definition from Dockerfile
#2 transferring dockerfile: 2.14kB done
#2 DONE 0.0s

#3 [frontend internal] load build definition from Dockerfile
#3 transferring dockerfile: 687B done
#3 DONE 0.0s

#4 [frontend internal] load metadata for docker.io/library/node:20-alpine
#4 ...

#5 [backend internal] load metadata for docker.io/library/python:3.11-slim
#5 DONE 0.2s

#6 [backend internal] load .dockerignore
#6 transferring context: 2B done
#6 DONE 0.0s

#7 [backend 1/8] FROM docker.io/library/python:3.11-slim@sha256:0ce77749ac83174a31d5e107ce0cfa6b28a2fd6b0615e029d9d84b39c48976ee
#7 DONE 0.0s

#8 [backend 2/8] WORKDIR /app
#8 CACHED

#9 [backend internal] load build context
#9 transferring context: 233.39MB 0.9s done
#9 DONE 0.9s

#10 [backend 3/8] RUN apt update && apt install -y --no-install-recommends     libgl1-mesa-glx     libegl1-mesa     libosmesa6     libopengl0     libglfw3     xvfb     llvm-dev     libllvm14     build-essential     curl     && apt clean && rm -rf /var/lib/apt/lists/*
#10 0.187
#10 0.187 WARNING: apt does not have a stable CLI interface. Use with caution in scripts.
#10 0.187
#10 0.262 Get:1 http://deb.debian.org/debian bookworm InRelease [151 kB]
#10 0.338 Get:2 http://deb.debian.org/debian bookworm-updates InRelease [55.4 kB]
#10 0.367 Get:3 http://deb.debian.org/debian-security bookworm-security InRelease [48.0 kB]
#10 0.396 Get:4 http://deb.debian.org/debian bookworm/main amd64 Packages [8793 kB]
#10 ...

#4 [frontend internal] load metadata for docker.io/library/node:20-alpine
#4 DONE 1.9s

#11 [frontend internal] load .dockerignore
#11 transferring context: 2B done
#11 DONE 0.0s

#12 [frontend 1/5] FROM docker.io/library/node:20-alpine@sha256:df02558528d3d3d0d621f112e232611aecfee7cbc654f6b375765f72bb262799
#12 resolve docker.io/library/node:20-alpine@sha256:df02558528d3d3d0d621f112e232611aecfee7cbc654f6b375765f72bb262799 done
#12 sha256:54225bd601967a0aa669ec9be621c24d8eeac874b698d55874018070898685c2 0B / 1.26MB 0.1s
#12 sha256:a9e48ad1219d4d11c6456a8db0fd5c11af46242d52edf84e17ab84a7bfd93809 0B / 445B 0.1s
#12 sha256:df02558528d3d3d0d621f112e232611aecfee7cbc654f6b375765f72bb262799 7.67kB / 7.67kB done
#12 sha256:ae6ee91a652d927de01d550c29f863a52f1da390c89df95f3ceba256d1e62604 1.72kB / 1.72kB done
#12 sha256:7cdef5a331927fafa250be6166052d8599bf5eb7b014342538c2cc79b70a081f 6.42kB / 6.42kB done
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 0B / 42.99MB 0.1s
#12 sha256:a9e48ad1219d4d11c6456a8db0fd5c11af46242d52edf84e17ab84a7bfd93809 445B / 445B 0.7s done
#12 sha256:54225bd601967a0aa669ec9be621c24d8eeac874b698d55874018070898685c2 1.26MB / 1.26MB 0.9s done
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 3.15MB / 42.99MB 2.0s
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 6.29MB / 42.99MB 2.3s
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 9.44MB / 42.99MB 2.5s
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 13.63MB / 42.99MB 2.9s
#12 ...

#13 [frontend internal] load build context
#13 transferring context: 593.80MB 3.0s done
#13 DONE 3.1s

#12 [frontend 1/5] FROM docker.io/library/node:20-alpine@sha256:df02558528d3d3d0d621f112e232611aecfee7cbc654f6b375765f72bb262799
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 18.87MB / 42.99MB 3.3s
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 22.02MB / 42.99MB 3.6s
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 26.21MB / 42.99MB 4.0s
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 31.46MB / 42.99MB 4.4s
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 34.60MB / 42.99MB 4.7s
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 37.75MB / 42.99MB 5.0s
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 41.94MB / 42.99MB 5.4s
#12 sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 42.99MB / 42.99MB 5.7s done
#12 extracting sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e
#12 extracting sha256:8c59d92d6fc9f01af4aaa86824be72b74bd4d940c4c46aa95d9710bfa46c975e 0.6s done
#12 extracting sha256:54225bd601967a0aa669ec9be621c24d8eeac874b698d55874018070898685c2 0.0s done
#12 extracting sha256:a9e48ad1219d4d11c6456a8db0fd5c11af46242d52edf84e17ab84a7bfd93809 done
#12 DONE 6.3s

#10 [backend 3/8] RUN apt update && apt install -y --no-install-recommends     libgl1-mesa-glx     libegl1-mesa     libosmesa6     libopengl0     libglfw3     xvfb     llvm-dev     libllvm14     build-essential     curl     && apt clean && rm -rf /var/lib/apt/lists/*
#10 3.215 Get:5 http://deb.debian.org/debian bookworm-updates/main amd64 Packages [6916 B]
#10 3.222 Get:6 http://deb.debian.org/debian-security bookworm-security/main amd64 Packages [272 kB]
#10 3.696 Fetched 9327 kB in 3s (2667 kB/s)
#10 3.696 Reading package lists...
#10 3.954 Building dependency tree...
#10 4.014 Reading state information...
#10 4.020 2 packages can be upgraded. Run 'apt list --upgradable' to see them.
#10 4.024
#10 4.024 WARNING: apt does not have a stable CLI interface. Use with caution in scripts.
#10 4.024
#10 4.034 Reading package lists...
#10 4.302 Building dependency tree...
#10 4.360 Reading state information...
#10 4.426 The following additional packages will be installed:
#10 4.426   binutils binutils-common binutils-x86-64-linux-gnu bzip2 cpp cpp-12 dpkg-dev
#10 4.426   g++ g++-12 gcc gcc-12 icu-devtools libasan8 libatomic1 libbinutils
#10 4.426   libbrotli1 libbsd0 libc-dev-bin libc6-dev libcc1-0 libclang-cpp14
#10 4.426   libcrypt-dev libctf-nobfd0 libctf0 libcurl3-nss libcurl4 libdpkg-perl
#10 4.426   libdrm-amdgpu1 libdrm-common libdrm-intel1 libdrm-nouveau2 libdrm-radeon1
#10 4.426   libdrm2 libedit2 libegl-mesa0 libegl1 libelf1 libexpat1 libffi-dev
#10 4.426   libfontenc1 libfreetype6 libgbm1 libgcc-12-dev libgdbm-compat4 libgl1
#10 4.426   libgl1-mesa-dri libglapi-mesa libglvnd0 libglx-mesa0 libglx0 libgomp1
#10 4.426   libgprofng0 libice6 libicu-dev libicu72 libisl23 libitm1 libjansson4
#10 4.426   libldap-2.5-0 libllvm15 liblsan0 libmpc3 libmpfr6 libncurses-dev libncurses6
#10 4.426   libnghttp2-14 libnsl-dev libnspr4 libnss3 libpciaccess0 libperl5.36 libpfm4
#10 4.426   libpixman-1-0 libpng16-16 libpsl5 libpython3-stdlib libpython3.11-minimal
#10 4.426   libpython3.11-stdlib libquadmath0 librtmp1 libsasl2-2 libsasl2-modules-db
#10 4.426   libsensors-config libsensors5 libsm6 libssh2-1 libstdc++-12-dev libtinfo-dev
#10 4.426   libtirpc-dev libtsan2 libubsan1 libunwind8 libwayland-client0
#10 4.426   libwayland-server0 libx11-6 libx11-data libx11-xcb1 libxau6 libxaw7
#10 4.426   libxcb-dri2-0 libxcb-dri3-0 libxcb-glx0 libxcb-present0 libxcb-randr0
#10 4.426   libxcb-shm0 libxcb-sync1 libxcb-xfixes0 libxcb1 libxdmcp6 libxext6
#10 4.426   libxfixes3 libxfont2 libxkbfile1 libxml2 libxml2-dev libxmu6 libxpm4
#10 4.426   libxrandr2 libxrender1 libxshmfence1 libxt6 libxxf86vm1 libyaml-0-2 libz3-4
#10 4.426   libz3-dev linux-libc-dev llvm llvm-14 llvm-14-dev llvm-14-linker-tools
#10 4.426   llvm-14-runtime llvm-14-tools llvm-runtime make media-types nss-plugin-pem
#10 4.427   patch perl perl-modules-5.36 python3 python3-minimal python3-pkg-resources
#10 4.427   python3-pygments python3-yaml python3.11 python3.11-minimal rpcsvc-proto
#10 4.427   x11-common x11-xkb-utils xkb-data xserver-common xz-utils
#10 4.427 Suggested packages:
#10 4.427   binutils-doc bzip2-doc cpp-doc gcc-12-locales cpp-12-doc debian-keyring
#10 4.427   g++-multilib g++-12-multilib gcc-12-doc gcc-multilib manpages-dev autoconf
#10 4.427   automake libtool flex bison gdb gcc-doc gcc-12-multilib glibc-doc gnupg | sq
#10 4.427   | sqop | pgpainless-cli sensible-utils git bzr libgles1 libgles2 libvulkan1
#10 4.427   icu-doc ncurses-doc pciutils lm-sensors libstdc++-12-doc pkg-config
#10 4.427   llvm-14-doc make-doc ed diffutils-doc perl-doc libterm-readline-gnu-perl
#10 4.427   | libterm-readline-perl-perl libtap-harness-archive-perl python3-doc
#10 4.427   python3-tk python3-venv python3-setuptools python-pygments-doc
#10 4.427   ttf-bitstream-vera python3.11-venv python3.11-doc binfmt-support
#10 4.427 Recommended packages:
#10 4.427   fakeroot gnupg | sq | sqop | pgpainless-cli libalgorithm-merge-perl manpages
#10 4.427   manpages-dev libc-devtools libfile-fcntllock-perl liblocale-gettext-perl
#10 4.427   libldap-common libgpm2 publicsuffix libsasl2-modules binfmt-support
#10 4.427   | systemd xfonts-base xauth
#10 4.859 The following NEW packages will be installed:
#10 4.859   binutils binutils-common binutils-x86-64-linux-gnu build-essential bzip2 cpp
#10 4.859   cpp-12 curl dpkg-dev g++ g++-12 gcc gcc-12 icu-devtools libasan8 libatomic1
#10 4.859   libbinutils libbrotli1 libbsd0 libc-dev-bin libc6-dev libcc1-0
#10 4.859   libclang-cpp14 libcrypt-dev libctf-nobfd0 libctf0 libcurl3-nss libcurl4
#10 4.859   libdpkg-perl libdrm-amdgpu1 libdrm-common libdrm-intel1 libdrm-nouveau2
#10 4.859   libdrm-radeon1 libdrm2 libedit2 libegl-mesa0 libegl1 libegl1-mesa libelf1
#10 4.859   libexpat1 libffi-dev libfontenc1 libfreetype6 libgbm1 libgcc-12-dev
#10 4.859   libgdbm-compat4 libgl1 libgl1-mesa-dri libgl1-mesa-glx libglapi-mesa
#10 4.859   libglfw3 libglvnd0 libglx-mesa0 libglx0 libgomp1 libgprofng0 libice6
#10 4.859   libicu-dev libicu72 libisl23 libitm1 libjansson4 libldap-2.5-0 libllvm14
#10 4.859   libllvm15 liblsan0 libmpc3 libmpfr6 libncurses-dev libncurses6 libnghttp2-14
#10 4.859   libnsl-dev libnspr4 libnss3 libopengl0 libosmesa6 libpciaccess0 libperl5.36
#10 4.859   libpfm4 libpixman-1-0 libpng16-16 libpsl5 libpython3-stdlib
#10 4.859   libpython3.11-minimal libpython3.11-stdlib libquadmath0 librtmp1 libsasl2-2
#10 4.859   libsasl2-modules-db libsensors-config libsensors5 libsm6 libssh2-1
#10 4.859   libstdc++-12-dev libtinfo-dev libtirpc-dev libtsan2 libubsan1 libunwind8
#10 4.859   libwayland-client0 libwayland-server0 libx11-6 libx11-data libx11-xcb1
#10 4.859   libxau6 libxaw7 libxcb-dri2-0 libxcb-dri3-0 libxcb-glx0 libxcb-present0
#10 4.859   libxcb-randr0 libxcb-shm0 libxcb-sync1 libxcb-xfixes0 libxcb1 libxdmcp6
#10 4.859   libxext6 libxfixes3 libxfont2 libxkbfile1 libxml2 libxml2-dev libxmu6
#10 4.859   libxpm4 libxrandr2 libxrender1 libxshmfence1 libxt6 libxxf86vm1 libyaml-0-2
#10 4.859   libz3-4 libz3-dev linux-libc-dev llvm llvm-14 llvm-14-dev
#10 4.859   llvm-14-linker-tools llvm-14-runtime llvm-14-tools llvm-dev llvm-runtime
#10 4.859   make media-types nss-plugin-pem patch perl perl-modules-5.36 python3
#10 4.859   python3-minimal python3-pkg-resources python3-pygments python3-yaml
#10 4.859   python3.11 python3.11-minimal rpcsvc-proto x11-common x11-xkb-utils xkb-data
#10 4.859   xserver-common xvfb xz-utils
#10 4.931 0 upgraded, 162 newly installed, 0 to remove and 2 not upgraded.
#10 4.931 Need to get 240 MB of archives.
#10 4.931 After this operation, 1164 MB of additional disk space will be used.
#10 4.931 Get:1 http://deb.debian.org/debian bookworm/main amd64 perl-modules-5.36 all 5.36.0-7+deb12u2 [2815 kB]
#10 ...

#14 [frontend 2/5] WORKDIR /app
#14 DONE 0.2s

#15 [frontend 3/5] COPY package.json yarn.lock* package-lock.json* ./
#15 DONE 0.1s

#10 [backend 3/8] RUN apt update && apt install -y --no-install-recommends     libgl1-mesa-glx     libegl1-mesa     libosmesa6     libopengl0     libglfw3     xvfb     llvm-dev     libllvm14     build-essential     curl     && apt clean && rm -rf /var/lib/apt/lists/*
#10 ...

#16 [frontend 4/5] RUN npm install
#16 ...

#10 [backend 3/8] RUN apt update && apt install -y --no-install-recommends     libgl1-mesa-glx     libegl1-mesa     libosmesa6     libopengl0     libglfw3     xvfb     llvm-dev     libllvm14     build-essential     curl     && apt clean && rm -rf /var/lib/apt/lists/*
#10 8.986 Get:2 http://deb.debian.org/debian bookworm/main amd64 libgdbm-compat4 amd64 1.23-3 [48.2 kB]
#10 9.018 Get:3 http://deb.debian.org/debian bookworm/main amd64 libperl5.36 amd64 5.36.0-7+deb12u2 [4207 kB]
#10 ...

#16 [frontend 4/5] RUN npm install
#16 11.96
#16 11.96 added 369 packages, and audited 370 packages in 12s
#16 11.96
#16 11.96 73 packages are looking for funding
#16 11.96   run `npm fund` for details
#16 11.96
#16 11.96 2 vulnerabilities (1 low, 1 critical)
#16 11.96
#16 11.96 To address all issues, run:
#16 11.96   npm audit fix
#16 11.96
#16 11.96 Run `npm audit` for details.
#16 11.96 npm notice
#16 11.96 npm notice New major version of npm available! 10.8.2 -> 11.5.2
#16 11.96 npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.5.2
#16 11.96 npm notice To update run: npm install -g npm@11.5.2
#16 11.96 npm notice
#16 DONE 12.1s

#10 [backend 3/8] RUN apt update && apt install -y --no-install-recommends     libgl1-mesa-glx     libegl1-mesa     libosmesa6     libopengl0     libglfw3     xvfb     llvm-dev     libllvm14     build-essential     curl     && apt clean && rm -rf /var/lib/apt/lists/*
#10 ...

#17 [frontend 5/5] COPY . .
#17 DONE 2.4s

#10 [backend 3/8] RUN apt update && apt install -y --no-install-recommends     libgl1-mesa-glx     libegl1-mesa     libosmesa6     libopengl0     libglfw3     xvfb     llvm-dev     libllvm14     build-essential     curl     && apt clean && rm -rf /var/lib/apt/lists/*
#10 22.32 Get:4 http://deb.debian.org/debian bookworm/main amd64 perl amd64 5.36.0-7+deb12u2 [239 kB]
#10 22.41 Get:5 http://deb.debian.org/debian bookworm/main amd64 libpython3.11-minimal amd64 3.11.2-6+deb12u6 [817 kB]
#10 22.68 Get:6 http://deb.debian.org/debian bookworm/main amd64 libexpat1 amd64 2.5.0-1+deb12u1 [98.9 kB]
#10 22.71 Get:7 http://deb.debian.org/debian bookworm/main amd64 python3.11-minimal amd64 3.11.2-6+deb12u6 [2064 kB]
#10 23.28 Get:8 http://deb.debian.org/debian bookworm/main amd64 python3-minimal amd64 3.11.2-1+b1 [26.3 kB]
#10 23.28 Get:9 http://deb.debian.org/debian bookworm/main amd64 media-types all 10.0.0 [26.1 kB]
#10 23.29 Get:10 http://deb.debian.org/debian bookworm/main amd64 libpython3.11-stdlib amd64 3.11.2-6+deb12u6 [1798 kB]
#10 23.83 Get:11 http://deb.debian.org/debian bookworm/main amd64 python3.11 amd64 3.11.2-6+deb12u6 [573 kB]
#10 23.99 Get:12 http://deb.debian.org/debian bookworm/main amd64 libpython3-stdlib amd64 3.11.2-1+b1 [9312 B]
#10 24.00 Get:13 http://deb.debian.org/debian bookworm/main amd64 python3 amd64 3.11.2-1+b1 [26.3 kB]
#10 24.01 Get:14 http://deb.debian.org/debian bookworm/main amd64 bzip2 amd64 1.0.8-5+b1 [49.8 kB]
#10 24.02 Get:15 http://deb.debian.org/debian bookworm/main amd64 xz-utils amd64 5.4.1-1 [471 kB]
#10 24.15 Get:16 http://deb.debian.org/debian bookworm/main amd64 binutils-common amd64 2.40-2 [2487 kB]
#10 24.75 Get:17 http://deb.debian.org/debian bookworm/main amd64 libbinutils amd64 2.40-2 [572 kB]
#10 24.88 Get:18 http://deb.debian.org/debian bookworm/main amd64 libctf-nobfd0 amd64 2.40-2 [153 kB]
#10 24.91 Get:19 http://deb.debian.org/debian bookworm/main amd64 libctf0 amd64 2.40-2 [89.8 kB]
#10 24.93 Get:20 http://deb.debian.org/debian bookworm/main amd64 libgprofng0 amd64 2.40-2 [812 kB]
#10 25.09 Get:21 http://deb.debian.org/debian bookworm/main amd64 libjansson4 amd64 2.14-2 [40.8 kB]
#10 25.10 Get:22 http://deb.debian.org/debian bookworm/main amd64 binutils-x86-64-linux-gnu amd64 2.40-2 [2246 kB]
#10 25.57 Get:23 http://deb.debian.org/debian bookworm/main amd64 binutils amd64 2.40-2 [65.0 kB]
#10 25.59 Get:24 http://deb.debian.org/debian bookworm/main amd64 libc-dev-bin amd64 2.36-9+deb12u10 [47.1 kB]
#10 25.60 Get:25 http://deb.debian.org/debian-security bookworm-security/main amd64 linux-libc-dev amd64 6.1.140-1 [2145 kB]
#10 26.11 Get:26 http://deb.debian.org/debian bookworm/main amd64 libcrypt-dev amd64 1:4.4.33-2 [118 kB]
#10 26.13 Get:27 http://deb.debian.org/debian bookworm/main amd64 libtirpc-dev amd64 1.3.3+ds-1 [191 kB]
#10 26.17 Get:28 http://deb.debian.org/debian bookworm/main amd64 libnsl-dev amd64 1.3.0-2 [66.4 kB]
#10 26.19 Get:29 http://deb.debian.org/debian bookworm/main amd64 rpcsvc-proto amd64 1.4.3-1 [63.3 kB]
#10 26.20 Get:30 http://deb.debian.org/debian bookworm/main amd64 libc6-dev amd64 2.36-9+deb12u10 [1903 kB]
#10 26.60 Get:31 http://deb.debian.org/debian bookworm/main amd64 libisl23 amd64 0.25-1.1 [683 kB]
#10 26.79 Get:32 http://deb.debian.org/debian bookworm/main amd64 libmpfr6 amd64 4.2.0-1 [701 kB]
#10 26.97 Get:33 http://deb.debian.org/debian bookworm/main amd64 libmpc3 amd64 1.3.1-1 [51.5 kB]
#10 26.98 Get:34 http://deb.debian.org/debian bookworm/main amd64 cpp-12 amd64 12.2.0-14+deb12u1 [9768 kB]
#10 ...

#18 [frontend] exporting to image
#18 exporting layers 4.6s done
#18 writing image sha256:4a3bc91f028e02642884a367ede9cadddab6762a5699e8b70c6860c7923a30ef done
#18 naming to docker.io/library/simworld-frontend done
#18 DONE 4.6s

#19 [frontend] resolving provenance for metadata file
#19 DONE 0.0s

#10 [backend 3/8] RUN apt update && apt install -y --no-install-recommends     libgl1-mesa-glx     libegl1-mesa     libosmesa6     libopengl0     libglfw3     xvfb     llvm-dev     libllvm14     build-essential     curl     && apt clean && rm -rf /var/lib/apt/lists/*
#10 28.94 Get:35 http://deb.debian.org/debian bookworm/main amd64 cpp amd64 4:12.2.0-3 [6836 B]
#10 28.94 Get:36 http://deb.debian.org/debian bookworm/main amd64 libcc1-0 amd64 12.2.0-14+deb12u1 [41.7 kB]
#10 28.95 Get:37 http://deb.debian.org/debian bookworm/main amd64 libgomp1 amd64 12.2.0-14+deb12u1 [116 kB]
#10 28.98 Get:38 http://deb.debian.org/debian bookworm/main amd64 libitm1 amd64 12.2.0-14+deb12u1 [26.1 kB]
#10 28.98 Get:39 http://deb.debian.org/debian bookworm/main amd64 libatomic1 amd64 12.2.0-14+deb12u1 [9376 B]
#10 28.98 Get:40 http://deb.debian.org/debian bookworm/main amd64 libasan8 amd64 12.2.0-14+deb12u1 [2193 kB]
#10 29.42 Get:41 http://deb.debian.org/debian bookworm/main amd64 liblsan0 amd64 12.2.0-14+deb12u1 [969 kB]
#10 29.60 Get:42 http://deb.debian.org/debian bookworm/main amd64 libtsan2 amd64 12.2.0-14+deb12u1 [2197 kB]
#10 30.13 Get:43 http://deb.debian.org/debian bookworm/main amd64 libubsan1 amd64 12.2.0-14+deb12u1 [883 kB]
#10 30.32 Get:44 http://deb.debian.org/debian bookworm/main amd64 libquadmath0 amd64 12.2.0-14+deb12u1 [145 kB]
#10 30.35 Get:45 http://deb.debian.org/debian bookworm/main amd64 libgcc-12-dev amd64 12.2.0-14+deb12u1 [2437 kB]
#10 30.83 Get:46 http://deb.debian.org/debian bookworm/main amd64 gcc-12 amd64 12.2.0-14+deb12u1 [19.3 MB]
#10 33.58 Get:47 http://deb.debian.org/debian bookworm/main amd64 gcc amd64 4:12.2.0-3 [5216 B]
#10 33.58 Get:48 http://deb.debian.org/debian bookworm/main amd64 libstdc++-12-dev amd64 12.2.0-14+deb12u1 [2047 kB]
#10 33.89 Get:49 http://deb.debian.org/debian bookworm/main amd64 g++-12 amd64 12.2.0-14+deb12u1 [10.7 MB]
#10 35.29 Get:50 http://deb.debian.org/debian bookworm/main amd64 g++ amd64 4:12.2.0-3 [1356 B]
#10 35.29 Get:51 http://deb.debian.org/debian bookworm/main amd64 make amd64 4.3-4.1 [396 kB]
#10 35.33 Get:52 http://deb.debian.org/debian bookworm/main amd64 libdpkg-perl all 1.21.22 [603 kB]
#10 35.41 Get:53 http://deb.debian.org/debian bookworm/main amd64 patch amd64 2.7.6-7 [128 kB]
#10 35.42 Get:54 http://deb.debian.org/debian bookworm/main amd64 dpkg-dev all 1.21.22 [1353 kB]
#10 35.58 Get:55 http://deb.debian.org/debian bookworm/main amd64 build-essential amd64 12.9 [7704 B]
#10 35.58 Get:56 http://deb.debian.org/debian bookworm/main amd64 libbrotli1 amd64 1.0.9-2+b6 [275 kB]
#10 35.61 Get:57 http://deb.debian.org/debian bookworm/main amd64 libsasl2-modules-db amd64 2.1.28+dfsg-10 [20.3 kB]
#10 35.61 Get:58 http://deb.debian.org/debian bookworm/main amd64 libsasl2-2 amd64 2.1.28+dfsg-10 [59.7 kB]
#10 35.62 Get:59 http://deb.debian.org/debian bookworm/main amd64 libldap-2.5-0 amd64 2.5.13+dfsg-5 [183 kB]
#10 35.64 Get:60 http://deb.debian.org/debian bookworm/main amd64 libnghttp2-14 amd64 1.52.0-1+deb12u2 [73.0 kB]
#10 35.65 Get:61 http://deb.debian.org/debian bookworm/main amd64 libpsl5 amd64 0.21.2-1 [58.7 kB]
#10 35.65 Get:62 http://deb.debian.org/debian bookworm/main amd64 librtmp1 amd64 2.4+20151223.gitfa8646d.1-2+b2 [60.8 kB]
#10 35.66 Get:63 http://deb.debian.org/debian bookworm/main amd64 libssh2-1 amd64 1.10.0-3+b1 [179 kB]
#10 35.68 Get:64 http://deb.debian.org/debian bookworm/main amd64 libcurl4 amd64 7.88.1-10+deb12u12 [391 kB]
#10 35.73 Get:65 http://deb.debian.org/debian bookworm/main amd64 curl amd64 7.88.1-10+deb12u12 [315 kB]
#10 35.76 Get:66 http://deb.debian.org/debian-security bookworm-security/main amd64 libicu72 amd64 72.1-3+deb12u1 [9376 kB]
#10 36.73 Get:67 http://deb.debian.org/debian-security bookworm-security/main amd64 icu-devtools amd64 72.1-3+deb12u1 [206 kB]
#10 36.75 Get:68 http://deb.debian.org/debian bookworm/main amd64 libbsd0 amd64 0.11.7-2 [117 kB]
#10 36.76 Get:69 http://deb.debian.org/debian bookworm/main amd64 libedit2 amd64 3.1-20221030-2 [93.0 kB]
#10 36.77 Get:70 http://deb.debian.org/debian-security bookworm-security/main amd64 libxml2 amd64 2.9.14+dfsg-1.3~deb12u2 [687 kB]
#10 36.84 Get:71 http://deb.debian.org/debian bookworm/main amd64 libz3-4 amd64 4.8.12-3.1 [7216 kB]
#10 37.51 Get:72 http://deb.debian.org/debian bookworm/main amd64 libllvm14 amd64 1:14.0.6-12 [21.8 MB]
#10 39.86 Get:73 http://deb.debian.org/debian bookworm/main amd64 libclang-cpp14 amd64 1:14.0.6-12 [11.1 MB]
#10 42.00 Get:74 http://deb.debian.org/debian bookworm/main amd64 libnspr4 amd64 2:4.35-1 [113 kB]
#10 42.01 Get:75 http://deb.debian.org/debian bookworm/main amd64 libnss3 amd64 2:3.87.1-1+deb12u1 [1331 kB]
#10 42.21 Get:76 http://deb.debian.org/debian bookworm/main amd64 nss-plugin-pem amd64 1.0.8+1-1 [54.6 kB]
#10 42.22 Get:77 http://deb.debian.org/debian bookworm/main amd64 libcurl3-nss amd64 7.88.1-10+deb12u12 [395 kB]
#10 42.27 Get:78 http://deb.debian.org/debian bookworm/main amd64 libdrm-common all 2.4.114-1 [7112 B]
#10 42.27 Get:79 http://deb.debian.org/debian bookworm/main amd64 libdrm2 amd64 2.4.114-1+b1 [37.5 kB]
#10 42.28 Get:80 http://deb.debian.org/debian bookworm/main amd64 libdrm-amdgpu1 amd64 2.4.114-1+b1 [20.9 kB]
#10 42.28 Get:81 http://deb.debian.org/debian bookworm/main amd64 libpciaccess0 amd64 0.17-2 [51.4 kB]
#10 42.29 Get:82 http://deb.debian.org/debian bookworm/main amd64 libdrm-intel1 amd64 2.4.114-1+b1 [64.0 kB]
#10 42.30 Get:83 http://deb.debian.org/debian bookworm/main amd64 libdrm-nouveau2 amd64 2.4.114-1+b1 [19.1 kB]
#10 42.30 Get:84 http://deb.debian.org/debian bookworm/main amd64 libdrm-radeon1 amd64 2.4.114-1+b1 [21.8 kB]
#10 42.31 Get:85 http://deb.debian.org/debian bookworm/main amd64 libwayland-server0 amd64 1.21.0-1 [35.9 kB]
#10 42.31 Get:86 http://deb.debian.org/debian bookworm/main amd64 libgbm1 amd64 22.3.6-1+deb12u1 [38.0 kB]
#10 42.32 Get:87 http://deb.debian.org/debian bookworm/main amd64 libglapi-mesa amd64 22.3.6-1+deb12u1 [35.7 kB]
#10 42.32 Get:88 http://deb.debian.org/debian bookworm/main amd64 libwayland-client0 amd64 1.21.0-1 [28.3 kB]
#10 42.32 Get:89 http://deb.debian.org/debian bookworm/main amd64 libxau6 amd64 1:1.0.9-1 [19.7 kB]
#10 42.33 Get:90 http://deb.debian.org/debian bookworm/main amd64 libxdmcp6 amd64 1:1.1.2-3 [26.3 kB]
#10 42.33 Get:91 http://deb.debian.org/debian bookworm/main amd64 libxcb1 amd64 1.15-1 [144 kB]
#10 42.36 Get:92 http://deb.debian.org/debian bookworm/main amd64 libx11-data all 2:1.8.4-2+deb12u2 [292 kB]
#10 42.39 Get:93 http://deb.debian.org/debian bookworm/main amd64 libx11-6 amd64 2:1.8.4-2+deb12u2 [760 kB]
#10 42.52 Get:94 http://deb.debian.org/debian bookworm/main amd64 libx11-xcb1 amd64 2:1.8.4-2+deb12u2 [192 kB]
#10 42.54 Get:95 http://deb.debian.org/debian bookworm/main amd64 libxcb-dri2-0 amd64 1.15-1 [107 kB]
#10 42.56 Get:96 http://deb.debian.org/debian bookworm/main amd64 libxcb-dri3-0 amd64 1.15-1 [107 kB]
#10 42.58 Get:97 http://deb.debian.org/debian bookworm/main amd64 libxcb-present0 amd64 1.15-1 [105 kB]
#10 42.60 Get:98 http://deb.debian.org/debian bookworm/main amd64 libxcb-randr0 amd64 1.15-1 [117 kB]
#10 42.63 Get:99 http://deb.debian.org/debian bookworm/main amd64 libxcb-sync1 amd64 1.15-1 [109 kB]
#10 42.65 Get:100 http://deb.debian.org/debian bookworm/main amd64 libxcb-xfixes0 amd64 1.15-1 [109 kB]
#10 42.67 Get:101 http://deb.debian.org/debian bookworm/main amd64 libxshmfence1 amd64 1.3-1 [8820 B]
#10 42.67 Get:102 http://deb.debian.org/debian bookworm/main amd64 libegl-mesa0 amd64 22.3.6-1+deb12u1 [114 kB]
#10 42.69 Get:103 http://deb.debian.org/debian bookworm/main amd64 libglvnd0 amd64 1.6.0-1 [51.8 kB]
#10 42.70 Get:104 http://deb.debian.org/debian bookworm/main amd64 libegl1 amd64 1.6.0-1 [33.7 kB]
#10 42.71 Get:105 http://deb.debian.org/debian bookworm/main amd64 libegl1-mesa amd64 22.3.6-1+deb12u1 [14.5 kB]
#10 42.71 Get:106 http://deb.debian.org/debian bookworm/main amd64 libelf1 amd64 0.188-2.1 [174 kB]
#10 42.74 Get:107 http://deb.debian.org/debian bookworm/main amd64 libffi-dev amd64 3.4.4-1 [59.4 kB]
#10 42.75 Get:108 http://deb.debian.org/debian bookworm/main amd64 libfontenc1 amd64 1:1.1.4-1 [24.3 kB]
#10 42.76 Get:109 http://deb.debian.org/debian bookworm/main amd64 libpng16-16 amd64 1.6.39-2 [276 kB]
#10 42.81 Get:110 http://deb.debian.org/debian bookworm/main amd64 libfreetype6 amd64 2.12.1+dfsg-5+deb12u4 [398 kB]
#10 42.88 Get:111 http://deb.debian.org/debian bookworm/main amd64 libxcb-glx0 amd64 1.15-1 [122 kB]
#10 42.91 Get:112 http://deb.debian.org/debian bookworm/main amd64 libxcb-shm0 amd64 1.15-1 [105 kB]
#10 42.92 Get:113 http://deb.debian.org/debian bookworm/main amd64 libxext6 amd64 2:1.3.4-1+b1 [52.9 kB]
#10 42.93 Get:114 http://deb.debian.org/debian bookworm/main amd64 libxfixes3 amd64 1:6.0.0-2 [22.7 kB]
#10 42.94 Get:115 http://deb.debian.org/debian bookworm/main amd64 libxxf86vm1 amd64 1:1.1.4-1+b2 [20.8 kB]
#10 42.94 Get:116 http://deb.debian.org/debian bookworm/main amd64 libllvm15 amd64 1:15.0.6-4+b1 [23.1 MB]
#10 47.13 Get:117 http://deb.debian.org/debian bookworm/main amd64 libsensors-config all 1:3.6.0-7.1 [14.3 kB]
#10 47.13 Get:118 http://deb.debian.org/debian bookworm/main amd64 libsensors5 amd64 1:3.6.0-7.1 [34.2 kB]
#10 47.13 Get:119 http://deb.debian.org/debian bookworm/main amd64 libgl1-mesa-dri amd64 22.3.6-1+deb12u1 [7239 kB]
#10 48.13 Get:120 http://deb.debian.org/debian bookworm/main amd64 libglx-mesa0 amd64 22.3.6-1+deb12u1 [147 kB]
#10 48.15 Get:121 http://deb.debian.org/debian bookworm/main amd64 libglx0 amd64 1.6.0-1 [34.4 kB]
#10 48.16 Get:122 http://deb.debian.org/debian bookworm/main amd64 libgl1 amd64 1.6.0-1 [88.4 kB]
#10 48.17 Get:123 http://deb.debian.org/debian bookworm/main amd64 libgl1-mesa-glx amd64 22.3.6-1+deb12u1 [14.5 kB]
#10 48.18 Get:124 http://deb.debian.org/debian bookworm/main amd64 libglfw3 amd64 3.3.8-1 [75.8 kB]
#10 48.19 Get:125 http://deb.debian.org/debian bookworm/main amd64 x11-common all 1:7.7+23 [252 kB]
#10 48.23 Get:126 http://deb.debian.org/debian bookworm/main amd64 libice6 amd64 2:1.0.10-1 [58.5 kB]
#10 48.24 Get:127 http://deb.debian.org/debian-security bookworm-security/main amd64 libicu-dev amd64 72.1-3+deb12u1 [10.3 MB]
#10 49.69 Get:128 http://deb.debian.org/debian bookworm/main amd64 libncurses6 amd64 6.4-4 [103 kB]
#10 49.70 Get:129 http://deb.debian.org/debian bookworm/main amd64 libncurses-dev amd64 6.4-4 [349 kB]
#10 49.74 Get:130 http://deb.debian.org/debian bookworm/main amd64 libosmesa6 amd64 22.3.6-1+deb12u1 [2905 kB]
#10 50.09 Get:131 http://deb.debian.org/debian bookworm/main amd64 libpfm4 amd64 4.13.0-1 [294 kB]
#10 50.13 Get:132 http://deb.debian.org/debian bookworm/main amd64 libpixman-1-0 amd64 0.42.2-1 [546 kB]
#10 50.19 Get:133 http://deb.debian.org/debian bookworm/main amd64 libsm6 amd64 2:1.2.3-1 [35.1 kB]
#10 50.19 Get:134 http://deb.debian.org/debian bookworm/main amd64 libtinfo-dev amd64 6.4-4 [924 B]
#10 50.19 Get:135 http://deb.debian.org/debian bookworm/main amd64 libunwind8 amd64 1.6.2-3 [51.2 kB]
#10 50.20 Get:136 http://deb.debian.org/debian bookworm/main amd64 libxt6 amd64 1:1.2.1-1.1 [186 kB]
#10 50.22 Get:137 http://deb.debian.org/debian bookworm/main amd64 libxmu6 amd64 2:1.1.3-3 [60.1 kB]
#10 50.23 Get:138 http://deb.debian.org/debian bookworm/main amd64 libxpm4 amd64 1:3.5.12-1.1+deb12u1 [48.6 kB]
#10 50.23 Get:139 http://deb.debian.org/debian bookworm/main amd64 libxaw7 amd64 2:1.0.14-1 [201 kB]
#10 50.25 Get:140 http://deb.debian.org/debian bookworm/main amd64 libxfont2 amd64 1:2.0.6-1 [136 kB]
#10 50.27 Get:141 http://deb.debian.org/debian bookworm/main amd64 libxkbfile1 amd64 1:1.1.0-1 [75.2 kB]
#10 50.28 Get:142 http://deb.debian.org/debian-security bookworm-security/main amd64 libxml2-dev amd64 2.9.14+dfsg-1.3~deb12u2 [783 kB]
#10 50.37 Get:143 http://deb.debian.org/debian bookworm/main amd64 libxrender1 amd64 1:0.9.10-1.1 [33.2 kB]
#10 50.37 Get:144 http://deb.debian.org/debian bookworm/main amd64 libxrandr2 amd64 2:1.5.2-2+b1 [39.2 kB]
#10 50.38 Get:145 http://deb.debian.org/debian bookworm/main amd64 libyaml-0-2 amd64 0.2.5-1 [53.6 kB]
#10 50.38 Get:146 http://deb.debian.org/debian bookworm/main amd64 libz3-dev amd64 4.8.12-3.1 [90.6 kB]
#10 50.39 Get:147 http://deb.debian.org/debian bookworm/main amd64 llvm-14-runtime amd64 1:14.0.6-12 [477 kB]
#10 50.45 Get:148 http://deb.debian.org/debian bookworm/main amd64 llvm-runtime amd64 1:14.0-55.7~deb12u1 [4812 B]
#10 50.45 Get:149 http://deb.debian.org/debian bookworm/main amd64 llvm-14-linker-tools amd64 1:14.0.6-12 [1288 kB]
#10 50.59 Get:150 http://deb.debian.org/debian bookworm/main amd64 llvm-14 amd64 1:14.0.6-12 [11.7 MB]
#10 51.77 Get:151 http://deb.debian.org/debian bookworm/main amd64 llvm amd64 1:14.0-55.7~deb12u1 [7212 B]
#10 51.77 Get:152 http://deb.debian.org/debian bookworm/main amd64 python3-pkg-resources all 66.1.1-1+deb12u1 [296 kB]
#10 51.79 Get:153 http://deb.debian.org/debian bookworm/main amd64 python3-pygments all 2.14.0+dfsg-1 [783 kB]
#10 51.87 Get:154 http://deb.debian.org/debian bookworm/main amd64 python3-yaml amd64 6.0-3+b2 [119 kB]
#10 51.88 Get:155 http://deb.debian.org/debian bookworm/main amd64 llvm-14-tools amd64 1:14.0.6-12 [405 kB]
#10 51.92 Get:156 http://deb.debian.org/debian bookworm/main amd64 llvm-14-dev amd64 1:14.0.6-12 [33.9 MB]
#10 56.51 Get:157 http://deb.debian.org/debian bookworm/main amd64 llvm-dev amd64 1:14.0-55.7~deb12u1 [5064 B]
#10 56.51 Get:158 http://deb.debian.org/debian bookworm/main amd64 x11-xkb-utils amd64 7.7+7 [165 kB]
#10 56.52 Get:159 http://deb.debian.org/debian bookworm/main amd64 xkb-data all 2.35.1-1 [764 kB]
#10 56.62 Get:160 http://deb.debian.org/debian-security bookworm-security/main amd64 xserver-common all 2:21.1.7-3+deb12u10 [2383 kB]
#10 56.89 Get:161 http://deb.debian.org/debian-security bookworm-security/main amd64 xvfb amd64 2:21.1.7-3+deb12u10 [3152 kB]
#10 57.23 Get:162 http://deb.debian.org/debian bookworm/main amd64 libopengl0 amd64 1.6.0-1 [30.6 kB]
#10 57.32 debconf: delaying package configuration, since apt-utils is not installed
#10 57.33 Fetched 240 MB in 52s (4582 kB/s)
#10 57.35 Selecting previously unselected package perl-modules-5.36.
(Reading database ... 6688 files and directories currently installed.)
#10 57.35 Preparing to unpack .../0-perl-modules-5.36_5.36.0-7+deb12u2_all.deb ...
#10 57.36 Unpacking perl-modules-5.36 (5.36.0-7+deb12u2) ...
#10 57.51 Selecting previously unselected package libgdbm-compat4:amd64.
#10 57.52 Preparing to unpack .../1-libgdbm-compat4_1.23-3_amd64.deb ...
#10 57.52 Unpacking libgdbm-compat4:amd64 (1.23-3) ...
#10 57.53 Selecting previously unselected package libperl5.36:amd64.
#10 57.54 Preparing to unpack .../2-libperl5.36_5.36.0-7+deb12u2_amd64.deb ...
#10 57.54 Unpacking libperl5.36:amd64 (5.36.0-7+deb12u2) ...
#10 57.71 Selecting previously unselected package perl.
#10 57.71 Preparing to unpack .../3-perl_5.36.0-7+deb12u2_amd64.deb ...
#10 57.72 Unpacking perl (5.36.0-7+deb12u2) ...
#10 57.77 Selecting previously unselected package libpython3.11-minimal:amd64.
#10 57.77 Preparing to unpack .../4-libpython3.11-minimal_3.11.2-6+deb12u6_amd64.deb ...
#10 57.77 Unpacking libpython3.11-minimal:amd64 (3.11.2-6+deb12u6) ...
#10 57.85 Selecting previously unselected package libexpat1:amd64.
#10 57.85 Preparing to unpack .../5-libexpat1_2.5.0-1+deb12u1_amd64.deb ...
#10 57.85 Unpacking libexpat1:amd64 (2.5.0-1+deb12u1) ...
#10 57.89 Selecting previously unselected package python3.11-minimal.
#10 57.89 Preparing to unpack .../6-python3.11-minimal_3.11.2-6+deb12u6_amd64.deb ...
#10 57.90 Unpacking python3.11-minimal (3.11.2-6+deb12u6) ...
#10 58.00 Setting up libpython3.11-minimal:amd64 (3.11.2-6+deb12u6) ...
#10 58.01 Setting up libexpat1:amd64 (2.5.0-1+deb12u1) ...
#10 58.01 Setting up python3.11-minimal (3.11.2-6+deb12u6) ...
#10 58.29 Selecting previously unselected package python3-minimal.
(Reading database ... 9003 files and directories currently installed.)
#10 58.29 Preparing to unpack .../python3-minimal_3.11.2-1+b1_amd64.deb ...
#10 58.29 Unpacking python3-minimal (3.11.2-1+b1) ...
#10 58.31 Selecting previously unselected package media-types.
#10 58.31 Preparing to unpack .../media-types_10.0.0_all.deb ...
#10 58.31 Unpacking media-types (10.0.0) ...
#10 58.34 Selecting previously unselected package libpython3.11-stdlib:amd64.
#10 58.34 Preparing to unpack .../libpython3.11-stdlib_3.11.2-6+deb12u6_amd64.deb ...
#10 58.35 Unpacking libpython3.11-stdlib:amd64 (3.11.2-6+deb12u6) ...
#10 58.45 Selecting previously unselected package python3.11.
#10 58.45 Preparing to unpack .../python3.11_3.11.2-6+deb12u6_amd64.deb ...
#10 58.45 Unpacking python3.11 (3.11.2-6+deb12u6) ...
#10 58.49 Selecting previously unselected package libpython3-stdlib:amd64.
#10 58.49 Preparing to unpack .../libpython3-stdlib_3.11.2-1+b1_amd64.deb ...
#10 58.49 Unpacking libpython3-stdlib:amd64 (3.11.2-1+b1) ...
#10 58.52 Setting up python3-minimal (3.11.2-1+b1) ...
#10 58.63 Selecting previously unselected package python3.
(Reading database ... 9413 files and directories currently installed.)
#10 58.64 Preparing to unpack .../000-python3_3.11.2-1+b1_amd64.deb ...
#10 58.65 Unpacking python3 (3.11.2-1+b1) ...
#10 58.69 Selecting previously unselected package bzip2.
#10 58.69 Preparing to unpack .../001-bzip2_1.0.8-5+b1_amd64.deb ...
#10 58.69 Unpacking bzip2 (1.0.8-5+b1) ...
#10 58.72 Selecting previously unselected package xz-utils.
#10 58.73 Preparing to unpack .../002-xz-utils_5.4.1-1_amd64.deb ...
#10 58.73 Unpacking xz-utils (5.4.1-1) ...
#10 58.80 Selecting previously unselected package binutils-common:amd64.
#10 58.80 Preparing to unpack .../003-binutils-common_2.40-2_amd64.deb ...
#10 58.80 Unpacking binutils-common:amd64 (2.40-2) ...
#10 58.92 Selecting previously unselected package libbinutils:amd64.
#10 58.92 Preparing to unpack .../004-libbinutils_2.40-2_amd64.deb ...
#10 58.92 Unpacking libbinutils:amd64 (2.40-2) ...
#10 58.95 Selecting previously unselected package libctf-nobfd0:amd64.
#10 58.95 Preparing to unpack .../005-libctf-nobfd0_2.40-2_amd64.deb ...
#10 58.95 Unpacking libctf-nobfd0:amd64 (2.40-2) ...
#10 58.99 Selecting previously unselected package libctf0:amd64.
#10 58.99 Preparing to unpack .../006-libctf0_2.40-2_amd64.deb ...
#10 58.99 Unpacking libctf0:amd64 (2.40-2) ...
#10 59.04 Selecting previously unselected package libgprofng0:amd64.
#10 59.04 Preparing to unpack .../007-libgprofng0_2.40-2_amd64.deb ...
#10 59.05 Unpacking libgprofng0:amd64 (2.40-2) ...
#10 59.11 Selecting previously unselected package libjansson4:amd64.
#10 59.11 Preparing to unpack .../008-libjansson4_2.14-2_amd64.deb ...
#10 59.11 Unpacking libjansson4:amd64 (2.14-2) ...
#10 59.13 Selecting previously unselected package binutils-x86-64-linux-gnu.
#10 59.13 Preparing to unpack .../009-binutils-x86-64-linux-gnu_2.40-2_amd64.deb ...
#10 59.13 Unpacking binutils-x86-64-linux-gnu (2.40-2) ...
#10 59.25 Selecting previously unselected package binutils.
#10 59.25 Preparing to unpack .../010-binutils_2.40-2_amd64.deb ...
#10 59.25 Unpacking binutils (2.40-2) ...
#10 59.26 Selecting previously unselected package libc-dev-bin.
#10 59.26 Preparing to unpack .../011-libc-dev-bin_2.36-9+deb12u10_amd64.deb ...
#10 59.26 Unpacking libc-dev-bin (2.36-9+deb12u10) ...
#10 59.28 Selecting previously unselected package linux-libc-dev:amd64.
#10 59.28 Preparing to unpack .../012-linux-libc-dev_6.1.140-1_amd64.deb ...
#10 59.28 Unpacking linux-libc-dev:amd64 (6.1.140-1) ...
#10 59.35 Selecting previously unselected package libcrypt-dev:amd64.
#10 59.35 Preparing to unpack .../013-libcrypt-dev_1%3a4.4.33-2_amd64.deb ...
#10 59.35 Unpacking libcrypt-dev:amd64 (1:4.4.33-2) ...
#10 59.39 Selecting previously unselected package libtirpc-dev:amd64.
#10 59.39 Preparing to unpack .../014-libtirpc-dev_1.3.3+ds-1_amd64.deb ...
#10 59.39 Unpacking libtirpc-dev:amd64 (1.3.3+ds-1) ...
#10 59.45 Selecting previously unselected package libnsl-dev:amd64.
#10 59.45 Preparing to unpack .../015-libnsl-dev_1.3.0-2_amd64.deb ...
#10 59.45 Unpacking libnsl-dev:amd64 (1.3.0-2) ...
#10 59.49 Selecting previously unselected package rpcsvc-proto.
#10 59.49 Preparing to unpack .../016-rpcsvc-proto_1.4.3-1_amd64.deb ...
#10 59.50 Unpacking rpcsvc-proto (1.4.3-1) ...
#10 59.55 Selecting previously unselected package libc6-dev:amd64.
#10 59.55 Preparing to unpack .../017-libc6-dev_2.36-9+deb12u10_amd64.deb ...
#10 59.55 Unpacking libc6-dev:amd64 (2.36-9+deb12u10) ...
#10 59.65 Selecting previously unselected package libisl23:amd64.
#10 59.65 Preparing to unpack .../018-libisl23_0.25-1.1_amd64.deb ...
#10 59.66 Unpacking libisl23:amd64 (0.25-1.1) ...
#10 59.70 Selecting previously unselected package libmpfr6:amd64.
#10 59.70 Preparing to unpack .../019-libmpfr6_4.2.0-1_amd64.deb ...
#10 59.71 Unpacking libmpfr6:amd64 (4.2.0-1) ...
#10 59.75 Selecting previously unselected package libmpc3:amd64.
#10 59.75 Preparing to unpack .../020-libmpc3_1.3.1-1_amd64.deb ...
#10 59.75 Unpacking libmpc3:amd64 (1.3.1-1) ...
#10 59.80 Selecting previously unselected package cpp-12.
#10 59.80 Preparing to unpack .../021-cpp-12_12.2.0-14+deb12u1_amd64.deb ...
#10 59.80 Unpacking cpp-12 (12.2.0-14+deb12u1) ...
#10 60.13 Selecting previously unselected package cpp.
#10 60.13 Preparing to unpack .../022-cpp_4%3a12.2.0-3_amd64.deb ...
#10 60.13 Unpacking cpp (4:12.2.0-3) ...
#10 60.16 Selecting previously unselected package libcc1-0:amd64.
#10 60.16 Preparing to unpack .../023-libcc1-0_12.2.0-14+deb12u1_amd64.deb ...
#10 60.16 Unpacking libcc1-0:amd64 (12.2.0-14+deb12u1) ...
#10 60.20 Selecting previously unselected package libgomp1:amd64.
#10 60.20 Preparing to unpack .../024-libgomp1_12.2.0-14+deb12u1_amd64.deb ...
#10 60.20 Unpacking libgomp1:amd64 (12.2.0-14+deb12u1) ...
#10 60.25 Selecting previously unselected package libitm1:amd64.
#10 60.25 Preparing to unpack .../025-libitm1_12.2.0-14+deb12u1_amd64.deb ...
#10 60.25 Unpacking libitm1:amd64 (12.2.0-14+deb12u1) ...
#10 60.29 Selecting previously unselected package libatomic1:amd64.
#10 60.29 Preparing to unpack .../026-libatomic1_12.2.0-14+deb12u1_amd64.deb ...
#10 60.29 Unpacking libatomic1:amd64 (12.2.0-14+deb12u1) ...
#10 60.33 Selecting previously unselected package libasan8:amd64.
#10 60.33 Preparing to unpack .../027-libasan8_12.2.0-14+deb12u1_amd64.deb ...
#10 60.33 Unpacking libasan8:amd64 (12.2.0-14+deb12u1) ...
#10 60.45 Selecting previously unselected package liblsan0:amd64.
#10 60.45 Preparing to unpack .../028-liblsan0_12.2.0-14+deb12u1_amd64.deb ...
#10 60.45 Unpacking liblsan0:amd64 (12.2.0-14+deb12u1) ...
#10 60.51 Selecting previously unselected package libtsan2:amd64.
#10 60.51 Preparing to unpack .../029-libtsan2_12.2.0-14+deb12u1_amd64.deb ...
#10 60.51 Unpacking libtsan2:amd64 (12.2.0-14+deb12u1) ...
#10 60.61 Selecting previously unselected package libubsan1:amd64.
#10 60.61 Preparing to unpack .../030-libubsan1_12.2.0-14+deb12u1_amd64.deb ...
#10 60.61 Unpacking libubsan1:amd64 (12.2.0-14+deb12u1) ...
#10 60.66 Selecting previously unselected package libquadmath0:amd64.
#10 60.66 Preparing to unpack .../031-libquadmath0_12.2.0-14+deb12u1_amd64.deb ...
#10 60.66 Unpacking libquadmath0:amd64 (12.2.0-14+deb12u1) ...
#10 60.69 Selecting previously unselected package libgcc-12-dev:amd64.
#10 60.70 Preparing to unpack .../032-libgcc-12-dev_12.2.0-14+deb12u1_amd64.deb ...
#10 60.70 Unpacking libgcc-12-dev:amd64 (12.2.0-14+deb12u1) ...
#10 60.81 Selecting previously unselected package gcc-12.
#10 60.81 Preparing to unpack .../033-gcc-12_12.2.0-14+deb12u1_amd64.deb ...
#10 60.82 Unpacking gcc-12 (12.2.0-14+deb12u1) ...
#10 61.16 Selecting previously unselected package gcc.
#10 61.16 Preparing to unpack .../034-gcc_4%3a12.2.0-3_amd64.deb ...
#10 61.16 Unpacking gcc (4:12.2.0-3) ...
#10 61.17 Selecting previously unselected package libstdc++-12-dev:amd64.
#10 61.17 Preparing to unpack .../035-libstdc++-12-dev_12.2.0-14+deb12u1_amd64.deb ...
#10 61.17 Unpacking libstdc++-12-dev:amd64 (12.2.0-14+deb12u1) ...
#10 61.28 Selecting previously unselected package g++-12.
#10 61.28 Preparing to unpack .../036-g++-12_12.2.0-14+deb12u1_amd64.deb ...
#10 61.28 Unpacking g++-12 (12.2.0-14+deb12u1) ...
#10 61.60 Selecting previously unselected package g++.
#10 61.60 Preparing to unpack .../037-g++_4%3a12.2.0-3_amd64.deb ...
#10 61.60 Unpacking g++ (4:12.2.0-3) ...
#10 61.61 Selecting previously unselected package make.
#10 61.61 Preparing to unpack .../038-make_4.3-4.1_amd64.deb ...
#10 61.61 Unpacking make (4.3-4.1) ...
#10 61.65 Selecting previously unselected package libdpkg-perl.
#10 61.65 Preparing to unpack .../039-libdpkg-perl_1.21.22_all.deb ...
#10 61.65 Unpacking libdpkg-perl (1.21.22) ...
#10 61.68 Selecting previously unselected package patch.
#10 61.68 Preparing to unpack .../040-patch_2.7.6-7_amd64.deb ...
#10 61.68 Unpacking patch (2.7.6-7) ...
#10 61.70 Selecting previously unselected package dpkg-dev.
#10 61.70 Preparing to unpack .../041-dpkg-dev_1.21.22_all.deb ...
#10 61.70 Unpacking dpkg-dev (1.21.22) ...
#10 61.76 Selecting previously unselected package build-essential.
#10 61.76 Preparing to unpack .../042-build-essential_12.9_amd64.deb ...
#10 61.76 Unpacking build-essential (12.9) ...
#10 61.77 Selecting previously unselected package libbrotli1:amd64.
#10 61.77 Preparing to unpack .../043-libbrotli1_1.0.9-2+b6_amd64.deb ...
#10 61.77 Unpacking libbrotli1:amd64 (1.0.9-2+b6) ...
#10 61.81 Selecting previously unselected package libsasl2-modules-db:amd64.
#10 61.81 Preparing to unpack .../044-libsasl2-modules-db_2.1.28+dfsg-10_amd64.deb ...
#10 61.81 Unpacking libsasl2-modules-db:amd64 (2.1.28+dfsg-10) ...
#10 61.84 Selecting previously unselected package libsasl2-2:amd64.
#10 61.84 Preparing to unpack .../045-libsasl2-2_2.1.28+dfsg-10_amd64.deb ...
#10 61.84 Unpacking libsasl2-2:amd64 (2.1.28+dfsg-10) ...
#10 61.88 Selecting previously unselected package libldap-2.5-0:amd64.
#10 61.88 Preparing to unpack .../046-libldap-2.5-0_2.5.13+dfsg-5_amd64.deb ...
#10 61.89 Unpacking libldap-2.5-0:amd64 (2.5.13+dfsg-5) ...
#10 61.94 Selecting previously unselected package libnghttp2-14:amd64.
#10 61.95 Preparing to unpack .../047-libnghttp2-14_1.52.0-1+deb12u2_amd64.deb ...
#10 61.95 Unpacking libnghttp2-14:amd64 (1.52.0-1+deb12u2) ...
#10 62.00 Selecting previously unselected package libpsl5:amd64.
#10 62.00 Preparing to unpack .../048-libpsl5_0.21.2-1_amd64.deb ...
#10 62.00 Unpacking libpsl5:amd64 (0.21.2-1) ...
#10 62.04 Selecting previously unselected package librtmp1:amd64.
#10 62.04 Preparing to unpack .../049-librtmp1_2.4+20151223.gitfa8646d.1-2+b2_amd64.deb ...
#10 62.05 Unpacking librtmp1:amd64 (2.4+20151223.gitfa8646d.1-2+b2) ...
#10 62.09 Selecting previously unselected package libssh2-1:amd64.
#10 62.09 Preparing to unpack .../050-libssh2-1_1.10.0-3+b1_amd64.deb ...
#10 62.10 Unpacking libssh2-1:amd64 (1.10.0-3+b1) ...
#10 62.16 Selecting previously unselected package libcurl4:amd64.
#10 62.16 Preparing to unpack .../051-libcurl4_7.88.1-10+deb12u12_amd64.deb ...
#10 62.16 Unpacking libcurl4:amd64 (7.88.1-10+deb12u12) ...
#10 62.21 Selecting previously unselected package curl.
#10 62.21 Preparing to unpack .../052-curl_7.88.1-10+deb12u12_amd64.deb ...
#10 62.21 Unpacking curl (7.88.1-10+deb12u12) ...
#10 62.26 Selecting previously unselected package libicu72:amd64.
#10 62.26 Preparing to unpack .../053-libicu72_72.1-3+deb12u1_amd64.deb ...
#10 62.26 Unpacking libicu72:amd64 (72.1-3+deb12u1) ...
#10 62.54 Selecting previously unselected package icu-devtools.
#10 62.54 Preparing to unpack .../054-icu-devtools_72.1-3+deb12u1_amd64.deb ...
#10 62.54 Unpacking icu-devtools (72.1-3+deb12u1) ...
#10 62.58 Selecting previously unselected package libbsd0:amd64.
#10 62.59 Preparing to unpack .../055-libbsd0_0.11.7-2_amd64.deb ...
#10 62.59 Unpacking libbsd0:amd64 (0.11.7-2) ...
#10 62.62 Selecting previously unselected package libedit2:amd64.
#10 62.62 Preparing to unpack .../056-libedit2_3.1-20221030-2_amd64.deb ...
#10 62.63 Unpacking libedit2:amd64 (3.1-20221030-2) ...
#10 62.68 Selecting previously unselected package libxml2:amd64.
#10 62.69 Preparing to unpack .../057-libxml2_2.9.14+dfsg-1.3~deb12u2_amd64.deb ...
#10 62.69 Unpacking libxml2:amd64 (2.9.14+dfsg-1.3~deb12u2) ...
#10 62.75 Selecting previously unselected package libz3-4:amd64.
#10 62.75 Preparing to unpack .../058-libz3-4_4.8.12-3.1_amd64.deb ...
#10 62.75 Unpacking libz3-4:amd64 (4.8.12-3.1) ...
#10 63.02 Selecting previously unselected package libllvm14:amd64.
#10 63.02 Preparing to unpack .../059-libllvm14_1%3a14.0.6-12_amd64.deb ...
#10 63.02 Unpacking libllvm14:amd64 (1:14.0.6-12) ...
#10 63.38 Selecting previously unselected package libclang-cpp14.
#10 63.38 Preparing to unpack .../060-libclang-cpp14_1%3a14.0.6-12_amd64.deb ...
#10 63.38 Unpacking libclang-cpp14 (1:14.0.6-12) ...
#10 63.62 Selecting previously unselected package libnspr4:amd64.
#10 63.62 Preparing to unpack .../061-libnspr4_2%3a4.35-1_amd64.deb ...
#10 63.62 Unpacking libnspr4:amd64 (2:4.35-1) ...
#10 63.64 Selecting previously unselected package libnss3:amd64.
#10 63.65 Preparing to unpack .../062-libnss3_2%3a3.87.1-1+deb12u1_amd64.deb ...
#10 63.65 Unpacking libnss3:amd64 (2:3.87.1-1+deb12u1) ...
#10 63.74 Selecting previously unselected package nss-plugin-pem:amd64.
#10 63.74 Preparing to unpack .../063-nss-plugin-pem_1.0.8+1-1_amd64.deb ...
#10 63.74 Unpacking nss-plugin-pem:amd64 (1.0.8+1-1) ...
#10 63.75 Selecting previously unselected package libcurl3-nss:amd64.
#10 63.76 Preparing to unpack .../064-libcurl3-nss_7.88.1-10+deb12u12_amd64.deb ...
#10 63.76 Unpacking libcurl3-nss:amd64 (7.88.1-10+deb12u12) ...
#10 63.79 Selecting previously unselected package libdrm-common.
#10 63.79 Preparing to unpack .../065-libdrm-common_2.4.114-1_all.deb ...
#10 63.80 Unpacking libdrm-common (2.4.114-1) ...
#10 63.83 Selecting previously unselected package libdrm2:amd64.
#10 63.83 Preparing to unpack .../066-libdrm2_2.4.114-1+b1_amd64.deb ...
#10 63.83 Unpacking libdrm2:amd64 (2.4.114-1+b1) ...
#10 63.87 Selecting previously unselected package libdrm-amdgpu1:amd64.
#10 63.87 Preparing to unpack .../067-libdrm-amdgpu1_2.4.114-1+b1_amd64.deb ...
#10 63.88 Unpacking libdrm-amdgpu1:amd64 (2.4.114-1+b1) ...
#10 63.92 Selecting previously unselected package libpciaccess0:amd64.
#10 63.92 Preparing to unpack .../068-libpciaccess0_0.17-2_amd64.deb ...
#10 63.92 Unpacking libpciaccess0:amd64 (0.17-2) ...
#10 63.96 Selecting previously unselected package libdrm-intel1:amd64.
#10 63.96 Preparing to unpack .../069-libdrm-intel1_2.4.114-1+b1_amd64.deb ...
#10 63.96 Unpacking libdrm-intel1:amd64 (2.4.114-1+b1) ...
#10 64.00 Selecting previously unselected package libdrm-nouveau2:amd64.
#10 64.00 Preparing to unpack .../070-libdrm-nouveau2_2.4.114-1+b1_amd64.deb ...
#10 64.00 Unpacking libdrm-nouveau2:amd64 (2.4.114-1+b1) ...
#10 64.04 Selecting previously unselected package libdrm-radeon1:amd64.
#10 64.04 Preparing to unpack .../071-libdrm-radeon1_2.4.114-1+b1_amd64.deb ...
#10 64.04 Unpacking libdrm-radeon1:amd64 (2.4.114-1+b1) ...
#10 64.08 Selecting previously unselected package libwayland-server0:amd64.
#10 64.09 Preparing to unpack .../072-libwayland-server0_1.21.0-1_amd64.deb ...
#10 64.09 Unpacking libwayland-server0:amd64 (1.21.0-1) ...
#10 64.10 Selecting previously unselected package libgbm1:amd64.
#10 64.10 Preparing to unpack .../073-libgbm1_22.3.6-1+deb12u1_amd64.deb ...
#10 64.11 Unpacking libgbm1:amd64 (22.3.6-1+deb12u1) ...
#10 64.12 Selecting previously unselected package libglapi-mesa:amd64.
#10 64.12 Preparing to unpack .../074-libglapi-mesa_22.3.6-1+deb12u1_amd64.deb ...
#10 64.12 Unpacking libglapi-mesa:amd64 (22.3.6-1+deb12u1) ...
#10 64.13 Selecting previously unselected package libwayland-client0:amd64.
#10 64.14 Preparing to unpack .../075-libwayland-client0_1.21.0-1_amd64.deb ...
#10 64.14 Unpacking libwayland-client0:amd64 (1.21.0-1) ...
#10 64.16 Selecting previously unselected package libxau6:amd64.
#10 64.16 Preparing to unpack .../076-libxau6_1%3a1.0.9-1_amd64.deb ...
#10 64.16 Unpacking libxau6:amd64 (1:1.0.9-1) ...
#10 64.17 Selecting previously unselected package libxdmcp6:amd64.
#10 64.17 Preparing to unpack .../077-libxdmcp6_1%3a1.1.2-3_amd64.deb ...
#10 64.17 Unpacking libxdmcp6:amd64 (1:1.1.2-3) ...
#10 64.19 Selecting previously unselected package libxcb1:amd64.
#10 64.19 Preparing to unpack .../078-libxcb1_1.15-1_amd64.deb ...
#10 64.19 Unpacking libxcb1:amd64 (1.15-1) ...
#10 64.20 Selecting previously unselected package libx11-data.
#10 64.20 Preparing to unpack .../079-libx11-data_2%3a1.8.4-2+deb12u2_all.deb ...
#10 64.20 Unpacking libx11-data (2:1.8.4-2+deb12u2) ...
#10 64.23 Selecting previously unselected package libx11-6:amd64.
#10 64.23 Preparing to unpack .../080-libx11-6_2%3a1.8.4-2+deb12u2_amd64.deb ...
#10 64.23 Unpacking libx11-6:amd64 (2:1.8.4-2+deb12u2) ...
#10 64.28 Selecting previously unselected package libx11-xcb1:amd64.
#10 64.28 Preparing to unpack .../081-libx11-xcb1_2%3a1.8.4-2+deb12u2_amd64.deb ...
#10 64.28 Unpacking libx11-xcb1:amd64 (2:1.8.4-2+deb12u2) ...
#10 64.31 Selecting previously unselected package libxcb-dri2-0:amd64.
#10 64.31 Preparing to unpack .../082-libxcb-dri2-0_1.15-1_amd64.deb ...
#10 64.31 Unpacking libxcb-dri2-0:amd64 (1.15-1) ...
#10 64.37 Selecting previously unselected package libxcb-dri3-0:amd64.
#10 64.37 Preparing to unpack .../083-libxcb-dri3-0_1.15-1_amd64.deb ...
#10 64.37 Unpacking libxcb-dri3-0:amd64 (1.15-1) ...
#10 64.43 Selecting previously unselected package libxcb-present0:amd64.
#10 64.44 Preparing to unpack .../084-libxcb-present0_1.15-1_amd64.deb ...
#10 64.44 Unpacking libxcb-present0:amd64 (1.15-1) ...
#10 64.49 Selecting previously unselected package libxcb-randr0:amd64.
#10 64.49 Preparing to unpack .../085-libxcb-randr0_1.15-1_amd64.deb ...
#10 64.49 Unpacking libxcb-randr0:amd64 (1.15-1) ...
#10 64.54 Selecting previously unselected package libxcb-sync1:amd64.
#10 64.55 Preparing to unpack .../086-libxcb-sync1_1.15-1_amd64.deb ...
#10 64.55 Unpacking libxcb-sync1:amd64 (1.15-1) ...
#10 64.60 Selecting previously unselected package libxcb-xfixes0:amd64.
#10 64.60 Preparing to unpack .../087-libxcb-xfixes0_1.15-1_amd64.deb ...
#10 64.61 Unpacking libxcb-xfixes0:amd64 (1.15-1) ...
#10 64.66 Selecting previously unselected package libxshmfence1:amd64.
#10 64.66 Preparing to unpack .../088-libxshmfence1_1.3-1_amd64.deb ...
#10 64.66 Unpacking libxshmfence1:amd64 (1.3-1) ...
#10 64.69 Selecting previously unselected package libegl-mesa0:amd64.
#10 64.70 Preparing to unpack .../089-libegl-mesa0_22.3.6-1+deb12u1_amd64.deb ...
#10 64.70 Unpacking libegl-mesa0:amd64 (22.3.6-1+deb12u1) ...
#10 64.75 Selecting previously unselected package libglvnd0:amd64.
#10 64.75 Preparing to unpack .../090-libglvnd0_1.6.0-1_amd64.deb ...
#10 64.75 Unpacking libglvnd0:amd64 (1.6.0-1) ...
#10 64.79 Selecting previously unselected package libegl1:amd64.
#10 64.80 Preparing to unpack .../091-libegl1_1.6.0-1_amd64.deb ...
#10 64.80 Unpacking libegl1:amd64 (1.6.0-1) ...
#10 64.85 Selecting previously unselected package libegl1-mesa:amd64.
#10 64.85 Preparing to unpack .../092-libegl1-mesa_22.3.6-1+deb12u1_amd64.deb ...
#10 64.85 Unpacking libegl1-mesa:amd64 (22.3.6-1+deb12u1) ...
#10 64.89 Selecting previously unselected package libelf1:amd64.
#10 64.89 Preparing to unpack .../093-libelf1_0.188-2.1_amd64.deb ...
#10 64.90 Unpacking libelf1:amd64 (0.188-2.1) ...
#10 64.96 Selecting previously unselected package libffi-dev:amd64.
#10 64.97 Preparing to unpack .../094-libffi-dev_3.4.4-1_amd64.deb ...
#10 64.97 Unpacking libffi-dev:amd64 (3.4.4-1) ...
#10 65.01 Selecting previously unselected package libfontenc1:amd64.
#10 65.02 Preparing to unpack .../095-libfontenc1_1%3a1.1.4-1_amd64.deb ...
#10 65.02 Unpacking libfontenc1:amd64 (1:1.1.4-1) ...
#10 65.05 Selecting previously unselected package libpng16-16:amd64.
#10 65.05 Preparing to unpack .../096-libpng16-16_1.6.39-2_amd64.deb ...
#10 65.06 Unpacking libpng16-16:amd64 (1.6.39-2) ...
#10 65.11 Selecting previously unselected package libfreetype6:amd64.
#10 65.11 Preparing to unpack .../097-libfreetype6_2.12.1+dfsg-5+deb12u4_amd64.deb ...
#10 65.12 Unpacking libfreetype6:amd64 (2.12.1+dfsg-5+deb12u4) ...
#10 65.18 Selecting previously unselected package libxcb-glx0:amd64.
#10 65.18 Preparing to unpack .../098-libxcb-glx0_1.15-1_amd64.deb ...
#10 65.18 Unpacking libxcb-glx0:amd64 (1.15-1) ...
#10 65.23 Selecting previously unselected package libxcb-shm0:amd64.
#10 65.23 Preparing to unpack .../099-libxcb-shm0_1.15-1_amd64.deb ...
#10 65.23 Unpacking libxcb-shm0:amd64 (1.15-1) ...
#10 65.28 Selecting previously unselected package libxext6:amd64.
#10 65.28 Preparing to unpack .../100-libxext6_2%3a1.3.4-1+b1_amd64.deb ...
#10 65.29 Unpacking libxext6:amd64 (2:1.3.4-1+b1) ...
#10 65.33 Selecting previously unselected package libxfixes3:amd64.
#10 65.33 Preparing to unpack .../101-libxfixes3_1%3a6.0.0-2_amd64.deb ...
#10 65.33 Unpacking libxfixes3:amd64 (1:6.0.0-2) ...
#10 65.37 Selecting previously unselected package libxxf86vm1:amd64.
#10 65.37 Preparing to unpack .../102-libxxf86vm1_1%3a1.1.4-1+b2_amd64.deb ...
#10 65.37 Unpacking libxxf86vm1:amd64 (1:1.1.4-1+b2) ...
#10 65.41 Selecting previously unselected package libllvm15:amd64.
#10 65.41 Preparing to unpack .../103-libllvm15_1%3a15.0.6-4+b1_amd64.deb ...
#10 65.41 Unpacking libllvm15:amd64 (1:15.0.6-4+b1) ...
#10 65.79 Selecting previously unselected package libsensors-config.
#10 65.79 Preparing to unpack .../104-libsensors-config_1%3a3.6.0-7.1_all.deb ...
#10 65.80 Unpacking libsensors-config (1:3.6.0-7.1) ...
#10 65.81 Selecting previously unselected package libsensors5:amd64.
#10 65.81 Preparing to unpack .../105-libsensors5_1%3a3.6.0-7.1_amd64.deb ...
#10 65.82 Unpacking libsensors5:amd64 (1:3.6.0-7.1) ...
#10 65.86 Selecting previously unselected package libgl1-mesa-dri:amd64.
#10 65.87 Preparing to unpack .../106-libgl1-mesa-dri_22.3.6-1+deb12u1_amd64.deb ...
#10 65.88 Unpacking libgl1-mesa-dri:amd64 (22.3.6-1+deb12u1) ...
#10 66.16 Selecting previously unselected package libglx-mesa0:amd64.
#10 66.16 Preparing to unpack .../107-libglx-mesa0_22.3.6-1+deb12u1_amd64.deb ...
#10 66.16 Unpacking libglx-mesa0:amd64 (22.3.6-1+deb12u1) ...
#10 66.19 Selecting previously unselected package libglx0:amd64.
#10 66.19 Preparing to unpack .../108-libglx0_1.6.0-1_amd64.deb ...
#10 66.19 Unpacking libglx0:amd64 (1.6.0-1) ...
#10 66.23 Selecting previously unselected package libgl1:amd64.
#10 66.24 Preparing to unpack .../109-libgl1_1.6.0-1_amd64.deb ...
#10 66.24 Unpacking libgl1:amd64 (1.6.0-1) ...
#10 66.29 Selecting previously unselected package libgl1-mesa-glx:amd64.
#10 66.29 Preparing to unpack .../110-libgl1-mesa-glx_22.3.6-1+deb12u1_amd64.deb ...
#10 66.29 Unpacking libgl1-mesa-glx:amd64 (22.3.6-1+deb12u1) ...
#10 66.33 Selecting previously unselected package libglfw3:amd64.
#10 66.33 Preparing to unpack .../111-libglfw3_3.3.8-1_amd64.deb ...
#10 66.33 Unpacking libglfw3:amd64 (3.3.8-1) ...
#10 66.37 Selecting previously unselected package x11-common.
#10 66.38 Preparing to unpack .../112-x11-common_1%3a7.7+23_all.deb ...
#10 66.38 Unpacking x11-common (1:7.7+23) ...
#10 66.44 Selecting previously unselected package libice6:amd64.
#10 66.44 Preparing to unpack .../113-libice6_2%3a1.0.10-1_amd64.deb ...
#10 66.44 Unpacking libice6:amd64 (2:1.0.10-1) ...
#10 66.48 Selecting previously unselected package libicu-dev:amd64.
#10 66.48 Preparing to unpack .../114-libicu-dev_72.1-3+deb12u1_amd64.deb ...
#10 66.48 Unpacking libicu-dev:amd64 (72.1-3+deb12u1) ...
#10 66.77 Selecting previously unselected package libncurses6:amd64.
#10 66.77 Preparing to unpack .../115-libncurses6_6.4-4_amd64.deb ...
#10 66.77 Unpacking libncurses6:amd64 (6.4-4) ...
#10 66.79 Selecting previously unselected package libncurses-dev:amd64.
#10 66.79 Preparing to unpack .../116-libncurses-dev_6.4-4_amd64.deb ...
#10 66.79 Unpacking libncurses-dev:amd64 (6.4-4) ...
#10 66.83 Selecting previously unselected package libosmesa6:amd64.
#10 66.83 Preparing to unpack .../117-libosmesa6_22.3.6-1+deb12u1_amd64.deb ...
#10 66.83 Unpacking libosmesa6:amd64 (22.3.6-1+deb12u1) ...
#10 66.97 Selecting previously unselected package libpfm4:amd64.
#10 66.97 Preparing to unpack .../118-libpfm4_4.13.0-1_amd64.deb ...
#10 66.97 Unpacking libpfm4:amd64 (4.13.0-1) ...
#10 67.01 Selecting previously unselected package libpixman-1-0:amd64.
#10 67.01 Preparing to unpack .../119-libpixman-1-0_0.42.2-1_amd64.deb ...
#10 67.01 Unpacking libpixman-1-0:amd64 (0.42.2-1) ...
#10 67.06 Selecting previously unselected package libsm6:amd64.
#10 67.06 Preparing to unpack .../120-libsm6_2%3a1.2.3-1_amd64.deb ...
#10 67.06 Unpacking libsm6:amd64 (2:1.2.3-1) ...
#10 67.10 Selecting previously unselected package libtinfo-dev:amd64.
#10 67.10 Preparing to unpack .../121-libtinfo-dev_6.4-4_amd64.deb ...
#10 67.10 Unpacking libtinfo-dev:amd64 (6.4-4) ...
#10 67.13 Selecting previously unselected package libunwind8:amd64.
#10 67.13 Preparing to unpack .../122-libunwind8_1.6.2-3_amd64.deb ...
#10 67.13 Unpacking libunwind8:amd64 (1.6.2-3) ...
#10 67.18 Selecting previously unselected package libxt6:amd64.
#10 67.18 Preparing to unpack .../123-libxt6_1%3a1.2.1-1.1_amd64.deb ...
#10 67.18 Unpacking libxt6:amd64 (1:1.2.1-1.1) ...
#10 67.22 Selecting previously unselected package libxmu6:amd64.
#10 67.23 Preparing to unpack .../124-libxmu6_2%3a1.1.3-3_amd64.deb ...
#10 67.23 Unpacking libxmu6:amd64 (2:1.1.3-3) ...
#10 67.27 Selecting previously unselected package libxpm4:amd64.
#10 67.27 Preparing to unpack .../125-libxpm4_1%3a3.5.12-1.1+deb12u1_amd64.deb ...
#10 67.28 Unpacking libxpm4:amd64 (1:3.5.12-1.1+deb12u1) ...
#10 67.31 Selecting previously unselected package libxaw7:amd64.
#10 67.31 Preparing to unpack .../126-libxaw7_2%3a1.0.14-1_amd64.deb ...
#10 67.31 Unpacking libxaw7:amd64 (2:1.0.14-1) ...
#10 67.36 Selecting previously unselected package libxfont2:amd64.
#10 67.36 Preparing to unpack .../127-libxfont2_1%3a2.0.6-1_amd64.deb ...
#10 67.37 Unpacking libxfont2:amd64 (1:2.0.6-1) ...
#10 67.42 Selecting previously unselected package libxkbfile1:amd64.
#10 67.42 Preparing to unpack .../128-libxkbfile1_1%3a1.1.0-1_amd64.deb ...
#10 67.42 Unpacking libxkbfile1:amd64 (1:1.1.0-1) ...
#10 67.47 Selecting previously unselected package libxml2-dev:amd64.
#10 67.47 Preparing to unpack .../129-libxml2-dev_2.9.14+dfsg-1.3~deb12u2_amd64.deb ...
#10 67.47 Unpacking libxml2-dev:amd64 (2.9.14+dfsg-1.3~deb12u2) ...
#10 67.53 Selecting previously unselected package libxrender1:amd64.
#10 67.53 Preparing to unpack .../130-libxrender1_1%3a0.9.10-1.1_amd64.deb ...
#10 67.53 Unpacking libxrender1:amd64 (1:0.9.10-1.1) ...
#10 67.58 Selecting previously unselected package libxrandr2:amd64.
#10 67.58 Preparing to unpack .../131-libxrandr2_2%3a1.5.2-2+b1_amd64.deb ...
#10 67.58 Unpacking libxrandr2:amd64 (2:1.5.2-2+b1) ...
#10 67.62 Selecting previously unselected package libyaml-0-2:amd64.
#10 67.62 Preparing to unpack .../132-libyaml-0-2_0.2.5-1_amd64.deb ...
#10 67.63 Unpacking libyaml-0-2:amd64 (0.2.5-1) ...
#10 67.67 Selecting previously unselected package libz3-dev:amd64.
#10 67.67 Preparing to unpack .../133-libz3-dev_4.8.12-3.1_amd64.deb ...
#10 67.67 Unpacking libz3-dev:amd64 (4.8.12-3.1) ...
#10 67.71 Selecting previously unselected package llvm-14-runtime.
#10 67.71 Preparing to unpack .../134-llvm-14-runtime_1%3a14.0.6-12_amd64.deb ...
#10 67.71 Unpacking llvm-14-runtime (1:14.0.6-12) ...
#10 67.77 Selecting previously unselected package llvm-runtime:amd64.
#10 67.77 Preparing to unpack .../135-llvm-runtime_1%3a14.0-55.7~deb12u1_amd64.deb ...
#10 67.77 Unpacking llvm-runtime:amd64 (1:14.0-55.7~deb12u1) ...
#10 67.80 Selecting previously unselected package llvm-14-linker-tools.
#10 67.80 Preparing to unpack .../136-llvm-14-linker-tools_1%3a14.0.6-12_amd64.deb ...
#10 67.80 Unpacking llvm-14-linker-tools (1:14.0.6-12) ...
#10 67.88 Selecting previously unselected package llvm-14.
#10 67.88 Preparing to unpack .../137-llvm-14_1%3a14.0.6-12_amd64.deb ...
#10 67.88 Unpacking llvm-14 (1:14.0.6-12) ...
#10 68.16 Selecting previously unselected package llvm.
#10 68.16 Preparing to unpack .../138-llvm_1%3a14.0-55.7~deb12u1_amd64.deb ...
#10 68.16 Unpacking llvm (1:14.0-55.7~deb12u1) ...
#10 68.18 Selecting previously unselected package python3-pkg-resources.
#10 68.19 Preparing to unpack .../139-python3-pkg-resources_66.1.1-1+deb12u1_all.deb ...
#10 68.19 Unpacking python3-pkg-resources (66.1.1-1+deb12u1) ...
#10 68.22 Selecting previously unselected package python3-pygments.
#10 68.22 Preparing to unpack .../140-python3-pygments_2.14.0+dfsg-1_all.deb ...
#10 68.22 Unpacking python3-pygments (2.14.0+dfsg-1) ...
#10 68.28 Selecting previously unselected package python3-yaml.
#10 68.29 Preparing to unpack .../141-python3-yaml_6.0-3+b2_amd64.deb ...
#10 68.29 Unpacking python3-yaml (6.0-3+b2) ...
#10 68.31 Selecting previously unselected package llvm-14-tools.
#10 68.31 Preparing to unpack .../142-llvm-14-tools_1%3a14.0.6-12_amd64.deb ...
#10 68.31 Unpacking llvm-14-tools (1:14.0.6-12) ...
#10 68.37 Selecting previously unselected package llvm-14-dev.
#10 68.37 Preparing to unpack .../143-llvm-14-dev_1%3a14.0.6-12_amd64.deb ...
#10 68.37 Unpacking llvm-14-dev (1:14.0.6-12) ...
#10 68.92 Selecting previously unselected package llvm-dev.
#10 68.92 Preparing to unpack .../144-llvm-dev_1%3a14.0-55.7~deb12u1_amd64.deb ...
#10 68.92 Unpacking llvm-dev (1:14.0-55.7~deb12u1) ...
#10 68.94 Selecting previously unselected package x11-xkb-utils.
#10 68.95 Preparing to unpack .../145-x11-xkb-utils_7.7+7_amd64.deb ...
#10 68.95 Unpacking x11-xkb-utils (7.7+7) ...
#10 68.99 Selecting previously unselected package xkb-data.
#10 68.99 Preparing to unpack .../146-xkb-data_2.35.1-1_all.deb ...
#10 68.99 Unpacking xkb-data (2.35.1-1) ...
#10 69.05 Selecting previously unselected package xserver-common.
#10 69.05 Preparing to unpack .../147-xserver-common_2%3a21.1.7-3+deb12u10_all.deb ...
#10 69.05 Unpacking xserver-common (2:21.1.7-3+deb12u10) ...
#10 69.10 Selecting previously unselected package xvfb.
#10 69.10 Preparing to unpack .../148-xvfb_2%3a21.1.7-3+deb12u10_amd64.deb ...
#10 69.10 Unpacking xvfb (2:21.1.7-3+deb12u10) ...
#10 69.16 Selecting previously unselected package libopengl0:amd64.
#10 69.16 Preparing to unpack .../149-libopengl0_1.6.0-1_amd64.deb ...
#10 69.16 Unpacking libopengl0:amd64 (1.6.0-1) ...
#10 69.19 Setting up media-types (10.0.0) ...
#10 69.19 Setting up libpixman-1-0:amd64 (0.42.2-1) ...
#10 69.19 Setting up libwayland-server0:amd64 (1.21.0-1) ...
#10 69.19 Setting up libpciaccess0:amd64 (0.17-2) ...
#10 69.20 Setting up libxau6:amd64 (1:1.0.9-1) ...
#10 69.20 Setting up libpsl5:amd64 (0.21.2-1) ...
#10 69.20 Setting up libicu72:amd64 (72.1-3+deb12u1) ...
#10 69.21 Setting up libyaml-0-2:amd64 (0.2.5-1) ...
#10 69.21 Setting up libglvnd0:amd64 (1.6.0-1) ...
#10 69.22 Setting up libpython3.11-stdlib:amd64 (3.11.2-6+deb12u6) ...
#10 69.22 Setting up libbrotli1:amd64 (1.0.9-2+b6) ...
#10 69.22 Setting up binutils-common:amd64 (2.40-2) ...
#10 69.23 Setting up x11-common (1:7.7+23) ...
#10 69.29 debconf: unable to initialize frontend: Dialog
#10 69.29 debconf: (TERM is not set, so the dialog frontend is not usable.)
#10 69.29 debconf: falling back to frontend: Readline
#10 69.30 debconf: unable to initialize frontend: Readline
#10 69.30 debconf: (This frontend requires a controlling tty.)
#10 69.30 debconf: falling back to frontend: Teletype
#10 69.31 invoke-rc.d: could not determine current runlevel
#10 69.31 invoke-rc.d: policy-rc.d denied execution of restart.
#10 69.32 Setting up libsensors-config (1:3.6.0-7.1) ...
#10 69.33 Setting up libnghttp2-14:amd64 (1.52.0-1+deb12u2) ...
#10 69.33 Setting up linux-libc-dev:amd64 (6.1.140-1) ...
#10 69.33 Setting up libctf-nobfd0:amd64 (2.40-2) ...
#10 69.34 Setting up xkb-data (2.35.1-1) ...
#10 69.34 Setting up libgomp1:amd64 (12.2.0-14+deb12u1) ...
#10 69.34 Setting up bzip2 (1.0.8-5+b1) ...
#10 69.35 Setting up libffi-dev:amd64 (3.4.4-1) ...
#10 69.35 Setting up libunwind8:amd64 (1.6.2-3) ...
#10 69.36 Setting up libopengl0:amd64 (1.6.0-1) ...
#10 69.36 Setting up libjansson4:amd64 (2.14-2) ...
#10 69.36 Setting up libsasl2-modules-db:amd64 (2.1.28+dfsg-10) ...
#10 69.37 Setting up libfontenc1:amd64 (1:1.1.4-1) ...
#10 69.37 Setting up perl-modules-5.36 (5.36.0-7+deb12u2) ...
#10 69.38 Setting up libz3-4:amd64 (4.8.12-3.1) ...
#10 69.38 Setting up libtirpc-dev:amd64 (1.3.3+ds-1) ...
#10 69.38 Setting up libpfm4:amd64 (4.13.0-1) ...
#10 69.39 Setting up rpcsvc-proto (1.4.3-1) ...
#10 69.39 Setting up libx11-data (2:1.8.4-2+deb12u2) ...
#10 69.39 Setting up make (4.3-4.1) ...
#10 69.40 Setting up libmpfr6:amd64 (4.2.0-1) ...
#10 69.40 Setting up libnspr4:amd64 (2:4.35-1) ...
#10 69.41 Setting up librtmp1:amd64 (2.4+20151223.gitfa8646d.1-2+b2) ...
#10 69.41 Setting up libncurses6:amd64 (6.4-4) ...
#10 69.41 Setting up xz-utils (5.4.1-1) ...
#10 69.43 update-alternatives: using /usr/bin/xz to provide /usr/bin/lzma (lzma) in auto mode
#10 69.43 update-alternatives: warning: skip creation of /usr/share/man/man1/lzma.1.gz because associated file /usr/share/man/man1/xz.1.gz (of link group lzma) doesn't exist
#10 69.43 update-alternatives: warning: skip creation of /usr/share/man/man1/unlzma.1.gz because associated file /usr/share/man/man1/unxz.1.gz (of link group lzma) doesn't exist
#10 69.43 update-alternatives: warning: skip creation of /usr/share/man/man1/lzcat.1.gz because associated file /usr/share/man/man1/xzcat.1.gz (of link group lzma) doesn't exist
#10 69.43 update-alternatives: warning: skip creation of /usr/share/man/man1/lzmore.1.gz because associated file /usr/share/man/man1/xzmore.1.gz (of link group lzma) doesn't exist
#10 69.43 update-alternatives: warning: skip creation of /usr/share/man/man1/lzless.1.gz because associated file /usr/share/man/man1/xzless.1.gz (of link group lzma) doesn't exist
#10 69.43 update-alternatives: warning: skip creation of /usr/share/man/man1/lzdiff.1.gz because associated file /usr/share/man/man1/xzdiff.1.gz (of link group lzma) doesn't exist
#10 69.43 update-alternatives: warning: skip creation of /usr/share/man/man1/lzcmp.1.gz because associated file /usr/share/man/man1/xzcmp.1.gz (of link group lzma) doesn't exist
#10 69.43 update-alternatives: warning: skip creation of /usr/share/man/man1/lzgrep.1.gz because associated file /usr/share/man/man1/xzgrep.1.gz (of link group lzma) doesn't exist
#10 69.43 update-alternatives: warning: skip creation of /usr/share/man/man1/lzegrep.1.gz because associated file /usr/share/man/man1/xzegrep.1.gz (of link group lzma) doesn't exist
#10 69.43 update-alternatives: warning: skip creation of /usr/share/man/man1/lzfgrep.1.gz because associated file /usr/share/man/man1/xzfgrep.1.gz (of link group lzma) doesn't exist
#10 69.43 Setting up libquadmath0:amd64 (12.2.0-14+deb12u1) ...
#10 69.44 Setting up libpng16-16:amd64 (1.6.39-2) ...
#10 69.45 Setting up libmpc3:amd64 (1.3.1-1) ...
#10 69.45 Setting up libatomic1:amd64 (12.2.0-14+deb12u1) ...
#10 69.45 Setting up patch (2.7.6-7) ...
#10 69.46 Setting up icu-devtools (72.1-3+deb12u1) ...
#10 69.46 Setting up libgdbm-compat4:amd64 (1.23-3) ...
#10 69.46 Setting up libsensors5:amd64 (1:3.6.0-7.1) ...
#10 69.47 Setting up libglapi-mesa:amd64 (22.3.6-1+deb12u1) ...
#10 69.47 Setting up libsasl2-2:amd64 (2.1.28+dfsg-10) ...
#10 69.47 Setting up libubsan1:amd64 (12.2.0-14+deb12u1) ...
#10 69.48 Setting up libnsl-dev:amd64 (1.3.0-2) ...
#10 69.48 Setting up libxshmfence1:amd64 (1.3-1) ...
#10 69.48 Setting up libcrypt-dev:amd64 (1:4.4.33-2) ...
#10 69.50 Setting up libasan8:amd64 (12.2.0-14+deb12u1) ...
#10 69.50 Setting up libssh2-1:amd64 (1.10.0-3+b1) ...
#10 69.51 Setting up libtsan2:amd64 (12.2.0-14+deb12u1) ...
#10 69.51 Setting up libbinutils:amd64 (2.40-2) ...
#10 69.51 Setting up libisl23:amd64 (0.25-1.1) ...
#10 69.52 Setting up libc-dev-bin (2.36-9+deb12u10) ...
#10 69.52 Setting up libbsd0:amd64 (0.11.7-2) ...
#10 69.52 Setting up libdrm-common (2.4.114-1) ...
#10 69.53 Setting up libelf1:amd64 (0.188-2.1) ...
#10 69.53 Setting up libxml2:amd64 (2.9.14+dfsg-1.3~deb12u2) ...
#10 69.53 Setting up libcc1-0:amd64 (12.2.0-14+deb12u1) ...
#10 69.54 Setting up libperl5.36:amd64 (5.36.0-7+deb12u2) ...
#10 69.54 Setting up liblsan0:amd64 (12.2.0-14+deb12u1) ...
#10 69.54 Setting up libitm1:amd64 (12.2.0-14+deb12u1) ...
#10 69.55 Setting up libpython3-stdlib:amd64 (3.11.2-1+b1) ...
#10 69.55 Setting up libwayland-client0:amd64 (1.21.0-1) ...
#10 69.55 Setting up libctf0:amd64 (2.40-2) ...
#10 69.56 Setting up libz3-dev:amd64 (4.8.12-3.1) ...
#10 69.56 Setting up python3.11 (3.11.2-6+deb12u6) ...
#10 69.89 Setting up libice6:amd64 (2:1.0.10-1) ...
#10 69.89 Setting up libxdmcp6:amd64 (1:1.1.2-3) ...
#10 69.89 Setting up cpp-12 (12.2.0-14+deb12u1) ...
#10 69.89 Setting up libxcb1:amd64 (1.15-1) ...
#10 69.90 Setting up libxcb-xfixes0:amd64 (1.15-1) ...
#10 69.90 Setting up libxcb-glx0:amd64 (1.15-1) ...
#10 69.90 Setting up libedit2:amd64 (3.1-20221030-2) ...
#10 69.91 Setting up python3 (3.11.2-1+b1) ...
#10 69.92 running python rtupdate hooks for python3.11...
#10 69.92 running python post-rtupdate hooks for python3.11...
#10 69.98 Setting up libnss3:amd64 (2:3.87.1-1+deb12u1) ...
#10 69.98 Setting up libxcb-shm0:amd64 (1.15-1) ...
#10 69.98 Setting up libldap-2.5-0:amd64 (2.5.13+dfsg-5) ...
#10 69.99 Setting up libxcb-present0:amd64 (1.15-1) ...
#10 69.99 Setting up perl (5.36.0-7+deb12u2) ...
#10 70.01 Setting up libgprofng0:amd64 (2.40-2) ...
#10 70.02 Setting up libfreetype6:amd64 (2.12.1+dfsg-5+deb12u4) ...
#10 70.02 Setting up libxcb-sync1:amd64 (1.15-1) ...
#10 70.02 Setting up libgcc-12-dev:amd64 (12.2.0-14+deb12u1) ...
#10 70.03 Setting up libdpkg-perl (1.21.22) ...
#10 70.03 Setting up libxcb-dri2-0:amd64 (1.15-1) ...
#10 70.03 Setting up libllvm14:amd64 (1:14.0.6-12) ...
#10 70.04 Setting up libdrm2:amd64 (2.4.114-1+b1) ...
#10 70.04 Setting up libxcb-randr0:amd64 (1.15-1) ...
#10 70.05 Setting up cpp (4:12.2.0-3) ...
#10 70.06 Setting up libllvm15:amd64 (1:15.0.6-4+b1) ...
#10 70.06 Setting up libcurl4:amd64 (7.88.1-10+deb12u12) ...
#10 70.06 Setting up libc6-dev:amd64 (2.36-9+deb12u10) ...
#10 70.07 Setting up libx11-6:amd64 (2:1.8.4-2+deb12u2) ...
#10 70.07 Setting up curl (7.88.1-10+deb12u12) ...
#10 70.07 Setting up libxkbfile1:amd64 (1:1.1.0-1) ...
#10 70.08 Setting up llvm-14-linker-tools (1:14.0.6-12) ...
#10 70.08 Setting up libsm6:amd64 (2:1.2.3-1) ...
#10 70.08 Setting up libxfont2:amd64 (1:2.0.6-1) ...
#10 70.09 Setting up libicu-dev:amd64 (72.1-3+deb12u1) ...
#10 70.09 Setting up binutils-x86-64-linux-gnu (2.40-2) ...
#10 70.09 Setting up libdrm-amdgpu1:amd64 (2.4.114-1+b1) ...
#10 70.10 Setting up libosmesa6:amd64 (22.3.6-1+deb12u1) ...
#10 70.10 Setting up python3-pkg-resources (66.1.1-1+deb12u1) ...
#10 70.24 Setting up libxcb-dri3-0:amd64 (1.15-1) ...
#10 70.24 Setting up libx11-xcb1:amd64 (2:1.8.4-2+deb12u2) ...
#10 70.24 Setting up libncurses-dev:amd64 (6.4-4) ...
#10 70.24 Setting up libdrm-nouveau2:amd64 (2.4.114-1+b1) ...
#10 70.24 Setting up libxpm4:amd64 (1:3.5.12-1.1+deb12u1) ...
#10 70.25 Setting up libxrender1:amd64 (1:0.9.10-1.1) ...
#10 70.25 Setting up libstdc++-12-dev:amd64 (12.2.0-14+deb12u1) ...
#10 70.25 Setting up libgbm1:amd64 (22.3.6-1+deb12u1) ...
#10 70.25 Setting up libdrm-radeon1:amd64 (2.4.114-1+b1) ...
#10 70.26 Setting up libdrm-intel1:amd64 (2.4.114-1+b1) ...
#10 70.26 Setting up libgl1-mesa-dri:amd64 (22.3.6-1+deb12u1) ...
#10 70.27 Setting up libxext6:amd64 (2:1.3.4-1+b1) ...
#10 70.27 Setting up nss-plugin-pem:amd64 (1.0.8+1-1) ...
#10 70.28 Setting up python3-yaml (6.0-3+b2) ...
#10 70.37 Setting up binutils (2.40-2) ...
#10 70.38 Setting up dpkg-dev (1.21.22) ...
#10 70.38 Setting up libxxf86vm1:amd64 (1:1.1.4-1+b2) ...
#10 70.39 Setting up python3-pygments (2.14.0+dfsg-1) ...
#10 70.67 Setting up libxml2-dev:amd64 (2.9.14+dfsg-1.3~deb12u2) ...
#10 70.67 Setting up libegl-mesa0:amd64 (22.3.6-1+deb12u1) ...
#10 70.67 Setting up llvm-14-runtime (1:14.0.6-12) ...
#10 70.67 Setting up gcc-12 (12.2.0-14+deb12u1) ...
#10 70.68 Setting up libxfixes3:amd64 (1:6.0.0-2) ...
#10 70.68 Setting up llvm-runtime:amd64 (1:14.0-55.7~deb12u1) ...
#10 70.68 Setting up libxrandr2:amd64 (2:1.5.2-2+b1) ...
#10 70.68 Setting up libclang-cpp14 (1:14.0.6-12) ...
#10 70.69 Setting up libxt6:amd64 (1:1.2.1-1.1) ...
#10 70.69 Setting up libcurl3-nss:amd64 (7.88.1-10+deb12u12) ...
#10 70.70 Setting up libegl1:amd64 (1.6.0-1) ...
#10 70.70 Setting up g++-12 (12.2.0-14+deb12u1) ...
#10 70.71 Setting up llvm-14 (1:14.0.6-12) ...
#10 70.71 Setting up llvm-14-tools (1:14.0.6-12) ...
#10 70.71 Setting up libtinfo-dev:amd64 (6.4-4) ...
#10 70.72 Setting up libxmu6:amd64 (2:1.1.3-3) ...
#10 70.72 Setting up libglx-mesa0:amd64 (22.3.6-1+deb12u1) ...
#10 70.72 Setting up libglx0:amd64 (1.6.0-1) ...
#10 70.73 Setting up libxaw7:amd64 (2:1.0.14-1) ...
#10 70.73 Setting up gcc (4:12.2.0-3) ...
#10 70.75 Setting up libegl1-mesa:amd64 (22.3.6-1+deb12u1) ...
#10 70.75 Setting up libgl1:amd64 (1.6.0-1) ...
#10 70.76 Setting up llvm (1:14.0-55.7~deb12u1) ...
#10 70.76 Setting up libgl1-mesa-glx:amd64 (22.3.6-1+deb12u1) ...
#10 70.77 Setting up g++ (4:12.2.0-3) ...
#10 70.78 update-alternatives: using /usr/bin/g++ to provide /usr/bin/c++ (c++) in auto mode
#10 70.78 Setting up build-essential (12.9) ...
#10 70.78 Setting up llvm-14-dev (1:14.0.6-12) ...
#10 70.79 Setting up llvm-dev (1:14.0-55.7~deb12u1) ...
#10 70.79 Setting up libglfw3:amd64 (3.3.8-1) ...
#10 70.79 Setting up x11-xkb-utils (7.7+7) ...
#10 70.80 Setting up xserver-common (2:21.1.7-3+deb12u10) ...
#10 70.80 Setting up xvfb (2:21.1.7-3+deb12u10) ...
#10 70.80 Processing triggers for libc-bin (2.36-9+deb12u10) ...
#10 70.87
#10 70.87 WARNING: apt does not have a stable CLI interface. Use with caution in scripts.
#10 70.87
#10 DONE 71.0s

#20 [backend 4/8] COPY requirements.txt .
#20 DONE 0.0s

#21 [backend 5/8] RUN pip install --no-cache-dir --upgrade pip &&     pip config set global.timeout 600 &&     pip config set global.retries 5
#21 0.777 Requirement already satisfied: pip in /usr/local/lib/python3.11/site-packages (24.0)
#21 0.920 Collecting pip
#21 1.087   Downloading pip-25.2-py3-none-any.whl.metadata (4.7 kB)
#21 1.119 Downloading pip-25.2-py3-none-any.whl (1.8 MB)
#21 1.362    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.8/1.8 MB 7.4 MB/s eta 0:00:00
#21 1.394 Installing collected packages: pip
#21 1.394   Attempting uninstall: pip
#21 1.395     Found existing installation: pip 24.0
#21 1.410     Uninstalling pip-24.0:
#21 1.477       Successfully uninstalled pip-24.0
#21 1.806 Successfully installed pip-25.2
#21 1.806 WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv
#21 2.193 Writing to /root/.config/pip/pip.conf
#21 2.429 Writing to /root/.config/pip/pip.conf
#21 DONE 2.5s

#22 [backend 6/8] RUN pip install --no-cache-dir --default-timeout=600 -r requirements.txt
#22 0.838 Collecting fastapi (from -r requirements.txt (line 1))
#22 1.097   Downloading fastapi-0.116.1-py3-none-any.whl.metadata (28 kB)
#22 1.321 Collecting matplotlib (from -r requirements.txt (line 3))
#22 1.380   Downloading matplotlib-3.10.5-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (11 kB)
#22 1.574 Collecting Pillow (from -r requirements.txt (line 4))
#22 1.632   Downloading pillow-11.3.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (9.0 kB)
#22 1.876 Collecting sionna (from -r requirements.txt (line 5))
#22 1.936   Downloading sionna-1.1.0-py3-none-any.whl.metadata (6.3 kB)
#22 2.006 Collecting sionna-rt (from -r requirements.txt (line 6))
#22 2.067   Downloading sionna_rt-1.1.0-py3-none-any.whl.metadata (4.8 kB)
#22 2.298 Collecting trimesh (from -r requirements.txt (line 7))
#22 2.357   Downloading trimesh-4.7.1-py3-none-any.whl.metadata (18 kB)
#22 2.603 Collecting pyrender>=0.1.45 (from -r requirements.txt (line 8))
#22 2.662   Downloading pyrender-0.1.45-py3-none-any.whl.metadata (1.5 kB)
#22 2.752 Collecting pyglet>=2.0.0 (from -r requirements.txt (line 9))
#22 2.811   Downloading pyglet-2.1.6-py3-none-any.whl.metadata (7.7 kB)
#22 2.884 Collecting PyOpenGL>=3.1.0 (from -r requirements.txt (line 10))
#22 2.946   Downloading PyOpenGL-3.1.9-py3-none-any.whl.metadata (3.3 kB)
#22 3.182 Collecting PyOpenGL_accelerate (from -r requirements.txt (line 11))
#22 3.241   Downloading PyOpenGL_accelerate-3.1.9-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (3.9 kB)
#22 3.310 Collecting python-multipart (from -r requirements.txt (line 12))
#22 3.370   Downloading python_multipart-0.0.20-py3-none-any.whl.metadata (1.8 kB)
#22 3.601 Collecting skyfield>=1.45 (from -r requirements.txt (line 13))
#22 3.660   Downloading skyfield-1.53-py3-none-any.whl.metadata (2.4 kB)
#22 3.748 Collecting httpx (from -r requirements.txt (line 14))
#22 3.818   Downloading httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
#22 3.908 Collecting redis (from -r requirements.txt (line 15))
#22 3.967   Downloading redis-6.2.0-py3-none-any.whl.metadata (10 kB)
#22 4.340 Collecting aiohttp (from -r requirements.txt (line 16))
#22 4.399   Downloading aiohttp-3.12.15-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (7.7 kB)
#22 4.510 Collecting psutil (from -r requirements.txt (line 17))
#22 4.568   Downloading psutil-7.0.0-cp36-abi3-manylinux_2_12_x86_64.manylinux2010_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (22 kB)
#22 4.651 Collecting structlog>=23.2.0 (from -r requirements.txt (line 20))
#22 4.709   Downloading structlog-25.4.0-py3-none-any.whl.metadata (7.6 kB)
#22 4.780 Collecting python-json-logger>=2.0.7 (from -r requirements.txt (line 21))
#22 4.838   Downloading python_json_logger-3.3.0-py3-none-any.whl.metadata (4.0 kB)
#22 4.931 Collecting pyyaml>=6.0.1 (from -r requirements.txt (line 22))
#22 4.991   Downloading PyYAML-6.0.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (2.1 kB)
#22 5.147 Collecting numpy>=1.24.0 (from -r requirements.txt (line 25))
#22 5.205   Downloading numpy-2.3.2-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (62 kB)
#22 5.335 Collecting aiofiles>=23.2.0 (from -r requirements.txt (line 26))
#22 5.394   Downloading aiofiles-24.1.0-py3-none-any.whl.metadata (10 kB)
#22 5.538 Collecting pandas>=2.0.0 (from -r requirements.txt (line 29))
#22 5.597   Downloading pandas-2.3.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (91 kB)
#22 5.770 Collecting scipy>=1.10.0 (from -r requirements.txt (line 30))
#22 5.828   Downloading scipy-1.16.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (61 kB)
#22 5.928 Collecting jinja2>=3.1.0 (from -r requirements.txt (line 31))
#22 5.987   Downloading jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
#22 6.241 Collecting sgp4>=2.21 (from -r requirements.txt (line 32))
#22 6.300   Downloading sgp4-2.24-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (33 kB)
#22 6.383 Collecting motor>=3.3.0 (from -r requirements.txt (line 39))
#22 6.443   Downloading motor-3.7.1-py3-none-any.whl.metadata (21 kB)
#22 6.541 Collecting uvicorn[standard] (from -r requirements.txt (line 2))
#22 6.599   Downloading uvicorn-0.35.0-py3-none-any.whl.metadata (6.5 kB)
#22 6.691 Collecting starlette<0.48.0,>=0.40.0 (from fastapi->-r requirements.txt (line 1))
#22 6.749   Downloading starlette-0.47.2-py3-none-any.whl.metadata (6.2 kB)
#22 6.891 Collecting pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4 (from fastapi->-r requirements.txt (line 1))
#22 6.949   Downloading pydantic-2.11.7-py3-none-any.whl.metadata (67 kB)
#22 7.041 Collecting typing-extensions>=4.8.0 (from fastapi->-r requirements.txt (line 1))
#22 7.099   Downloading typing_extensions-4.14.1-py3-none-any.whl.metadata (3.0 kB)
#22 7.167 Collecting annotated-types>=0.6.0 (from pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4->fastapi->-r requirements.txt (line 1))
#22 7.227   Downloading annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
#22 7.694 Collecting pydantic-core==2.33.2 (from pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4->fastapi->-r requirements.txt (line 1))
#22 7.753   Downloading pydantic_core-2.33.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.8 kB)
#22 7.827 Collecting typing-inspection>=0.4.0 (from pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4->fastapi->-r requirements.txt (line 1))
#22 7.887   Downloading typing_inspection-0.4.1-py3-none-any.whl.metadata (2.6 kB)
#22 7.972 Collecting anyio<5,>=3.6.2 (from starlette<0.48.0,>=0.40.0->fastapi->-r requirements.txt (line 1))
#22 8.031   Downloading anyio-4.10.0-py3-none-any.whl.metadata (4.0 kB)
#22 8.111 Collecting idna>=2.8 (from anyio<5,>=3.6.2->starlette<0.48.0,>=0.40.0->fastapi->-r requirements.txt (line 1))
#22 8.168   Downloading idna-3.10-py3-none-any.whl.metadata (10 kB)
#22 8.230 Collecting sniffio>=1.1 (from anyio<5,>=3.6.2->starlette<0.48.0,>=0.40.0->fastapi->-r requirements.txt (line 1))
#22 8.289   Downloading sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
#22 8.373 Collecting click>=7.0 (from uvicorn[standard]->-r requirements.txt (line 2))
#22 8.431   Downloading click-8.2.1-py3-none-any.whl.metadata (2.5 kB)
#22 8.500 Collecting h11>=0.8 (from uvicorn[standard]->-r requirements.txt (line 2))
#22 8.559   Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
#22 8.648 Collecting httptools>=0.6.3 (from uvicorn[standard]->-r requirements.txt (line 2))
#22 8.706   Downloading httptools-0.6.4-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (3.6 kB)
#22 8.786 Collecting python-dotenv>=0.13 (from uvicorn[standard]->-r requirements.txt (line 2))
#22 8.845   Downloading python_dotenv-1.1.1-py3-none-any.whl.metadata (24 kB)
#22 8.945 Collecting uvloop>=0.15.1 (from uvicorn[standard]->-r requirements.txt (line 2))
#22 9.003   Downloading uvloop-0.21.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
#22 9.113 Collecting watchfiles>=0.13 (from uvicorn[standard]->-r requirements.txt (line 2))
#22 9.171   Downloading watchfiles-1.1.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
#22 9.285 Collecting websockets>=10.4 (from uvicorn[standard]->-r requirements.txt (line 2))
#22 9.344   Downloading websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.8 kB)
#22 9.451 Collecting contourpy>=1.0.1 (from matplotlib->-r requirements.txt (line 3))
#22 9.510   Downloading contourpy-1.3.3-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (5.5 kB)
#22 9.581 Collecting cycler>=0.10 (from matplotlib->-r requirements.txt (line 3))
#22 9.641   Downloading cycler-0.12.1-py3-none-any.whl.metadata (3.8 kB)
#22 9.782 Collecting fonttools>=4.22.0 (from matplotlib->-r requirements.txt (line 3))
#22 9.841   Downloading fonttools-4.59.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (107 kB)
#22 9.966 Collecting kiwisolver>=1.3.1 (from matplotlib->-r requirements.txt (line 3))
#22 10.03   Downloading kiwisolver-1.4.8-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.2 kB)
#22 10.12 Collecting packaging>=20.0 (from matplotlib->-r requirements.txt (line 3))
#22 10.18   Downloading packaging-25.0-py3-none-any.whl.metadata (3.3 kB)
#22 10.27 Collecting pyparsing>=2.3.1 (from matplotlib->-r requirements.txt (line 3))
#22 10.33   Downloading pyparsing-3.2.3-py3-none-any.whl.metadata (5.0 kB)
#22 10.40 Collecting python-dateutil>=2.7 (from matplotlib->-r requirements.txt (line 3))
#22 10.46   Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
#22 10.63 Collecting tensorflow!=2.16,!=2.17,>=2.14 (from sionna->-r requirements.txt (line 5))
#22 10.69   Downloading tensorflow-2.19.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.1 kB)
#22 10.69 Collecting numpy>=1.24.0 (from -r requirements.txt (line 25))
#22 10.75   Downloading numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (61 kB)
#22 10.85 Collecting importlib_resources>=6.4.5 (from sionna->-r requirements.txt (line 5))
#22 10.91   Downloading importlib_resources-6.5.2-py3-none-any.whl.metadata (3.9 kB)
#22 11.16 Collecting mitsuba==3.6.2 (from sionna-rt->-r requirements.txt (line 6))
#22 11.22   Downloading mitsuba-3.6.2-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (6.9 kB)
#22 11.46 Collecting drjit==1.0.3 (from sionna-rt->-r requirements.txt (line 6))
#22 11.52   Downloading drjit-1.0.3-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (7.0 kB)
#22 11.61 Collecting ipywidgets>=8.1.5 (from sionna-rt->-r requirements.txt (line 6))
#22 11.66   Downloading ipywidgets-8.1.7-py3-none-any.whl.metadata (2.4 kB)
#22 11.90 Collecting pythreejs>=2.4.2 (from sionna-rt->-r requirements.txt (line 6))
#22 11.96   Downloading pythreejs-2.4.2-py3-none-any.whl.metadata (5.4 kB)
#22 12.05 Collecting freetype-py (from pyrender>=0.1.45->-r requirements.txt (line 8))
#22 12.11   Downloading freetype_py-2.5.1-py3-none-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_12_x86_64.manylinux2010_x86_64.whl.metadata (6.3 kB)
#22 12.19 Collecting imageio (from pyrender>=0.1.45->-r requirements.txt (line 8))
#22 12.25   Downloading imageio-2.37.0-py3-none-any.whl.metadata (5.2 kB)
#22 12.35 Collecting networkx (from pyrender>=0.1.45->-r requirements.txt (line 8))
#22 12.41   Downloading networkx-3.5-py3-none-any.whl.metadata (6.3 kB)
#22 12.43 Collecting PyOpenGL>=3.1.0 (from -r requirements.txt (line 10))
#22 12.49   Downloading PyOpenGL-3.1.0.zip (2.2 MB)
#22 12.85      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.2/2.2 MB 6.5 MB/s  0:00:00
#22 12.94   Preparing metadata (setup.py): started
#22 13.30   Preparing metadata (setup.py): finished with status 'done'
#22 13.36 Collecting six (from pyrender>=0.1.45->-r requirements.txt (line 8))
#22 13.42   Downloading six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
#22 13.51 Collecting certifi>=2017.4.17 (from skyfield>=1.45->-r requirements.txt (line 13))
#22 13.57   Downloading certifi-2025.8.3-py3-none-any.whl.metadata (2.4 kB)
#22 13.79 Collecting jplephem>=2.13 (from skyfield>=1.45->-r requirements.txt (line 13))
#22 13.85   Downloading jplephem-2.23-py3-none-any.whl.metadata (23 kB)
#22 13.94 Collecting httpcore==1.* (from httpx->-r requirements.txt (line 14))
#22 14.00   Downloading httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
#22 14.08 Collecting aiohappyeyeballs>=2.5.0 (from aiohttp->-r requirements.txt (line 16))
#22 14.14   Downloading aiohappyeyeballs-2.6.1-py3-none-any.whl.metadata (5.9 kB)
#22 14.21 Collecting aiosignal>=1.4.0 (from aiohttp->-r requirements.txt (line 16))
#22 14.27   Downloading aiosignal-1.4.0-py3-none-any.whl.metadata (3.7 kB)
#22 14.34 Collecting attrs>=17.3.0 (from aiohttp->-r requirements.txt (line 16))
#22 14.40   Downloading attrs-25.3.0-py3-none-any.whl.metadata (10 kB)
#22 14.52 Collecting frozenlist>=1.1.1 (from aiohttp->-r requirements.txt (line 16))
#22 14.58   Downloading frozenlist-1.7.0-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (18 kB)
#22 14.76 Collecting multidict<7.0,>=4.5 (from aiohttp->-r requirements.txt (line 16))
#22 14.82   Downloading multidict-6.6.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (5.3 kB)
#22 14.91 Collecting propcache>=0.2.0 (from aiohttp->-r requirements.txt (line 16))
#22 14.97   Downloading propcache-0.3.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (12 kB)
#22 15.21 Collecting yarl<2.0,>=1.17.0 (from aiohttp->-r requirements.txt (line 16))
#22 15.27   Downloading yarl-1.20.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (73 kB)
#22 15.39 Collecting pytz>=2020.1 (from pandas>=2.0.0->-r requirements.txt (line 29))
#22 15.45   Downloading pytz-2025.2-py2.py3-none-any.whl.metadata (22 kB)
#22 15.52 Collecting tzdata>=2022.7 (from pandas>=2.0.0->-r requirements.txt (line 29))
#22 15.58   Downloading tzdata-2025.2-py2.py3-none-any.whl.metadata (1.4 kB)
#22 15.70 Collecting MarkupSafe>=2.0 (from jinja2>=3.1.0->-r requirements.txt (line 31))
#22 15.76   Downloading MarkupSafe-3.0.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.0 kB)
#22 16.00 Collecting pymongo<5.0,>=4.9 (from motor>=3.3.0->-r requirements.txt (line 39))
#22 16.05   Downloading pymongo-4.13.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (22 kB)
#22 16.14 Collecting dnspython<3.0.0,>=1.16.0 (from pymongo<5.0,>=4.9->motor>=3.3.0->-r requirements.txt (line 39))
#22 16.20   Downloading dnspython-2.7.0-py3-none-any.whl.metadata (5.8 kB)
#22 16.29 Collecting comm>=0.1.3 (from ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 16.35   Downloading comm-0.2.3-py3-none-any.whl.metadata (3.7 kB)
#22 16.44 Collecting ipython>=6.1.0 (from ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 16.50   Downloading ipython-9.4.0-py3-none-any.whl.metadata (4.4 kB)
#22 16.60 Collecting traitlets>=4.3.1 (from ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 16.66   Downloading traitlets-5.14.3-py3-none-any.whl.metadata (10 kB)
#22 16.73 Collecting widgetsnbextension~=4.0.14 (from ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 16.79   Downloading widgetsnbextension-4.0.14-py3-none-any.whl.metadata (1.6 kB)
#22 16.85 Collecting jupyterlab_widgets~=3.0.15 (from ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 16.91   Downloading jupyterlab_widgets-3.0.15-py3-none-any.whl.metadata (20 kB)
#22 17.00 Collecting decorator (from ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 17.06   Downloading decorator-5.2.1-py3-none-any.whl.metadata (3.9 kB)
#22 17.12 Collecting ipython-pygments-lexers (from ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 17.18   Downloading ipython_pygments_lexers-1.1.1-py3-none-any.whl.metadata (1.1 kB)
#22 17.25 Collecting jedi>=0.16 (from ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 17.31   Downloading jedi-0.19.2-py2.py3-none-any.whl.metadata (22 kB)
#22 17.38 Collecting matplotlib-inline (from ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 17.44   Downloading matplotlib_inline-0.1.7-py3-none-any.whl.metadata (3.9 kB)
#22 17.51 Collecting pexpect>4.3 (from ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 17.57   Downloading pexpect-4.9.0-py2.py3-none-any.whl.metadata (2.5 kB)
#22 17.66 Collecting prompt_toolkit<3.1.0,>=3.0.41 (from ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 17.71   Downloading prompt_toolkit-3.0.51-py3-none-any.whl.metadata (6.4 kB)
#22 17.79 Collecting pygments>=2.4.0 (from ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 17.85   Downloading pygments-2.19.2-py3-none-any.whl.metadata (2.5 kB)
#22 17.91 Collecting stack_data (from ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 17.97   Downloading stack_data-0.6.3-py3-none-any.whl.metadata (18 kB)
#22 18.05 Collecting wcwidth (from prompt_toolkit<3.1.0,>=3.0.41->ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 18.11   Downloading wcwidth-0.2.13-py2.py3-none-any.whl.metadata (14 kB)
#22 18.19 Collecting parso<0.9.0,>=0.8.4 (from jedi>=0.16->ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 18.24   Downloading parso-0.8.4-py2.py3-none-any.whl.metadata (7.7 kB)
#22 18.31 Collecting ptyprocess>=0.5 (from pexpect>4.3->ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 18.37   Downloading ptyprocess-0.7.0-py2.py3-none-any.whl.metadata (1.3 kB)
#22 18.61 Collecting ipydatawidgets>=1.1.1 (from pythreejs>=2.4.2->sionna-rt->-r requirements.txt (line 6))
#22 18.67   Downloading ipydatawidgets-4.3.5-py2.py3-none-any.whl.metadata (1.4 kB)
#22 18.75 Collecting traittypes>=0.2.0 (from ipydatawidgets>=1.1.1->pythreejs>=2.4.2->sionna-rt->-r requirements.txt (line 6))
#22 18.81   Downloading traittypes-0.2.1-py2.py3-none-any.whl.metadata (1.0 kB)
#22 18.89 Collecting absl-py>=1.0.0 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 18.95   Downloading absl_py-2.3.1-py3-none-any.whl.metadata (3.3 kB)
#22 19.02 Collecting astunparse>=1.6.0 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 19.08   Downloading astunparse-1.6.3-py2.py3-none-any.whl.metadata (4.4 kB)
#22 19.15 Collecting flatbuffers>=24.3.25 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 19.21   Downloading flatbuffers-25.2.10-py2.py3-none-any.whl.metadata (875 bytes)
#22 19.28 Collecting gast!=0.5.0,!=0.5.1,!=0.5.2,>=0.2.1 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 19.34   Downloading gast-0.6.0-py3-none-any.whl.metadata (1.3 kB)
#22 19.41 Collecting google-pasta>=0.1.1 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 19.47   Downloading google_pasta-0.2.0-py3-none-any.whl.metadata (814 bytes)
#22 19.54 Collecting libclang>=13.0.0 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 19.60   Downloading libclang-18.1.1-py2.py3-none-manylinux2010_x86_64.whl.metadata (5.2 kB)
#22 19.82 Collecting opt-einsum>=2.3.2 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 19.88   Downloading opt_einsum-3.4.0-py3-none-any.whl.metadata (6.3 kB)
#22 20.05 Collecting protobuf!=4.21.0,!=4.21.1,!=4.21.2,!=4.21.3,!=4.21.4,!=4.21.5,<6.0.0dev,>=3.20.3 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 20.11   Downloading protobuf-5.29.5-cp38-abi3-manylinux2014_x86_64.whl.metadata (592 bytes)
#22 20.20 Collecting requests<3,>=2.21.0 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 20.25   Downloading requests-2.32.4-py3-none-any.whl.metadata (4.9 kB)
#22 20.26 Requirement already satisfied: setuptools in /usr/local/lib/python3.11/site-packages (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5)) (65.5.1)
#22 20.33 Collecting termcolor>=1.1.0 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 20.39   Downloading termcolor-3.1.0-py3-none-any.whl.metadata (6.4 kB)
#22 20.56 Collecting wrapt>=1.11.0 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 20.62   Downloading wrapt-1.17.2-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.4 kB)
#22 20.96 Collecting grpcio<2.0,>=1.24.3 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 21.02   Downloading grpcio-1.74.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (3.8 kB)
#22 21.10 Collecting tensorboard~=2.19.0 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 21.16   Downloading tensorboard-2.19.0-py3-none-any.whl.metadata (1.8 kB)
#22 21.24 Collecting keras>=3.5.0 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 21.30   Downloading keras-3.11.1-py3-none-any.whl.metadata (5.9 kB)
#22 21.40 Collecting h5py>=3.11.0 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 21.46   Downloading h5py-3.14.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (2.7 kB)
#22 21.55 Collecting ml-dtypes<1.0.0,>=0.5.1 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 21.61   Downloading ml_dtypes-0.5.3-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (8.9 kB)
#22 21.70 Collecting tensorflow-io-gcs-filesystem>=0.23.1 (from tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 21.76   Downloading tensorflow_io_gcs_filesystem-0.37.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (14 kB)
#22 21.89 Collecting charset_normalizer<4,>=2 (from requests<3,>=2.21.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 21.95   Downloading charset_normalizer-3.4.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (35 kB)
#22 22.05 Collecting urllib3<3,>=1.21.1 (from requests<3,>=2.21.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 22.11   Downloading urllib3-2.5.0-py3-none-any.whl.metadata (6.5 kB)
#22 22.21 Collecting markdown>=2.6.8 (from tensorboard~=2.19.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 22.27   Downloading markdown-3.8.2-py3-none-any.whl.metadata (5.1 kB)
#22 22.39 Collecting tensorboard-data-server<0.8.0,>=0.7.0 (from tensorboard~=2.19.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 22.45   Downloading tensorboard_data_server-0.7.2-py3-none-manylinux_2_31_x86_64.whl.metadata (1.1 kB)
#22 22.52 Collecting werkzeug>=1.0.1 (from tensorboard~=2.19.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 22.58   Downloading werkzeug-3.1.3-py3-none-any.whl.metadata (3.7 kB)
#22 22.60 Requirement already satisfied: wheel<1.0,>=0.23.0 in /usr/local/lib/python3.11/site-packages (from astunparse>=1.6.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5)) (0.45.1)
#22 22.70 Collecting rich (from keras>=3.5.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 22.75   Downloading rich-14.1.0-py3-none-any.whl.metadata (18 kB)
#22 22.82 Collecting namex (from keras>=3.5.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 22.88   Downloading namex-0.1.0-py3-none-any.whl.metadata (322 bytes)
#22 22.99 Collecting optree (from keras>=3.5.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 23.05   Downloading optree-0.17.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (33 kB)
#22 23.16 Collecting markdown-it-py>=2.2.0 (from rich->keras>=3.5.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 23.22   Downloading markdown_it_py-3.0.0-py3-none-any.whl.metadata (6.9 kB)
#22 23.29 Collecting mdurl~=0.1 (from markdown-it-py>=2.2.0->rich->keras>=3.5.0->tensorflow!=2.16,!=2.17,>=2.14->sionna->-r requirements.txt (line 5))
#22 23.35   Downloading mdurl-0.1.2-py3-none-any.whl.metadata (1.6 kB)
#22 23.43 Collecting executing>=1.2.0 (from stack_data->ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 23.48   Downloading executing-2.2.0-py2.py3-none-any.whl.metadata (8.9 kB)
#22 23.56 Collecting asttokens>=2.1.0 (from stack_data->ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 23.62   Downloading asttokens-3.0.0-py3-none-any.whl.metadata (4.7 kB)
#22 23.69 Collecting pure-eval (from stack_data->ipython>=6.1.0->ipywidgets>=8.1.5->sionna-rt->-r requirements.txt (line 6))
#22 23.75   Downloading pure_eval-0.2.3-py3-none-any.whl.metadata (6.3 kB)
#22 23.81 Downloading fastapi-0.116.1-py3-none-any.whl (95 kB)
#22 23.88 Downloading pydantic-2.11.7-py3-none-any.whl (444 kB)
#22 23.98 Downloading pydantic_core-2.33.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.0 MB)
#22 24.19    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.0/2.0 MB 9.6 MB/s  0:00:00
#22 24.25 Downloading starlette-0.47.2-py3-none-any.whl (72 kB)
#22 24.31 Downloading anyio-4.10.0-py3-none-any.whl (107 kB)
#22 24.38 Downloading uvicorn-0.35.0-py3-none-any.whl (66 kB)
#22 24.45 Downloading matplotlib-3.10.5-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (8.7 MB)
#22 25.29    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8.7/8.7 MB 10.3 MB/s  0:00:00
#22 25.35 Downloading pillow-11.3.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (6.6 MB)
#22 26.17    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.6/6.6 MB 8.0 MB/s  0:00:00
#22 26.23 Downloading sionna-1.1.0-py3-none-any.whl (520 kB)
#22 26.36 Downloading sionna_rt-1.1.0-py3-none-any.whl (8.5 MB)
#22 27.35    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8.5/8.5 MB 8.6 MB/s  0:00:00
#22 27.59 Downloading drjit-1.0.3-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (4.3 MB)
#22 28.35    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.3/4.3 MB 5.5 MB/s  0:00:00
#22 28.40 Downloading mitsuba-3.6.2-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (57.7 MB)
#22 34.62    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 57.7/57.7 MB 9.3 MB/s  0:00:06
#22 34.68 Downloading numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (18.3 MB)
#22 36.50    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 18.3/18.3 MB 10.0 MB/s  0:00:01
#22 36.56 Downloading trimesh-4.7.1-py3-none-any.whl (709 kB)
#22 36.67    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 709.0/709.0 kB 5.6 MB/s  0:00:00
#22 36.73 Downloading pyrender-0.1.45-py3-none-any.whl (1.2 MB)
#22 36.89    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.2/1.2 MB 7.6 MB/s  0:00:00
#22 36.95 Downloading pyglet-2.1.6-py3-none-any.whl (983 kB)
#22 37.07    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 984.0/984.0 kB 7.5 MB/s  0:00:00
#22 37.14 Downloading PyOpenGL_accelerate-3.1.9-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.2 MB)
#22 37.54    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.2/3.2 MB 8.0 MB/s  0:00:00
#22 37.60 Downloading python_multipart-0.0.20-py3-none-any.whl (24 kB)
#22 37.66 Downloading skyfield-1.53-py3-none-any.whl (366 kB)
#22 37.75 Downloading httpx-0.28.1-py3-none-any.whl (73 kB)
#22 37.82 Downloading httpcore-1.0.9-py3-none-any.whl (78 kB)
#22 37.88 Downloading redis-6.2.0-py3-none-any.whl (278 kB)
#22 37.97 Downloading aiohttp-3.12.15-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (1.7 MB)
#22 38.17    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.7/1.7 MB 8.5 MB/s  0:00:00
#22 38.23 Downloading multidict-6.6.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (246 kB)
#22 38.32 Downloading yarl-1.20.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (348 kB)
#22 38.41 Downloading psutil-7.0.0-cp36-abi3-manylinux_2_12_x86_64.manylinux2010_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (277 kB)
#22 38.49 Downloading structlog-25.4.0-py3-none-any.whl (68 kB)
#22 38.56 Downloading python_json_logger-3.3.0-py3-none-any.whl (15 kB)
#22 38.62 Downloading PyYAML-6.0.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (762 kB)
#22 38.71    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 763.0/763.0 kB 8.6 MB/s  0:00:00
#22 38.77 Downloading aiofiles-24.1.0-py3-none-any.whl (15 kB)
#22 38.83 Downloading pandas-2.3.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (12.4 MB)
#22 40.16    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 12.4/12.4 MB 9.3 MB/s  0:00:01
#22 40.22 Downloading scipy-1.16.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (35.4 MB)
#22 43.65    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 35.4/35.4 MB 10.3 MB/s  0:00:03
#22 43.71 Downloading jinja2-3.1.6-py3-none-any.whl (134 kB)
#22 43.78 Downloading sgp4-2.24-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (234 kB)
#22 43.86 Downloading motor-3.7.1-py3-none-any.whl (74 kB)
#22 43.92 Downloading pymongo-4.13.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (1.4 MB)
#22 44.08    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.4/1.4 MB 14.9 MB/s  0:00:00
#22 44.14 Downloading dnspython-2.7.0-py3-none-any.whl (313 kB)
#22 44.23 Downloading aiohappyeyeballs-2.6.1-py3-none-any.whl (15 kB)
#22 44.29 Downloading aiosignal-1.4.0-py3-none-any.whl (7.5 kB)
#22 44.35 Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
#22 44.41 Downloading attrs-25.3.0-py3-none-any.whl (63 kB)
#22 44.48 Downloading certifi-2025.8.3-py3-none-any.whl (161 kB)
#22 44.56 Downloading click-8.2.1-py3-none-any.whl (102 kB)
#22 44.63 Downloading contourpy-1.3.3-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (355 kB)
#22 44.72 Downloading cycler-0.12.1-py3-none-any.whl (8.3 kB)
#22 44.79 Downloading fonttools-4.59.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (5.0 MB)
#22 45.42    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.0/5.0 MB 7.9 MB/s  0:00:00
#22 45.48 Downloading frozenlist-1.7.0-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (235 kB)
#22 45.56 Downloading h11-0.16.0-py3-none-any.whl (37 kB)
#22 45.62 Downloading httptools-0.6.4-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (459 kB)
#22 45.73 Downloading idna-3.10-py3-none-any.whl (70 kB)
#22 45.79 Downloading importlib_resources-6.5.2-py3-none-any.whl (37 kB)
#22 45.85 Downloading ipywidgets-8.1.7-py3-none-any.whl (139 kB)
#22 45.93 Downloading jupyterlab_widgets-3.0.15-py3-none-any.whl (216 kB)
#22 46.01 Downloading widgetsnbextension-4.0.14-py3-none-any.whl (2.2 MB)
#22 46.26    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.2/2.2 MB 8.5 MB/s  0:00:00
#22 46.32 Downloading comm-0.2.3-py3-none-any.whl (7.3 kB)
#22 46.38 Downloading ipython-9.4.0-py3-none-any.whl (611 kB)
#22 46.45    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 611.0/611.0 kB 8.1 MB/s  0:00:00
#22 46.51 Downloading prompt_toolkit-3.0.51-py3-none-any.whl (387 kB)
#22 46.61 Downloading jedi-0.19.2-py2.py3-none-any.whl (1.6 MB)
#22 46.79    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.6/1.6 MB 8.7 MB/s  0:00:00
#22 46.85 Downloading parso-0.8.4-py2.py3-none-any.whl (103 kB)
#22 46.91 Downloading jplephem-2.23-py3-none-any.whl (49 kB)
#22 46.98 Downloading kiwisolver-1.4.8-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (1.4 MB)
#22 47.13    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.4/1.4 MB 9.3 MB/s  0:00:00
#22 47.19 Downloading MarkupSafe-3.0.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (23 kB)
#22 47.25 Downloading packaging-25.0-py3-none-any.whl (66 kB)
#22 47.32 Downloading pexpect-4.9.0-py2.py3-none-any.whl (63 kB)
#22 47.38 Downloading propcache-0.3.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (213 kB)
#22 47.46 Downloading ptyprocess-0.7.0-py2.py3-none-any.whl (13 kB)
#22 47.52 Downloading pygments-2.19.2-py3-none-any.whl (1.2 MB)
#22 47.65    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.2/1.2 MB 9.0 MB/s  0:00:00
#22 47.72 Downloading pyparsing-3.2.3-py3-none-any.whl (111 kB)
#22 47.78 Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
#22 47.86 Downloading python_dotenv-1.1.1-py3-none-any.whl (20 kB)
#22 47.92 Downloading pythreejs-2.4.2-py3-none-any.whl (3.4 MB)
#22 48.28    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.4/3.4 MB 9.4 MB/s  0:00:00
#22 48.34 Downloading ipydatawidgets-4.3.5-py2.py3-none-any.whl (271 kB)
#22 48.42 Downloading pytz-2025.2-py2.py3-none-any.whl (509 kB)
#22 48.52 Downloading six-1.17.0-py2.py3-none-any.whl (11 kB)
#22 48.58 Downloading sniffio-1.3.1-py3-none-any.whl (10 kB)
#22 48.64 Downloading tensorflow-2.19.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (644.9 MB)
#22 121.1    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 644.9/644.9 MB 8.1 MB/s  0:01:12
#22 121.2 Downloading grpcio-1.74.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (6.2 MB)
#22 122.0    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.2/6.2 MB 7.2 MB/s  0:00:00
#22 122.1 Downloading ml_dtypes-0.5.3-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (4.9 MB)
#22 122.7    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.9/4.9 MB 8.2 MB/s  0:00:00
#22 122.8 Downloading protobuf-5.29.5-cp38-abi3-manylinux2014_x86_64.whl (319 kB)
#22 122.9 Downloading requests-2.32.4-py3-none-any.whl (64 kB)
#22 122.9 Downloading charset_normalizer-3.4.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (147 kB)
#22 123.0 Downloading tensorboard-2.19.0-py3-none-any.whl (5.5 MB)
#22 123.6    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.5/5.5 MB 9.1 MB/s  0:00:00
#22 123.7 Downloading tensorboard_data_server-0.7.2-py3-none-manylinux_2_31_x86_64.whl (6.6 MB)
#22 124.3    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.6/6.6 MB 10.2 MB/s  0:00:00
#22 124.4 Downloading urllib3-2.5.0-py3-none-any.whl (129 kB)
#22 124.4 Downloading absl_py-2.3.1-py3-none-any.whl (135 kB)
#22 124.5 Downloading astunparse-1.6.3-py2.py3-none-any.whl (12 kB)
#22 124.6 Downloading flatbuffers-25.2.10-py2.py3-none-any.whl (30 kB)
#22 124.6 Downloading gast-0.6.0-py3-none-any.whl (21 kB)
#22 124.7 Downloading google_pasta-0.2.0-py3-none-any.whl (57 kB)
#22 124.8 Downloading h5py-3.14.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (4.5 MB)
#22 125.3    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.5/4.5 MB 9.0 MB/s  0:00:00
#22 125.4 Downloading keras-3.11.1-py3-none-any.whl (1.4 MB)
#22 125.6    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.4/1.4 MB 8.0 MB/s  0:00:00
#22 125.6 Downloading libclang-18.1.1-py2.py3-none-manylinux2010_x86_64.whl (24.5 MB)
#22 129.0    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 24.5/24.5 MB 7.3 MB/s  0:00:03
#22 129.0 Downloading markdown-3.8.2-py3-none-any.whl (106 kB)
#22 129.1 Downloading opt_einsum-3.4.0-py3-none-any.whl (71 kB)
#22 129.2 Downloading tensorflow_io_gcs_filesystem-0.37.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (5.1 MB)
#22 130.0    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.1/5.1 MB 5.9 MB/s  0:00:00
#22 130.1 Downloading termcolor-3.1.0-py3-none-any.whl (7.7 kB)
#22 130.1 Downloading traitlets-5.14.3-py3-none-any.whl (85 kB)
#22 130.2 Downloading traittypes-0.2.1-py2.py3-none-any.whl (8.6 kB)
#22 130.3 Downloading typing_extensions-4.14.1-py3-none-any.whl (43 kB)
#22 130.3 Downloading typing_inspection-0.4.1-py3-none-any.whl (14 kB)
#22 130.4 Downloading tzdata-2025.2-py2.py3-none-any.whl (347 kB)
#22 130.5 Downloading uvloop-0.21.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (4.0 MB)
#22 131.2    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.0/4.0 MB 6.2 MB/s  0:00:00
#22 131.2 Downloading watchfiles-1.1.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (453 kB)
#22 131.4 Downloading websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (182 kB)
#22 131.4 Downloading werkzeug-3.1.3-py3-none-any.whl (224 kB)
#22 131.5 Downloading wrapt-1.17.2-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (83 kB)
#22 131.6 Downloading decorator-5.2.1-py3-none-any.whl (9.2 kB)
#22 131.7 Downloading freetype_py-2.5.1-py3-none-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_12_x86_64.manylinux2010_x86_64.whl (1.0 MB)
#22 131.8    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.0/1.0 MB 6.4 MB/s  0:00:00
#22 131.9 Downloading imageio-2.37.0-py3-none-any.whl (315 kB)
#22 132.0 Downloading ipython_pygments_lexers-1.1.1-py3-none-any.whl (8.1 kB)
#22 132.0 Downloading matplotlib_inline-0.1.7-py3-none-any.whl (9.9 kB)
#22 132.1 Downloading namex-0.1.0-py3-none-any.whl (5.9 kB)
#22 132.2 Downloading networkx-3.5-py3-none-any.whl (2.0 MB)
#22 132.5    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.0/2.0 MB 6.3 MB/s  0:00:00
#22 132.5 Downloading optree-0.17.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (402 kB)
#22 132.7 Downloading rich-14.1.0-py3-none-any.whl (243 kB)
#22 132.7 Downloading markdown_it_py-3.0.0-py3-none-any.whl (87 kB)
#22 132.8 Downloading mdurl-0.1.2-py3-none-any.whl (10.0 kB)
#22 132.9 Downloading stack_data-0.6.3-py3-none-any.whl (24 kB)
#22 132.9 Downloading asttokens-3.0.0-py3-none-any.whl (26 kB)
#22 133.0 Downloading executing-2.2.0-py2.py3-none-any.whl (26 kB)
#22 133.1 Downloading pure_eval-0.2.3-py3-none-any.whl (11 kB)
#22 133.1 Downloading wcwidth-0.2.13-py2.py3-none-any.whl (34 kB)
#22 133.7 Building wheels for collected packages: PyOpenGL
#22 133.7   DEPRECATION: Building 'PyOpenGL' using the legacy setup.py bdist_wheel mechanism, which will be removed in a future version. pip 25.3 will enforce this behaviour change. A possible replacement is to use the standardized build interface by setting the `--use-pep517` option, (possibly combined with `--no-build-isolation`), or adding a `pyproject.toml` file to the source tree of 'PyOpenGL'. Discussion can be found at https://github.com/pypa/pip/issues/6334
#22 133.7   Building wheel for PyOpenGL (setup.py): started
#22 134.5   Building wheel for PyOpenGL (setup.py): finished with status 'done'
#22 134.5   Created wheel for PyOpenGL: filename=PyOpenGL-3.1.0-py3-none-any.whl size=1745192 sha256=d815fd58aef7fabc282a4046993e097e96d789602fbfe9cc7f2e5e614d262329
#22 134.5   Stored in directory: /tmp/pip-ephem-wheel-cache-dbuujzx2/wheels/2f/37/f5/f88cd3dddf75bc3ce608e44bf8a79078c408bf1f351a50818e
#22 134.5 Successfully built PyOpenGL
#22 134.6 Installing collected packages: wcwidth, sgp4, pytz, PyOpenGL_accelerate, PyOpenGL, pure-eval, ptyprocess, namex, libclang, flatbuffers, wrapt, widgetsnbextension, websockets, uvloop, urllib3, tzdata, typing-extensions, traitlets, termcolor, tensorflow-io-gcs-filesystem, tensorboard-data-server, structlog, sniffio, six, redis, pyyaml, python-multipart, python-json-logger, python-dotenv, pyparsing, pygments, pyglet, psutil, protobuf, propcache, prompt_toolkit, Pillow, pexpect, parso, packaging, opt-einsum, numpy, networkx, multidict, mdurl, MarkupSafe, markdown, kiwisolver, jupyterlab_widgets, importlib_resources, idna, httptools, h11, grpcio, gast, frozenlist, freetype-py, fonttools, executing, drjit, dnspython, decorator, cycler, comm, click, charset_normalizer, certifi, attrs, asttokens, annotated-types, aiohappyeyeballs, aiofiles, absl-py, yarl, werkzeug, uvicorn, typing-inspection, trimesh, traittypes, stack_data, scipy, requests, python-dateutil, pymongo, pydantic-core, optree, ml-dtypes, mitsuba, matplotlib-inline, markdown-it-py, jplephem, jinja2, jedi, ipython-pygments-lexers, imageio, httpcore, h5py, google-pasta, contourpy, astunparse, anyio, aiosignal, watchfiles, tensorboard, starlette, skyfield, rich, pyrender, pydantic, pandas, motor, matplotlib, ipython, httpx, aiohttp, keras, ipywidgets, fastapi, tensorflow, ipydatawidgets, pythreejs, sionna-rt, sionna
#22 152.1
#22 152.1 WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.
#22 152.1 Successfully installed MarkupSafe-3.0.2 Pillow-11.3.0 PyOpenGL-3.1.0 PyOpenGL_accelerate-3.1.9 absl-py-2.3.1 aiofiles-24.1.0 aiohappyeyeballs-2.6.1 aiohttp-3.12.15 aiosignal-1.4.0 annotated-types-0.7.0 anyio-4.10.0 asttokens-3.0.0 astunparse-1.6.3 attrs-25.3.0 certifi-2025.8.3 charset_normalizer-3.4.2 click-8.2.1 comm-0.2.3 contourpy-1.3.3 cycler-0.12.1 decorator-5.2.1 dnspython-2.7.0 drjit-1.0.3 executing-2.2.0 fastapi-0.116.1 flatbuffers-25.2.10 fonttools-4.59.0 freetype-py-2.5.1 frozenlist-1.7.0 gast-0.6.0 google-pasta-0.2.0 grpcio-1.74.0 h11-0.16.0 h5py-3.14.0 httpcore-1.0.9 httptools-0.6.4 httpx-0.28.1 idna-3.10 imageio-2.37.0 importlib_resources-6.5.2 ipydatawidgets-4.3.5 ipython-9.4.0 ipython-pygments-lexers-1.1.1 ipywidgets-8.1.7 jedi-0.19.2 jinja2-3.1.6 jplephem-2.23 jupyterlab_widgets-3.0.15 keras-3.11.1 kiwisolver-1.4.8 libclang-18.1.1 markdown-3.8.2 markdown-it-py-3.0.0 matplotlib-3.10.5 matplotlib-inline-0.1.7 mdurl-0.1.2 mitsuba-3.6.2 ml-dtypes-0.5.3 motor-3.7.1 multidict-6.6.3 namex-0.1.0 networkx-3.5 numpy-1.26.4 opt-einsum-3.4.0 optree-0.17.0 packaging-25.0 pandas-2.3.1 parso-0.8.4 pexpect-4.9.0 prompt_toolkit-3.0.51 propcache-0.3.2 protobuf-5.29.5 psutil-7.0.0 ptyprocess-0.7.0 pure-eval-0.2.3 pydantic-2.11.7 pydantic-core-2.33.2 pyglet-2.1.6 pygments-2.19.2 pymongo-4.13.2 pyparsing-3.2.3 pyrender-0.1.45 python-dateutil-2.9.0.post0 python-dotenv-1.1.1 python-json-logger-3.3.0 python-multipart-0.0.20 pythreejs-2.4.2 pytz-2025.2 pyyaml-6.0.2 redis-6.2.0 requests-2.32.4 rich-14.1.0 scipy-1.16.1 sgp4-2.24 sionna-1.1.0 sionna-rt-1.1.0 six-1.17.0 skyfield-1.53 sniffio-1.3.1 stack_data-0.6.3 starlette-0.47.2 structlog-25.4.0 tensorboard-2.19.0 tensorboard-data-server-0.7.2 tensorflow-2.19.0 tensorflow-io-gcs-filesystem-0.37.1 termcolor-3.1.0 traitlets-5.14.3 traittypes-0.2.1 trimesh-4.7.1 typing-extensions-4.14.1 typing-inspection-0.4.1 tzdata-2025.2 urllib3-2.5.0 uvicorn-0.35.0 uvloop-0.21.0 watchfiles-1.1.0 wcwidth-0.2.13 websockets-15.0.1 werkzeug-3.1.3 widgetsnbextension-4.0.14 wrapt-1.17.2 yarl-1.20.1
#22 DONE 153.1s

#23 [backend 7/8] COPY . .
#23 DONE 0.2s

#24 [backend 8/8] RUN mkdir -p /app/data /app/netstack/tle_data &&     chmod 755 /app/data /app/netstack/tle_data
#24 DONE 0.2s

#25 [backend] exporting to image
#25 exporting layers
#25 exporting layers 10.0s done
#25 writing image sha256:d0bce2b861efdc3bb0a0305d39482574be6104586c84ee6d89e3030ea143a2d5 done
#25 naming to docker.io/library/simworld-backend done
#25 DONE 10.0s

#26 [backend] resolving provenance for metadata file
#26 DONE 0.0s
[+] Building 2/2
 ✔ simworld-backend   Built                                                                   0.0s
 ✔ simworld-frontend  Built                                                                   0.0s
✅ SimWorld 服務構建完成
make[1]: Leaving directory '/home/sat/ntn-stack'
✅ 所有服務構建完成