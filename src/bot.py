from telethon import TelegramClient, events, Button
from telethon.tl.types import PeerChannel
from db import init_db, get_db, User, Admin, BotConfig, Product
from config import API_ID, API_HASH, BOT_TOKEN, LOG_CHANNEL_ID, SUPER_ADMIN_ID
from messages import get_message
import logging

# Logging configuration
logging.basicConfig(
    filename='logs/bot.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# Initialize the database
init_db()

# Initialize the Telegram client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


# Start command (auto-detect role)
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id

    try:
        # Send log to the log channel
        await client.send_message(PeerChannel(int(LOG_CHANNEL_ID)), get_message("log_user_start", "fa").format(user_id=user_id))
    except Exception as e:
        logging.error(f"Failed to send log to channel. Error: {e}")

    buttons = [
        [Button.inline("English 🇬🇧"), Button.inline("فارسی 🇮🇷")],
    ]

    await event.respond("Welcome to the bot! Please select an option.👋 \nبه ربات خوش آمدید! لطفاً یک گزینه را انتخاب کنید.👋", buttons=buttons)


# Handle button clicks
@client.on(events.CallbackQuery)
async def button_click(event):
    user_id = event.sender_id
    data = event.data.decode("utf-8")  # Get the button data

    db = next(get_db())

    # Language selection
    if data == "English 🇬🇧":
        lang = "en"
    elif data == "فارسی 🇮🇷":
        lang = "fa"
    else:
        lang = "fa"

    # Check if the user is an admin
    super_admin_id = int(SUPER_ADMIN_ID)
    admin_ids = [super_admin_id] + \
        [admin.admin_id for admin in db.query(Admin).all()]

    if user_id in admin_ids:
        # Admin Panel buttons
        if data == "manage_users":
            buttons = [
                [Button.text(get_message("increase_balance", lang))],
                [Button.text(get_message("decrease_balance", lang))],
                [Button.text(get_message("ban_user", lang))],
                [Button.text(get_message("unban_user", lang))],
                [Button.text(get_message("admin_panel.title", lang))]
            ]
            await event.edit(get_message("manage_users.title", lang), buttons=buttons)

        elif data == "manage_products":
            buttons = [
                [Button.text(get_message("increase_price", lang))],
                [Button.text(get_message("decrease_price", lang))],
                [Button.text(get_message("admin_panel.title", lang))]
            ]
            await event.edit(get_message("manage_products.title", lang), buttons=buttons)

        elif data == "manage_orders":
            buttons = [
                [Button.text(get_message("complete_order", lang))],
                [Button.text(get_message("cancel_order", lang))],
                [Button.text(get_message("admin_panel.title", lang))]
            ]
            await event.edit(get_message("manage_orders.title", lang), buttons=buttons)

        elif data == "manage_admins":
            # Only the super admin can manage admins
            if user_id == SUPER_ADMIN_ID:
                buttons = [
                    [Button.text(get_message("add_admin", lang))],
                    [Button.text(get_message("remove_admin", lang))],
                    [Button.text(get_message("admin_panel.title", lang))]
                ]
                await event.edit(get_message("manage_admins.title", lang), buttons=buttons)
            else:
                await event.respond(get_message("errors.permission_denied", lang))

        elif data == "toggle_bot":
            # Toggle bot status (enabled/disabled)
            config = db.query(BotConfig).first()
            if config:
                config.bot_disabled = not config.bot_disabled
            else:
                config = BotConfig(bot_disabled=True)
                db.add(config)
            db.commit()

            status = "disabled" if config.bot_disabled else "enabled"
            await event.edit(get_message("bot_status.toggle_message", lang).format(status=status))
        else:
            # Show Admin Panel
            buttons = [
                [Button.text(get_message("admin_panel.manage_users", lang))],
                [Button.text(get_message("admin_panel.manage_products", lang))],
                [Button.text(get_message("admin_panel.manage_orders", lang))],
                [Button.text(get_message("admin_panel.manage_admins", lang))],
                [Button.text(get_message("admin_panel.toggle_bot", lang))]
            ]
            await event.respond(get_message("admin_panel.title", lang), buttons=buttons)
    else:
        # User Panel buttons
        if data == "view_products":
            products = db.query(Product).all()
            if not products:
                await event.respond(get_message("errors.product_not_found", lang))
                return

            # Show products as buttons
            buttons = []
            for product in products:
                buttons.append(
                    [Button.text(f"{product.name} - {product.price}")])

            buttons.append(
                [Button.text(get_message("user_panel.title", lang))])
            await event.edit(get_message("products", lang), buttons=buttons)

        elif data == "check_balance":
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                await event.respond(get_message("errors.user_not_found", lang))
                return

            await event.edit(get_message("balance_check", lang).format(balance=user.balance))

        elif data == "place_order":
            # Place order logic
            await event.edit(get_message("order_confirmation", lang))

        elif data == "support":
            await event.edit(get_message("support.message", lang))

        elif data == "rules":
            await event.edit(get_message("rules.message", lang))
        else:
            # Show User Panel
            buttons = [
                [Button.text(get_message("user_panel.view_products", lang))],
                [Button.text(get_message("user_panel.check_balance", lang))],
                [Button.text(get_message("user_panel.order_product", lang))],
                [Button.text(get_message("support", lang))],
                [Button.text(get_message("rules", lang))]
            ]
            await event.respond(get_message("user_panel.title", lang), buttons=buttons)

# Run the bot
client.run_until_disconnected()
