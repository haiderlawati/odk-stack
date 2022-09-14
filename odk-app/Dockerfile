# build stage
FROM node:lts-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ARG MODE=${MODE}
RUN if [ "$MODE" = "development" ] ; then mv .env.development .env.production ; fi
RUN if [ "$MODE" = "staging" ] ; then mv .env.staging .env.production ; fi
ARG APP_NAME=${APP_NAME}
RUN node update-manifest.js
RUN npm run build

# production stage
FROM nginx:stable-alpine as production-stage
RUN rm /etc/nginx/conf.d/default.conf
# Haider added this
RUN mkdir /etc/nginx/certs
COPY 5936616ab5877ad8.crt /etc/nginx/certs/5936616ab5877ad8.crt
COPY brand_cp.odp-cloud.com.key /etc/nginx/certs/brand_cp.odp-cloud.com.key
# END of new addition
COPY production-nginx.conf /etc/nginx/conf.d/production.conf
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
# Haider added this part
EXPOSE 443
# END of new addition
CMD ["nginx", "-g", "daemon off;"]
