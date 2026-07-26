FROM denoland/deno:2.9.4

WORKDIR /app

COPY deno.json deno.lock ./
COPY . .

RUN deno cache main.ts

EXPOSE 3000

CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-env", "--env", "main.ts"]
