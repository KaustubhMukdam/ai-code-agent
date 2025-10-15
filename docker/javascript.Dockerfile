FROM node:20-slim

WORKDIR /code

RUN npm install -g eslint

RUN useradd -m -u 1001 coderunner || true
USER node

CMD ["node"]