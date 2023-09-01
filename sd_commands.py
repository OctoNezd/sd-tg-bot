import random
import base64
import html
import io
import re
import json
import logging
import settings
import sd_api
from telegram import Update
from telegram.ext import ContextTypes
import bleach

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

GENERIC_PROMPT_CONFIG = {"do_not_save_samples": True, "do_not_save_grid": True}


async def rand_print(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    percent = random.randint(1, 100)
    logger.debug(percent)
    context.args = []
    if update.message.text is not None:
        context.args = update.message.text.split(" ")
    if update.message.caption is not None:
        context.args = update.message.caption.split(" ")
    if percent < settings.RANDOM_PROMPT_PERCENTAGE and len(context.args) > 0:
        logger.info("Random query! %s%%", percent)
        try:
            await prompt(update, context)
        except sd_api.QueueIsBusy:
            pass

POTENTIAL_NSFW_RE = re.compile(r"(nsfw|sex|naked|breast|pussy|vagina|cock|dick|penis|futa)")

async def prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or context.args is None:
        return
    if len(context.args) == 0:
        await update.message.reply_text("you hadn't specified a prompt.")
        return
    query = " ".join(context.args)
    may_be_nsfw = POTENTIAL_NSFW_RE.match(query)
    async with await sd_api.get_session(error_on_queue=True) as session:
        await update.message.reply_chat_action("upload_photo")
        async with session.post(
            "/sdapi/v1/txt2img",
            json=dict(
                prompt=query, **settings.GENERATION_CONFIG, **GENERIC_PROMPT_CONFIG
            ),
            timeout=120,
        ) as response:
            if response.status == 200:
                data = await response.json()
                cap = "\n".join(json.loads(data["info"])["infotexts"])
                image = io.BytesIO(base64.b64decode(data["images"][0].split(",", 1)[0]))
                image.seek(0)
                await update.message.reply_photo(photo=image, caption=cap[:1024], has_spoiler=may_be_nsfw)
            else:
                raise sd_api.SDError((await response.json())["errors"])


async def list_loras(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    async with await sd_api.get_session(error_on_queue=False) as session:
        await update.message.reply_chat_action("typing")
        async with session.get(
            "/sdapi/v1/loras",
            timeout=120,
        ) as response:
            if response.status == 200:
                loras = await response.json()
                if len(loras) == 0:
                    await update.message.reply_text("No loras installed")
                    return
                msg = ""
                for lora in loras:
                    msg += f"• {html.escape(lora['name'])}\n"
                    usage = f"<lora:{lora['alias']}:1>"
                    msg += f"> <code>{html.escape(usage)}</code>\n"
                    async with session.get(
                        f"/file=models/Lora/{lora['name']}.civitai.info"
                    ) as cai_r:
                        if cai_r.status == 200:
                            # content_type=None is needed to disable check for application/json
                            cai_info = await cai_r.json(content_type=None)
                            msg += f"> Trigger words: "
                            for trained_word in cai_info["trainedWords"]:
                                msg += f"<code>{html.escape(trained_word)}</code> "
                            msg += "\n"
                        else:
                            msg += "> Failed to fetch trigger words\n"
                    msg += "\n"
                await update.message.reply_text(
                    "Installed loras:\n\n" + msg, parse_mode="HTML"
                )
            else:
                raise sd_api.SDError((await response.json())["errors"])


GENERAL_UPSCALE_CONFIG = {
    "upscaler_1": "R-ESRGAN 4x+ Anime6B",
    "upscaling_resize": 2,
    "resize_mode": 0,
}


async def upscale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    cmd = update.message.caption or update.message.text
    if cmd is None:
        return
    if not cmd.startswith("/upscale"):
        return
    if not (update.message.photo or update.message.document):
        await update.message.reply_text("You need to upload a photo or a document")
        return
    if update.message.document:
        attachment = update.message.document
    elif update.message.photo:
        attachment = update.message.photo[-1]
    else:
        raise ValueError("how")
    attachment = await attachment.get_file()
    buf = await attachment.download_as_bytearray()
    upl = base64.b64encode(buf).decode()
    async with await sd_api.get_session(error_on_queue=True) as session:
        await update.message.reply_chat_action("upload_document")
        async with session.post(
            "/sdapi/v1/extra-single-image",
            json=dict(image=upl, **GENERAL_UPSCALE_CONFIG),
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.debug(data["html_info"])
                image = io.BytesIO(base64.b64decode(data["image"]))
                image.seek(0)
                await update.message.reply_document(
                    document=image,
                    caption=bleach.clean(
                        data["html_info"],
                        tags={"a", "b", "i", "code"},
                        protocols={"http", "https"},
                        strip=True,
                        strip_comments=True,
                    ),
                    filename="upscaled.png",
                    parse_mode="HTML",
                )
            else:
                raise sd_api.SDError((await response.text()))
