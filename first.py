import asyncio
from telethon import TelegramClient, events
from datetime import datetime
import random


api_id = 23288250
api_hash = '4af3b4b4770120cb3f6266d7776a0eca'


personal_link_message = """
text me on group

https://t.me/+KMMytzOAITg5ZTU1

and


"""
group_message_text = "hello This is navya"

group_reply_text = "ADD me and Text me" 

group_individual_send_delay_min = 5
group_individual_send_delay_max = 15


group_loop_interval = 200


private_send_delay_min = 5
private_send_delay_max = 15


client = TelegramClient('session_name', api_id, api_hash)


sent_to_private_users = set()


def load_sent_private_users():
    """Loads user IDs from 'sent_users_private.txt' into the tracking set."""
    try:
        with open('sent_users_private.txt', 'r') as f:
            for line in f:
                sent_to_private_users.add(int(line.strip()))
        print(f"[{datetime.now()}] Loaded {len(sent_to_private_users)} previously sent users for private messages.")
    except FileNotFoundError:

        print(f"[{datetime.now()}] No 'sent_users_private.txt' found. Starting fresh for new private messages.")

def save_sent_private_user(user_id):
    """Saves a new user ID to 'sent_users_private.txt' to persist the sent status."""
    with open('sent_users_private.txt', 'a') as f:
        f.write(str(user_id) + '\n')
    print(f"[{datetime.now()}] Saved private user ID {user_id} to sent list.")


@client.on(events.NewMessage(incoming=True))
async def handle_new_private_message(event):
    """
    Handles new incoming private messages.
    If the message is private and hasn't been sent to before, it sends the personal link.
    """

    if not event.is_private:
        return

    sender = await event.get_sender()
    sender_id = sender.id


    if sender.is_self:
        return


    if sender_id in sent_to_private_users:
        print(f"[{datetime.now()}] Already sent private message to {sender.username or sender.first_name} (ID: {sender_id})")
        return

    try:

        random_delay = random.uniform(private_send_delay_min, private_send_delay_max)
        print(f"[{datetime.now()}] New private message from {sender.username or sender.first_name}. Waiting {random_delay:.2f}s before sending...")
        await asyncio.sleep(random_delay)


        await client.send_message(sender_id, personal_link_message)

        sent_to_private_users.add(sender_id)
        save_sent_private_user(sender_id)
        print(f"[{datetime.now()}] Sent private message to {sender.username or sender.first_name}")
    except Exception as e:
        print(f"[ERROR] Failed to send private message to {sender.username or sender.first_name} (ID: {sender_id}): {e}")


@client.on(events.NewMessage(incoming=True))
async def handle_group_replies_to_bot(event):
    """
    Handles replies to the bot's messages in groups or channels.
    If a user replies to a message sent by this bot, it replies with a predefined text.
    """

    if not (event.is_group or event.is_channel):
        return


    if event.is_reply:
        try:

            replied_msg = await event.get_reply_message()




            if replied_msg is None:
                print(f"[{datetime.now()}] Received a reply in group {event.chat.title}, but the replied-to message could not be retrieved (it might be deleted or too old). Skipping.")
                return

            me = await client.get_me() 


            if replied_msg.sender_id == me.id:
                sender = await event.get_sender()
                print(f"[{datetime.now()}] Received reply from {sender.username or sender.first_name} in group {event.chat.title} to bot's message. Replying...")
                await event.reply(group_reply_text)
                print(f"[{datetime.now()}] Sent group reply to {sender.username or sender.first_name}")
        except Exception as e:
            print(f"[ERROR] Failed to handle group reply: {e}")


async def send_messages_to_groups_in_loop():
    """
    Continuously loops through all joined groups/channels and sends a message.
    It checks for admin rights to avoid sending in groups where the user is an admin.
    """
    while True: # This loop ensures the function runs indefinitely
        print(f"\n[{datetime.now()}] Starting a new round of group message sending...")
        # Iterate through all dialogs (chats, groups, channels) the client is part of
        async for dialog in client.iter_dialogs():
            # Process only groups or channels
            if dialog.is_group or dialog.is_channel:
                try:
                    entity = await client.get_entity(dialog.id)
                    can_send = False
                    is_admin = False

                    # Check if the user has admin rights in the group/channel
                    if hasattr(entity, 'admin_rights') and entity.admin_rights:
                        # If any admin right is present, consider the user an admin
                        if (entity.admin_rights.add_admins or
                            entity.admin_rights.ban_users or
                            entity.admin_rights.change_info or
                            entity.admin_rights.delete_messages or
                            entity.admin_rights.edit_messages or
                            entity.admin_rights.invite_users or
                            entity.admin_rights.manage_call or
                            entity.admin_rights.pin_messages or
                            entity.admin_rights.post_messages):
                                is_admin = True

                    # If the user is an admin, skip this group/channel
                    if is_admin:
                        print(f"[{datetime.now()}] Skipping group/channel {dialog.name} - User is admin.")
                        continue

                    # Handle channels specifically (broadcast entities)
                    if hasattr(entity, 'broadcast') and entity.broadcast:
                        # For channels, check if the user has permission to post messages
                        if hasattr(entity, 'admin_rights') and entity.admin_rights and entity.admin_rights.post_messages:
                            can_send = True
                        else:
                            print(f"[{datetime.now()}] Skipping channel {dialog.name} - No post permission.")
                    else:
                        # For regular groups, assume sending is allowed if not an admin
                        can_send = True

                    # If allowed to send, proceed with sending the message
                    if can_send:
                        # Introduce a random delay before sending to each group
                        random_delay = random.uniform(group_individual_send_delay_min, group_individual_send_delay_max)
                        print(f"[{datetime.now()}] Sending to {dialog.name} in {random_delay:.2f}s...")
                        await asyncio.sleep(random_delay)
                        await client.send_message(dialog.id, group_message_text)
                        print(f"[{datetime.now()}] Sent message to {dialog.name}")

                except Exception as e:
                    print(f"[ERROR] Could not send to {dialog.name}: {e}")

        # After iterating through all groups, wait for the specified interval before starting a new round
        print(f"[{datetime.now()}] Finished group round. Waiting {group_loop_interval}s...")
        await asyncio.sleep(group_loop_interval)

# --- Main function ---
async def main():
    """
    The main asynchronous function to start the bot.
    It loads previously sent private users, starts the Telegram client,
    and then concurrently runs the group message sending loop and keeps the client connected.
    """
    load_sent_private_users() # Load data at startup
    await client.start() # Connect to Telegram
    print("\u2705 Userbot is running and logged in.")


    await asyncio.gather(
        send_messages_to_groups_in_loop(),
        client.run_until_disconnected() # Keeps the client connected and listens for events
    )

# --- Run bot ---
if __name__ == '__main__':
    """
    Entry point of the script.
    It runs the main asynchronous function and handles keyboard interrupts (Ctrl+C)
    for graceful shutdown.
    """
    try:
        # Run the main function until it completes (which is never, as it runs indefinitely)
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        # Handle manual interruption (Ctrl+C)
        print("\nBot stopped by user.")
    except Exception as e:
        # Catch any other unhandled exceptions
        print(f"Unhandled error: {e}")
    finally:
        # Ensure the client disconnects gracefully if it's still connected
        if client.is_connected():
            client.loop.run_until_complete(client.disconnect())
            print("Client disconnected.")
