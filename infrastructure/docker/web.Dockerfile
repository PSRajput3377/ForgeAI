# ForgeAI web image (Next.js). Not wired into docker-compose yet — the frontend
# is run on the host during development (`make web-dev`). Provided so the web
# app can be containerized for deployment in Phase 11.
FROM node:22-alpine

WORKDIR /app/apps/web

COPY apps/web/package.json ./
RUN npm install

COPY apps/web/ ./

EXPOSE 3000
CMD ["npm", "run", "dev"]
