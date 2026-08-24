FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm install

COPY . .

RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]