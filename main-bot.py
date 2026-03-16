import os
import discord
from aiohttp import web
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PORT = int(os.getenv('PORT', 3000))

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


async def handle_webhook(request):
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"error": "JSON inválido"}, status=400)

    event_type = payload.get('event_type')
    discord_id = payload.get('discord_id')
    data = payload.get('data', {})

    if not discord_id or not event_type:
        return web.json_response({"error": "Faltando discord_id ou event_type"}, status=400)

    try:

        user = await client.fetch_user(int(discord_id))
        
        if not user:
            return web.json_response({"error": "Usuário não encontrado"}, status=404)

        try:
            timestamp = datetime.fromisoformat(payload.get('timestamp').replace('Z', '+00:00'))
        except:
            timestamp = discord.utils.utcnow()

        embed = discord.Embed(
            color=discord.Color.from_rgb(220, 38, 38),
            timestamp=timestamp
        )
        embed.set_footer(text='Central de Comando - 4° GB', icon_url=client.user.display_avatar.url)

        if event_type == 'BATE_PONTO':
            embed.title = '⏱️ Turno Finalizado com Sucesso'
            embed.description = 'Olá, seu registro de ponto foi salvo no sistema.'
            embed.add_field(name='Viatura', value=f"`{data.get('vehicle_prefix', 'N/A')}`", inline=True)
            embed.add_field(name='Duração do Turno', value=f"`{data.get('duration_formatted', 'N/A')}`", inline=True)
            
        elif event_type == 'RSO':
            embed.title = '📋 Relatório de Serviço (RSO) Recebido'
            embed.description = 'Seu relatório operacional foi enviado para aprovação do Comando.'
            embed.add_field(name='Unidade/Prefixo', value=f"`{data.get('unit_prefix', 'N/A')}`", inline=True)
            embed.add_field(name='Total de Ações', value=f"`{data.get('total_actions', 0)}`", inline=True)
            embed.add_field(name='Resgates', value=str(data.get('rescues', 0)), inline=True)
            embed.add_field(name='Acidentes', value=str(data.get('traffic_accidents', 0)), inline=True)
            
            apoios_simulados = int(data.get('public_agency_support', 0)) + int(data.get('simulations_trainings', 0))
            embed.add_field(name='Apoios/Simulados', value=str(apoios_simulados), inline=True)
            
        else:
            return web.json_response({"error": "event_type desconhecido"}, status=400)

        await user.send(embed=embed)
        print(f"DM enviada para {user.name} ({event_type})")
        return web.json_response({"success": True, "message": "DM enviada com sucesso."})

    except discord.Forbidden:
        print(f"DMs fechadas para o ID {discord_id}")
        return web.json_response({"error": "O usuário está com as DMs fechadas"}, status=403)
    except Exception as e:
        print(f"Falha interna: {e}")
        return web.json_response({"error": "Erro interno no bot"}, status=500)


@client.event
async def on_ready():
    print(f'🚒 Bot Operacional logado como {client.user}')
    app = web.Application(middlewares=[cors_middleware])
    

    app.router.add_post('/webhook', handle_webhook)
    app.router.add_options('/webhook', handle_webhook) 
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print(f'🌐 Servidor Webhook escutando na porta {PORT}')

# Liga o Bot
if __name__ == '__main__':
    client.run(TOKEN)