import asyncio
from commands.s3_commands import upload_channel, upload_guild_to_s3


async def run_dotnet_channel_and_upload(api_token, chan_id, folder_name, key):
    # Define the directory path
    dotnet_dir = "/Users/chiragrastogi/Dev/Moment_app/Where2Be-Server/src/worker/scraper/DiscordChatExporter.Cli"

    # Run the dotnet command
    dotnet_cmd = [
        'dotnet', 'DiscordChatExporter.Cli.dll', 'export',
        '-t', api_token, '-c', chan_id,
        '-f', 'Json',
        '-o', f"/Users/chiragrastogi/Dev/Moment_app/Where2Be-Server/src/worker/scraper/{folder_name}"
    ]

    process = await asyncio.create_subprocess_exec(*dotnet_cmd, cwd=dotnet_dir)
    await process.communicate()

    await asyncio.run(upload_channel(key))

async def run_dotnet_guild_and_upload(api_token, guild_id, folder_name):
    # Define the directory path
    dotnet_dir = "/Users/chiragrastogi/Dev/Moment_app/Where2Be-Server/src/worker/scraper/DiscordChatExporter.Cli"

    # Run the dotnet command
    dotnet_cmd = [
        'dotnet', 'DiscordChatExporter.Cli.dll', 'exportguild',
        '-t', api_token, '-g', guild_id,
        '-f', 'Json',
        '-o', f"/Users/chiragrastogi/Dev/Moment_app/Where2Be-Server/src/worker/scraper/buffers/{folder_name}"
    ]

    process = await asyncio.create_subprocess_exec(*dotnet_cmd, cwd=dotnet_dir)
    await process.communicate()

    await upload_guild_to_s3(
        "/Users/chiragrastogi/Dev/Moment_app/Where2Be-Server/src/worker/scraper/buffers/data_UCB/")
