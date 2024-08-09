import discord
from discord.ext import commands, tasks
import json
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox

def smooth_print(text, delay=0.1):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def Spinner():
    l = ['|', '/', '-', '\\']
    for i in l+l+l:
        sys.stdout.write(f"\r{i}")
        sys.stdout.flush()
        time.sleep(0.1)

def input_with_typing_animation(prompt, speed):
    user_input = ""
    for char in prompt:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    user_input = input()
    return user_input

typing_speed = 0.04

Spinner()
smooth_print("/.\ Installing dependencies", 0.05)
time.sleep(0.3)
print("  /.\ Authenticating...")
time.sleep(0.5)
print("  /.\ Authenticated !")

token = input_with_typing_animation("\n  /.\ Bot Token [~]: ", typing_speed)
print(f"Token received: {token}")

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
client.remove_command('help')

AUTHORIZED_USER_IDS = [1223099425572786380, 684952723895877656]  # Replace with your Discord ID
OWNER_USER_ID = [1223099425572786380, 684952723895877656]  # Replace with your Discord ID

def is_authorized(ctx):
    return ctx.author.id in AUTHORIZED_USER_IDS

def is_owner(ctx):
    return ctx.author.id == OWNER_USER_ID

def get_save_filename(guild_id):
    save_path = r'C:\Users\proev\Desktop\Mod'
    os.makedirs(save_path, exist_ok=True)
    return os.path.join(save_path, f'server_state_{guild_id}.json')

def get_permban_filename():
    save_path = r'C:\Users\proev\Desktop\Mod'
    return os.path.join(save_path, 'permbanned_users.json')

def load_permbanned_users():
    filename = get_permban_filename()
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def save_permbanned_users(permbanned_users):
    filename = get_permban_filename()
    with open(filename, 'w') as f:
        json.dump(permbanned_users, f, indent=4)

@client.command()
async def save(ctx):
    if is_authorized(ctx):
        try:
            await ctx.message.delete()
            guild = ctx.guild
            state = {
                'roles': [
                    {
                        'id': role.id,
                        'name': role.name,
                        'permissions': role.permissions.value,
                        'color': role.color.value,
                        'hoist': role.hoist,
                        'mentionable': role.mentionable
                    }
                    for role in guild.roles if role.name != "@everyone"
                ],
                'channels': [
                    {
                        'id': channel.id,
                        'name': channel.name,
                        'type': str(channel.type),
                        'position': channel.position,
                        'topic': getattr(channel, 'topic', None),
                        'nsfw': getattr(channel, 'nsfw', False),
                        'slowmode_delay': getattr(channel, 'slowmode_delay', None),
                        'bitrate': getattr(channel, 'bitrate', None),
                        'user_limit': getattr(channel, 'user_limit', None),
                        'icon': getattr(channel, 'icon', None)
                    }
                    for channel in guild.channels
                ],
            }
            filename = get_save_filename(guild.id)
            with open(filename, 'w') as f:
                json.dump(state, f, indent=4)
            await ctx.send("Server state has been saved.")
        except Exception as e:
            print(f"Error saving server state: {e}")
            await ctx.send("An error occurred while saving the server state.")
    else:
        await ctx.send("You are not authorized to use this command.")

@client.command()
async def recover(ctx):
    if is_authorized(ctx):
        try:
            await ctx.message.delete()
            guild = ctx.guild
            filename = get_save_filename(guild.id)
            if not os.path.exists(filename):
                await ctx.send("No saved state found for this server.")
                return
            
            with open(filename, 'r') as f:
                state = json.load(f)
            
            for role in guild.roles:
                if role.name != "@everyone":
                    try:
                        await role.delete()
                    except Exception as e:
                        print(f"Error deleting role {role.name}: {e}")
                        pass
            
            for channel in guild.channels:
                try:
                    await channel.delete()
                except Exception as e:
                    print(f"Error deleting channel {channel.name}: {e}")
                    pass

            existing_roles = {role.id: role for role in guild.roles}
            for role_data in state['roles']:
                if role_data['id'] not in existing_roles:
                    try:
                        await guild.create_role(
                            name=role_data['name'],
                            permissions=discord.Permissions(role_data['permissions']),
                            color=discord.Color(role_data['color']),
                            hoist=role_data['hoist'],
                            mentionable=role_data['mentionable']
                        )
                    except Exception as e:
                        print(f"Error creating role {role_data['name']}: {e}")
                        pass
            
            for channel_data in state['channels']:
                try:
                    if channel_data['type'] == 'text':
                        await guild.create_text_channel(
                            name=channel_data['name'],
                            position=channel_data['position'],
                            topic=channel_data['topic'],
                            nsfw=channel_data['nsfw'],
                            slowmode_delay=channel_data['slowmode_delay']
                        )
                    elif channel_data['type'] == 'voice':
                        await guild.create_voice_channel(
                            name=channel_data['name'],
                            position=channel_data['position'],
                            bitrate=channel_data['bitrate'],
                            user_limit=channel_data['user_limit']
                        )
                except Exception as e:
                    print(f"Error creating channel {channel_data['name']}: {e}")
                    pass
            
            await ctx.send("Server state has been recovered.")
        except Exception as e:
            print(f"Error recovering server state: {e}")
            await ctx.send("An error occurred while recovering the server state.")
    else:
        await ctx.send("You are not authorized to use this command.")

