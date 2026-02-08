FROM node:alpine

WORKDIR /usr/src/app

COPY package.json .
COPY package-lock.json .
RUN npm install

COPY src/ .
COPY tsconfig.json .
COPY tsconfig.node.json .
COPY vite.config.ts .
COPY .env .


EXPOSE 8030

CMD ["npm", "run", "dev"]