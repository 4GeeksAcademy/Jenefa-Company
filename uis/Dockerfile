FROM node:alpine

WORKDIR /workspace

# Install workspace dependencies explicitly per app to keep install boundaries clear.
COPY package.json ./
COPY src/package.json ./src/package.json
COPY uis/website/package.json ./uis/website/package.json
COPY uis/web/package.json ./uis/web/package.json

RUN npm install -w website && npm install -w web

COPY uis/start.sh ./uis/start.sh
RUN chmod +x ./uis/start.sh

CMD ["/bin/sh", "/workspace/uis/start.sh"]
