import interactions
from interactions import *
from random import shuffle
import sqlite3

TOKEN = "MTEyMjkxNDQ5OTc4ODI3NTg0Mg.GvC0NY.8QRxCOWiUBVJFbNEjFEVNEL9FVaSHj01VDfcMA"

bot = interactions.Client(token=TOKEN)

simbol = '\n'
cards = [6, 7, 8, 9, 10, 2, 3, 4, 11] * 4
shuffle(cards)
gameStart = False
global countPoint
countPoint = 0
playing_user = 0

yesButton = Button(style=ButtonStyle.PRIMARY, label="Да", custom_id="yep_21")
noButton = Button(style=ButtonStyle.DANGER, label="Нет", custom_id="nope_21")


@listen()
async def on_startup():
    print(f'{bot.user} активирован')
    for guild in bot.guilds:
        print(
            f'{bot.user} подключен к чату:\n'
            f'{guild.name} (id: {guild.id})'
        )

@component_callback("yep_21")
async def yep_21_callback(ctx: ComponentContext):
    global countPoint
    global gameStart
    if not gameStart:
        return await ctx.send(f'Игра не начата!{simbol}Начните игру командой /start_21')
    if ctx.author_id != playing_user:
        return await ctx.send('Сейчас играете не вы!')
    current = cards.pop()
    countPoint += current
    user_id = ctx.author_id
    if countPoint > 21:
        await ctx.send(f'Сожалею, но вы проиграли{simbol}Ваш счет: {countPoint} очков')
        await save_result(user_id, countPoint, False)
        countPoint = 0
        gameStart = False
        return
    elif countPoint == 21:
        await ctx.send('Поздравляю, вы набрали 21 очко!')
        await save_result(user_id, countPoint, True)
        countPoint = 0
        gameStart = False
        return
    await ctx.send(f'Вам выпала карта номиналом {current}{simbol}Желаете взять еще карту?', components=[yesButton, noButton])

@component_callback('nope_21')
async def nope_21_callback(ctx: ComponentContext):
    global gameStart
    global countPoint
    if not gameStart:
        return await ctx.send(f'Игра не начата!{simbol}Начните игру командой /start_21')
    if ctx.author_id != playing_user:
        return await ctx.send('Сейчас играете не вы!')
    user_id = ctx.author_id
    gameStart = False
    await ctx.send(f'Вы закончили игру с {countPoint} очков')
    await save_result(user_id, countPoint, False)

    countPoint = 0

@slash_command(description='Сыграть в 21 очко')
async def start_21(ctx: SlashContext):
    global playing_user
    global countPoint
    global gameStart
    if gameStart:
        return await ctx.send('Закончите игру прежде чем начинать новую!')
    gameStart = True
    playing_user = ctx.author_id
    await ctx.send('Игра началась!')
    current = cards.pop()
    await ctx.send(f'Вам выпала карта номиналом {current}{simbol}Желаете взять еще карту?', components=[yesButton, noButton])
    countPoint += current

async def save_result(user_id: int, score: int, win: bool):
    conn = sqlite3.connect('leaderboard.db')
    cur = conn.cursor()
    if win:
        cur.execute(f"select * from leaders where id={user_id}")
        
        temp = cur.fetchall()
        if len(temp) == 0:
            cur.execute(f'insert into leaders(id, max_score, count_win) values({user_id}, {score}, 1)')
            conn.commit()
            print('Данные сохранены!')
            return

        cur.execute(f'update leaders set count_win = count_win + 1 where id = {user_id}')
        conn.commit()
    else:
        cur.execute(f"select * from leaders where id={user_id}")

        temp = cur.fetchall()
        if len(temp) == 0:
            cur.execute(f'insert into leaders(id, max_score, count_lose) values({user_id}, {score}, 1)')
            conn.commit()
            print('Данные сохранены!')
            return
        
        cur.execute(f"select * from leaders where id={user_id}")
        dbScore = cur.fetchall()[0][1]
        if score > dbScore:
            score = dbScore
        cur.execute(f'update leaders set count_lose = count_lose + 1, max_score = {score} where id = {user_id}')
        conn.commit()
    print('Данные сохранены!')

@slash_command(description='Показать таблицу лидеров')
async def leaderboard(ctx):
    conn = sqlite3.connect('leaderboard.db')
    cur = conn.cursor()

    cur.execute('select * from leaders order by count_win desc;')
    temp = cur.fetchall()
    if len(temp) < 5:
        result = temp
    else:
        cur.execute('select * from leaders order by count_win desc;')
        result = cur.fetchmany(5)
    await ctx.send(
        simbol.join([f'{i} место: {await bot.fetch_user(result[i - 1][0])} {result[i - 1][2]} побед' for i in range(1, len(result) + 1)])
    )
    

bot.start()