import logging

from telegram import Update, Bot, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import settings as settings

import sd_commands, sd_api

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def com_setup(app: Application):
    await app.bot.set_my_commands(
        [
            BotCommand("prompt", description="Generate a prompt"),
            BotCommand("loras", description="List installed loras"),
            BotCommand("upscale", description="Upscale image"),
        ]
    )
    return


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)
    if not (update and update.message):
        return
    if isinstance(context.error, sd_api.SDError):
        await update.message.reply_text(
            f"Stable diffusion error: {context.error}",
        )
    else:
        await update.message.reply_text(
            "Unexpected error.",
        )


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(settings.TG_BOT_API_TOKEN).build()

    # on different commands - answer in Telegram
    chat_whitelist = filters.ALL
    if settings.CHAT_WHITELIST is not None:
        chat_whitelist = filters.Chat([int(settings.CHAT_WHITELIST)])
    logger.info("Chat whitelist: %s", chat_whitelist)
    application.add_handler(
        CommandHandler("prompt", sd_commands.prompt, filters=chat_whitelist)
    )
    application.add_handler(
        CommandHandler("loras", sd_commands.list_loras, filters=chat_whitelist)
    )
    application.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION) & chat_whitelist,
            sd_commands.upscale,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & chat_whitelist, sd_commands.rand_print
        )
    )

    application.add_error_handler(error_handler)  # type: ignore

    application.post_init = com_setup

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=[Update.MESSAGE], drop_pending_updates=True)


if __name__ == "__main__":
    main()
