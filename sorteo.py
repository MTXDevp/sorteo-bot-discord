import asyncio
import discord
import random
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

# Definir los intents necesarios
intents = discord.Intents.default()
intents.members = True  # Habilitar la intención de miembros
intents.presences = True  # Habilitar la intención de presencia
intents.message_content = True  # Permitir que el bot lea el contenido de los mensajes


# prefijo y los intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Ruta del archivo JSON para almacenar participaciones
participaciones_file = 'participaciones.json'

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener el token de la variable de entorno
TOKEN = os.getenv('DISCORD_TOKEN')

# Cargar participaciones desde un archivo JSON, si existe
if os.path.exists(participaciones_file):
    with open(participaciones_file, 'r') as f:
        participaciones = json.load(f)
else:
    participaciones = {}

# Manejo de errores general
async def send_error_message(ctx, message):
    await ctx.send(f"❌ {message}")

# Comando para que los administradores inscriban a un usuario en el sorteo
@bot.command(name="registrar")
@commands.has_permissions(administrator=True)  # Solo permite a administradores
async def participar(ctx, display_name: str = None, num_participaciones: int = None):
    if display_name is None:
        await send_error_message(ctx, "Faltó introducir el nombre del usuario.")
        return
    if num_participaciones is None:
        await send_error_message(ctx, "Faltan las participaciones. Por favor, proporciona el número de participaciones.")
        return

    try:
        usuario = None

        # Buscar al usuario por display_name en el servidor (sin importar mayúsculas)
        for member in ctx.guild.members:
            if member.display_name.lower() == display_name.lower():  # Comparar sin importar mayúsculas
                usuario = str(member.id)
                break

        if usuario is None:
            await send_error_message(ctx, f"No se encontró un usuario con el nombre '{display_name}' en el servidor.")
            return

        # Verificar si el número de participaciones es válido
        if num_participaciones <= 0:
            await send_error_message(ctx, "El número de participaciones debe ser mayor a 0.")
            return

        # Registrar o actualizar el número de participaciones del usuario
        participaciones[usuario] = participaciones.get(usuario, 0) + num_participaciones

        # Guardar participaciones en el archivo JSON
        with open(participaciones_file, 'w') as f:
            json.dump(participaciones, f)

        await ctx.send(f"{display_name} se ha inscrito con {num_participaciones} participaciones. ¡Buena suerte!")

    except Exception as e:
        await send_error_message(ctx, f"Ocurrió un error inesperado: {str(e)}")

# Comando para eliminar participaciones, solo para administradores
@bot.command(name="eliminar")
@commands.has_permissions(administrator=True)  # Solo permite a administradores
async def eliminar(ctx, display_name: str = None, num_participaciones: int = None):
    if display_name is None:
        await send_error_message(ctx, "Faltó introducir el nombre del usuario.")
        return
    if num_participaciones is None:
        await send_error_message(ctx, "Faltan las participaciones. Por favor, proporciona el número de participaciones a eliminar.")
        return

    try:
        usuario = None

        # Buscar al usuario por display_name en el servidor
        for member in ctx.guild.members:
            if member.display_name.lower() == display_name.lower():
                usuario = str(member.id)
                break

        if usuario is None:
            await send_error_message(ctx, f"No se encontró un usuario con el nombre '{display_name}' en el servidor.")
            return

        # Verificar si el número de participaciones es válido
        if num_participaciones <= 0:
            await send_error_message(ctx, "El número de participaciones a eliminar debe ser mayor a 0.")
            return

        # Verificar si el usuario tiene suficientes participaciones
        if usuario not in participaciones or participaciones[usuario] < num_participaciones:
            await send_error_message(ctx, "El usuario no tiene suficientes participaciones para eliminar.")
            return

        # Actualizar el número de participaciones del usuario
        participaciones[usuario] -= num_participaciones

        # Si el usuario ya no tiene participaciones, eliminar su registro
        if participaciones[usuario] == 0:
            del participaciones[usuario]

        # Guardar participaciones en el archivo JSON
        with open(participaciones_file, 'w') as f:
            json.dump(participaciones, f)

        await ctx.send(f"{display_name} ha eliminado {num_participaciones} participaciones.")

    except Exception as e:
        await send_error_message(ctx, f"Ocurrió un error inesperado: {str(e)}")