@client.command()
async def permban(ctx, user_id: int):
    if is_authorized(ctx):
        try:
            await ctx.message.delete()
            user = ctx.guild.get_member(user_id)
            if user:
                await user.ban(reason="Permanently banned by admin.")
                permbanned_users = load_permbanned_users()
                if user_id not in permbanned_users:
                    permbanned_users.append(user_id)
                    save_permbanned_users(permbanned_users)
                await ctx.send(f"User with ID {user_id} has been permanently banned.")
            else:
                await ctx.send("User not found in this server.")
        except Exception as e:
            print(f"Error in permban command: {e}")
            await ctx.send("An error occurred while banning the user.")
    else:
        await ctx.send("You are not authorized to use this command.")

@client.command()
async def unpermban(ctx, user_id: int):
    if is_owner(ctx):
        try:
            await ctx.message.delete()
            permbanned_users = load_permbanned_users()
            if user_id in permbanned_users:
                permbanned_users.remove(user_id)
                save_permbanned_users(permbanned_users)
                for guild in client.guilds:
                    banned_users = await guild.bans()
                    if any(ban.user.id == user_id for ban in banned_users):
                        try:
                            await guild.unban(discord.Object(id=user_id))
                        except Exception as e:
                            print(f"Error unbanning user {user_id}: {e}")
                await ctx.send(f"User with ID {user_id} has been removed from the permanent ban list.")
            else:
                await ctx.send("User is not in the permanent ban list.")
        except Exception as e:
            print(f"Error in unpermban command: {e}")
            await ctx.send("An error occurred while unbanning the user.")
    else:
        await ctx.send("You are not authorized to use this command.")

@client.command()
async def delroles(ctx, *, role_name: str):
    if is_authorized(ctx):
        try:
            await ctx.message.delete()
            guild = ctx.guild
            for role in guild.roles:
                if role.name == role_name and role.name != "@everyone":
                    try:
                        await role.delete()
                    except Exception as e:
                        print(f"Error deleting role {role.name}: {e}")
                        pass
            await ctx.send(f"Roles with name '{role_name}' have been deleted.")
        except Exception as e:
            print(f"Error in delroles command: {e}")
            await ctx.send("An error occurred while deleting roles.")
    else:
        await ctx.send("You are not authorized to use this command.")

@client.command()
async def delchannels(ctx, *, channel_name: str):
    if is_authorized(ctx):
        try:
            await ctx.message.delete()
            guild = ctx.guild
            for channel in guild.channels:
                if channel.name == channel_name:
                    try:
                        await channel.delete()
                    except Exception as e:
                        print(f"Error deleting channel {channel.name}: {e}")
                        pass
            await ctx.send(f"Channels with name '{channel_name}' have been deleted.")
        except Exception as e:
            print(f"Error in delchannels command: {e}")
            await ctx.send("An error occurred while deleting channels.")
    else:
        await ctx.send("You are not authorized to use this command.")

@client.command()
async def help(ctx, *args):
    await ctx.message.delete()
    help_text = """```fix
❄️ !delroles [role name] - Deletes roles with a specific name (admin only).
❄️ !delchannels [channel name] - Deletes channels with a specific name (admin only).
❄️ !save - Saves the current state of the server (admin only).
❄️ !recover - Recovers the server state from a saved file (admin only).
❄️ !permban [user_id] - Permanently bans a user by their ID (admin only).
❄️ !unpermban [user_id] - Removes a user from the permanent ban list and attempts to unban them (owner only).
```"""
    embed = discord.Embed(color=0xfffafa, title="B_13 Mod Help ❄️")
    embed.add_field(name="Help ⚠️", value=help_text)
    embed.set_footer(text='B_13 Mod Help ⚠️')
    await ctx.send(embed=embed)

@client.event
async def on_command(ctx):
    print(f"Command '{ctx.command}' used by {ctx.author.name}#{ctx.author.discriminator}")

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} ({client.user.id})")
    await client.change_presence(activity=discord.Game(name="Managing Roles and Channels"))
    check_permbanned_users.start()

@tasks.loop(seconds=0.5)
async def check_permbanned_users():
    permbanned_users = load_permbanned_users()
    for guild in client.guilds:
        for user_id in permbanned_users:
            member = guild.get_member(user_id)
            if member and not member.bot:
                try:
                    await member.ban(reason="Permanently banned by admin.")
                except Exception as e:
                    print(f"Error banning user {user_id}: {e}")

@client.event
async def on_guild_remove(guild):
    def show_popup(user):
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("Bot Removed", f"The bot has been removed from the server: {guild.name}\nRemoved by: {user}")
        root.destroy()

    async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add):
        if entry.target.id == client.user.id:
            show_popup(entry.user.name)
            break

client.run(os.getenv('DISCORD_TOKEN'))
