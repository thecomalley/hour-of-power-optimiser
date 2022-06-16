import os

from discord_webhook import DiscordWebhook, DiscordEmbed


def notfiy_discord(yesterday, peak_hop, kwh):
    discord_webhook_url = os.environ["DISCORD_WEBHOOK_URL"]

    webhook = DiscordWebhook(url=discord_webhook_url, username="az-hop")

    embed = DiscordEmbed(title=f'Hour of Power set: {kwh}kwh @ {peak_hop}', color='03b2f8')
    embed.set_timestamp()
    embed.add_embed_field(name='Time', value=peak_hop, inline=False)

    embed.add_embed_field(name='Previous', value=yesterday['date'])
    embed.add_embed_field(name='usage_best', value=yesterday['usage_best'])
    embed.add_embed_field(name='hour_best', value=yesterday['hour_best'])
    embed.add_embed_field(name='usage_actual', value=yesterday['usage_actual'])
    embed.add_embed_field(name='savings_actual', value=yesterday['savings_actual'])
    embed.add_embed_field(name='savings_best', value=yesterday['savings_best'])

    webhook.add_embed(embed)
    response = webhook.execute()