@bot.command(name="sorteo")
@commands.has_permissions(administrator=True)  # Solo permite a administradores
async def sorteo(ctx):
    try:
        # Buscar el canal de voz llamado "Sorteo" o "sorteo"
        canal_voz = discord.utils.get(ctx.guild.voice_channels, name="Sorteo") or discord.utils.get(ctx.guild.voice_channels, name="sorteo")
        
        if canal_voz is None:
            await send_error_message(ctx, "❌ No se encontró un canal de voz llamado 'Sorteo' o 'sorteo'.")
            return  # Salir si el canal no existe

        # Obtener los miembros en el canal de voz especificado
        miembros_canal = canal_voz.members
        if not miembros_canal:
            await send_error_message(ctx, "No hay participantes en el canal de voz.")
            return

        # Verificar si todos los miembros del canal de voz están en la lista de participaciones
        for miembro in miembros_canal:
            if str(miembro.id) not in participaciones:
                await send_error_message(ctx, f"El usuario **{miembro.display_name}** no está registrado en la lista de participantes.")

                # Mostrar la lista actual de participaciones en formato de lista
                lista_actual = "\n".join(
                    [f"• {(await bot.fetch_user(uid)).display_name}: {num_participaciones}" for uid, num_participaciones in participaciones.items()]
                ) or "No hay participantes registrados."
                await ctx.send(f"📋 Lista actual de participantes:\n{lista_actual}")

                return  # No iniciar el sorteo

        # Crear una lista filtrada de participantes que están en el canal de voz
        lista_filtrada = []
        for usuario_id, num_participaciones in participaciones.items():
            if str(usuario_id) in [str(miembro.id) for miembro in miembros_canal]:
                lista_filtrada.extend([usuario_id] * num_participaciones)

        # Mensaje de inicio del sorteo
        mensaje = await ctx.send("🎉 ¡Comenzando el sorteo! 🎉\n🌀 Preparándose para girar la ruleta...")

        # Simulación de la ruleta mostrando nombres
        for _ in range(20):  # Girar 20 veces
            nombre_actual = random.choice(lista_filtrada)
            usuario_actual = await bot.fetch_user(nombre_actual)
            nombre_resaltado = f"**{usuario_actual.display_name}**"
            nombres_listados = "\n".join(
                [f"• {(await bot.fetch_user(uid)).display_name}" if uid != nombre_actual else nombre_resaltado for uid in lista_filtrada]
            )
            mensaje_final = f"🎉 ¡Comenzando el sorteo! 🎉\n{nombres_listados}\n\n 🌀¡Girando! {nombre_resaltado}!"
            await mensaje.edit(content=mensaje_final)
            await asyncio.sleep(0.5)  # Espera un poco más entre nombres

        # Elegir un ganador al azar de la lista filtrada
        ganador_id = random.choice(lista_filtrada)
        ganador = await bot.fetch_user(ganador_id)

        # Anunciar el ganador
        await mensaje.edit(content=f"🎉 ¡El ganador del sorteo es **{ganador.display_name}**! 🎉")

        # Eliminar al ganador de participaciones
        if ganador_id in participaciones:
            del participaciones[ganador_id]  # Eliminar al ganador de la lista de participaciones
            await ctx.send(f"🗑️ Se ha eliminado al usuario **{ganador.display_name}** de la lista ponderada.")
            save_participaciones(participaciones)  # Guardar cambios en el archivo JSON

        # Mostrar la lista ponderada tras la eliminación con el número de participaciones
        lista_ponderada_actualizada = [(uid, num_participaciones) for uid, num_participaciones in participaciones.items()]
        lista_mostrar = "\n".join(
            [f"• {(await bot.fetch_user(uid)).display_name}: {num_participaciones}" for uid, num_participaciones in lista_ponderada_actualizada]
        ) or "No quedan participantes."

        await ctx.send(f"📋 Participaciones actualizadas:\n{lista_mostrar}")

    except discord.HTTPException as e:
        await send_error_message(ctx, f"Ocurrió un error con la API de Discord: {str(e)}")
    except Exception as e:
        await send_error_message(ctx, f"Ocurrió un error inesperado: {str(e)}")


# Guardar participaciones en un archivo JSON
def save_participaciones(participaciones):
    with open('participaciones.json', 'w') as f:
        json.dump(participaciones, f)

# Comando para eliminar todas las participaciones, solo para administradores
@bot.command(name="sorteo_eliminar")
@commands.has_permissions(administrator=True)  # Solo permite a administradores
async def sorteo_elimninar(ctx):
    try:
        participaciones.clear()  # Limpiar el diccionario en memoria

        # Eliminar el archivo JSON de participaciones
        if os.path.exists(participaciones_file):
            os.remove(participaciones_file)

        await ctx.send("✅ Todas las participaciones han sido eliminadas.")

    except Exception as e:
        await send_error_message(ctx, f"Ocurrió un error inesperado: {str(e)}")

