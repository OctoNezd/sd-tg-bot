# StableDiffusion AUTOMATIC1111 Telegram bot

## Usage

1. Create .env file or systemd service with following environment variables. Customize them to apply to you, obviously.

```
TG_BOT_API_TOKEN=telegramtokenhere
SD_WEBUI_URL=http://my.stable-diffusion.server:7860/
CHAT_WHITELIST=my-telegram-group-id
GENERATION_CONFIG={"negative_prompt": "(worst quality:1.6, low quality:1.6), (zombie, sketch, interlocked fingers, comic)", "sampler_index": "UniPC", "width": 512, "height": 768, "steps": 25}
RANDOM_PROMPT_PERCENTAGE=5
```

(RANDOM_PROMPT_PERCENTAGE defines the random percentage at which bot will catch random message in chat and prompt it for shit and giggles. Set to 0 to disable)

2. `poetry install`

3. Run `python3 main.py`

## Using with AbdBarho/stable-diffusion-webui-docker

Add docker-compose.override.yml file:

```yml
version: "3.9"
services:
    telegram-bot:
        profiles: ["auto", "auto-cpu"]
        build: "./sd-tg-bot"
        restart: unless-stopped
        environment:
            - SD_WEBUI_URL=http://auto:7860 # Or auto-cpu
```

Clone bot:

`git clone https://github.com/OctoNezd/sd-tg-bot.git`

Setup .env file or specify parameters in `environment:`