# Comando para ver las participaciones de un usuario
@bot.command(name="mis_participaciones")
async def mis_participaciones(ctx):
    try:
        usuario = str(ctx.author.id)
        num_participaciones = participaciones.get(usuario, 0)
        await ctx.send(f"Tienes {num_participaciones} participaciones en el sorteo.")

    except Exception as e:
        await send_error_message(ctx, f"Ocurrió un error inesperado: {str(e)}")

# Comando para listar todas las participaciones
@bot.command(name="participantes")
async def participantes(ctx):
    try:
        if not participaciones:
            await send_error_message(ctx, "No hay participantes registrados en el sorteo.")
            return

        # Crear un mensaje que contenga la lista de participantes y sus participaciones
        mensaje = "Participantes en el sorteo:\n"
        for usuario_id, num_participaciones in participaciones.items():
            usuario = await bot.fetch_user(usuario_id)
            mensaje += f"{usuario.display_name}: {num_participaciones} participaciones\n"  # Usar display_name

        await ctx.send(mensaje)

    except Exception as e:
        await send_error_message(ctx, f"Ocurrió un error inesperado: {str(e)}")

@bot.command(name="usuarios_activos")
@commands.has_permissions(administrator=True)  # Solo permite a administradores
async def usuarios_activos(ctx):
    try:
        miembros = ctx.guild.members

        # Mapeo de símbolos para estados
        estado_simbolos = {
            discord.Status.online: "🟢",  # Verde para online
            discord.Status.idle: "🟡",     # Amarillo para idle
            discord.Status.dnd: "🔴",      # Rojo para do not disturb
            discord.Status.offline: "⚫"    # Negro para offline (si se desea mostrar)
        }

        # Filtrar miembros activos, excluyendo bots y asignando símbolos
        usuarios_en_linea = [
            f"{estado_simbolos[member.status]} {member.display_name}" for member in miembros 
            if member.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd) and not member.bot
        ]

        if not usuarios_en_linea:
            await ctx.send("❌ No hay usuarios activos en línea.")
            return

        mensaje = "Usuarios activos en el servidor:\n" + "\n".join(usuarios_en_linea)
        await ctx.send(mensaje)

    except Exception as e:
        await ctx.send(f"Ocurrió un error inesperado: {str(e)}")



@bot.command(name="miembros")
@commands.has_permissions(administrator=True)  # Solo permite a administradores
async def miembros(ctx):
    try:
        # Obtener todos los miembros del servidor
        miembros = ctx.guild.members
        
        # Crear una lista con los nombres de los miembros
        lista_miembros = [member.display_name for member in miembros]

        if not lista_miembros:
            await ctx.send("❌ No hay miembros en el servidor.")
            return

        # Crear un mensaje con todos los nombres de los miembros
        mensaje = "Miembros en el servidor:\n" + "\n".join(lista_miembros)
        
        # Enviar el mensaje
        await ctx.send(mensaje)

    except Exception as e:
        await ctx.send(f"Ocurrió un error inesperado: {str(e)}")

#!sumar_participaciones #nombre-del-canal 
# Comando para sumar 1 participación a todos los miembros en un canal específico
@bot.command(name="generar")
@commands.has_permissions(administrator=True)  # Solo permite a administradores
async def sumar_participaciones_voz(ctx, canal: discord.VoiceChannel):
    try:
        # Iterar sobre los miembros en el canal de voz
        for member in canal.members:
            if not member.bot:  # Ignorar los bots
                usuario_id = str(member.id)
                # Sumar 1 participación
                participaciones[usuario_id] = participaciones.get(usuario_id, 0) + 1
        
        # Guardar participaciones en el archivo JSON
        with open(participaciones_file, 'w') as f:
            json.dump(participaciones, f)
        
        await ctx.send(f"Se ha sumado 1 participación a todos los miembros en el canal de voz '{canal.name}'.")
        
    except Exception as e:
        await send_error_message(ctx, f"Ocurrió un error inesperado: {str(e)}")

    
# Evento para manejar errores en los comandos
@bot.event
async def on_command_error(ctx, error):
    # Verifica si el error es un error de comando de tipo CommandNotFound
    if isinstance(error, commands.CommandNotFound):
        await send_error_message(ctx, "Comando no encontrado. Por favor verifica la sintaxis y el nombre del comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await send_error_message(ctx, "Faltan argumentos requeridos. Por favor proporciona todos los argumentos necesarios.")
    elif isinstance(error, commands.BadArgument):
        # Manejo de BadArgument para comandos específicos
        if ctx.invoked_with == "participar":
            await send_error_message(ctx, f"Ocurrió un error inesperado: {str(e)}")
            
bot.run(TOKEN)
