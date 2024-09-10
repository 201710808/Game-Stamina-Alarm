from concurrent.futures import thread
import threading
import time
from socket import *

import asyncio
import datetime
import time
import discord
from discord.ext import tasks, commands

import os
from dotenv import load_dotenv


global present_sanity
global total_sanity
global status
global sec
global clientSock

present_sanity = '-'
total_sanity = '-'
status = 'Disconnected'

load_dotenv()
sec = int(os.environ.get('INTERVAL'))

def receive():
    port = int(os.environ.get('PORT'))
    serverSock = socket(AF_INET, SOCK_STREAM)
    serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSock.bind(('', port))
    serverSock.listen(1)
    print('\n%d번 포트로 접속 대기중...' % port)
    global status
    status = 'Listening'
    
    global clientSock
    clientSock, clientAddr = serverSock.accept()
    print('\n', str(clientAddr), '에서 접속되었습니다.')
    status = 'Connected'    

    while status != 'Disconnected':
        try:
            global total_sanity
            global present_sanity
            
            recvData = clientSock.recv(1024)
            if recvData.decode():
                print(f'Data received: {recvData.decode()}')
                recvData = list(map(lambda x: x.strip(), recvData.decode().split(',')))
                print(recvData)
                
                if recvData[2] == 'Detect':
                    if recvData[0].isdigit() and recvData[1].isdigit():
                        if int(recvData[0]) > 0 and int(recvData[1]) >= 0 and int(recvData[1]) <= int(recvData[0]):
                            total_sanity = int(recvData[0])
                            present_sanity = int(recvData[1])
                        print(f'Sanity detected: {present_sanity}/{total_sanity}')
                        status = recvData[2]

                    response = f'{total_sanity},{present_sanity},{status}'
                    clientSock.send(response.encode())
                    print(f'Response sent: {response}')
                
                elif recvData[2] == 'Close':
                    # clientSock.close()
                    print(f'{clientAddr} is disconnected')
                    status = recvData[2] 

        except Exception as e:
            print(f'Error: {e}')
            status = 'Disconnected'
            server_start_thread()
            break

def server_start():
    while status == 'Disconnected':
        try:
            print("Server is starting...")
            serverThread = threading.Thread(target=receive)
            serverThread.start()
                
        except Exception as e:
            print(f'Error: {e}')
        
        time.sleep(2)
        # print(f'thread is end')
    
def server_start_thread():
    server_start_thread = threading.Thread(target=server_start, daemon=True)
    server_start_thread.start()
    
server_start_thread()

########################################################################################################################

def insertSanity():
    global total_sanity
    global present_sanity
    temp = total_sanity
    if temp == '-':
        temp = input("최대 이성을 입력해주세요.: ")
    while True:
        try:
            temp = int(temp)
            break
        except:
            temp = input("최대 이성을 재입력해주세요.: ")
    total_sanity = temp

    temp = input("현재 이성을 입력해주세요.: ")
    while True:
        try:
            temp = int(temp)
            break
        except:
            temp = input("현재 이성을 재입력해주세요.: ")
    present_sanity = temp
    showPresentSanity()


def showIPaddress():
    search_ip = os.environ.get('IP_3NUM')[:-3]
    os.system(f'ifconfig|grep {search_ip}')
    input("<<Press Any Key to Continue>>\n\n\n")


def turnOffServer():
    pass


def showPresentSanity():
    global total_sanity
    global present_sanity
    try:
        try:
            present_sanity = present_sanity.replace("\n", "")
            total_sanity = total_sanity.replace("\n", "")
        except:
            pass
        print('\n\n현재 이성: ' + str(present_sanity) + '/' + str(total_sanity))
        estimated_time = (int(total_sanity) - int(present_sanity)) * 6
        print('예상 소요 시간: ' + str(estimated_time) + '분')
        _, _, _, hh, mm, _, _, _, _ = time.localtime(time.time())
        hh = int(hh + estimated_time / 60)
        mm += (estimated_time % 60)
        if mm >= 60:
            mm -= 60
            hh += 1
        if hh >= 24:
            hh -= 24
        print('완충 완료 시각: ' + str(int(hh)) + ':' + format(mm, '02'))
        input("<<Press Any Key to Continue>>\n\n\n")
    except:
        print('오류가 발생했습니다!')


def need_input():
    while True:
        select = input("\n\n원하는 동작을 선택해주세요.\n"
              "\n"
              "1. 이성 직접 입력\n"
              "2. 현재 기기 IP 확인\n"
              "3. 이성 타이머 확인하기\n")

        if select == '1':
            insertSanity()
        elif select == '2':
            showIPaddress()
        elif select == '3':
            showPresentSanity()
        else:
            print("올바른 숫자를 입력해주세요.\n\n\n")


# need_input = threading.Thread(target=need_input)
# need_input.start()


########################################################################################################################

TOKEN = os.environ.get('TOKEN')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID'))

# client = discord.Client(intents=discord.Intents.default())
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def create_embed(_total_sanity, _present_sanity, _estimated_time):
    _, _, _, hh, mm, _, _, _, _ = time.localtime(time.time())
    hh = int(hh + _estimated_time / 60)
    mm += (_estimated_time % 60)
    if mm >= 60:
        mm -= 60
        hh += 1
    if hh >= 24:
        hh -= 24
    if _estimated_time <= 60:
        embed = discord.Embed(title="🚨 1시간 이내 이성 충전 완료 예정 🚨", color=0xCC0000)
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/400214285969784833/976140408876855366/icon_16.png")
    else:
        embed = discord.Embed(title="📢 이성 충전 정보 현황 알림 📢", color=0x99FF00)
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1064878216466141235.png")
    text0 = str(_present_sanity) + '/' + str(_total_sanity)
    text0 = text0.replace("\n", "")
    embed.add_field(name="ㅤ", value="ㅤ", inline=False)
    embed.add_field(name="⚡ 현재 이성", value=text0, inline=False)
    embed.add_field(name="⏳ 예상 소요 시간", value=(str(_estimated_time)+'분'), inline=False)
    embed.add_field(name="⏰ 충전 완료 시각", value=(str(int(hh)) + ':' + format(mm, '02')), inline=False)
    embed.timestamp = datetime.datetime.now()

    embed.set_footer(text='\u200b')
    return embed

async def delete_messages(channel):
    while True:
        deleted = await channel.purge(limit=3)
        if len(deleted) == 0:
            break
        # await asyncio.sleep(1)
        
def calculate_estimated_time(total_sanity, present_sanity):
    estimated_time = (total_sanity - present_sanity) * 6
    return estimated_time

async def create_and_send_embed(channel, estimated_time):
    global total_sanity
    global present_sanity
    
    embed = create_embed(total_sanity, present_sanity, estimated_time)
    await channel.send(embed=embed)

@tasks.loop(seconds=1)
async def send_message_channel():
    global status
    global sec
    global total_sanity
    global present_sanity
    global clientSock
    
    if sec > 0:
        sec -= 1
        # print(sec)
            
        if sec == 0:
            if present_sanity != '-' and present_sanity < total_sanity:
                present_sanity += 1
                
                if status == 'Connected':
                    message = f'{total_sanity}, {present_sanity}, {status}'
                    clientSock.send(message.encode())
                    print(f'Message: {message}')
    
    try:
        # Send discord message if less than 60 min left before the sanity is full
        if present_sanity != '-' and total_sanity != '-' and (total_sanity - present_sanity) <= 10 and sec == 0:
            channel = bot.get_channel(CHANNEL_ID)
            
            await delete_messages(channel)
                
            estimated_time = calculate_estimated_time(total_sanity, present_sanity)
            await create_and_send_embed(channel, estimated_time)
        
        # Send discord message when the client sent 'Detect' message         
        elif status == 'Detect':
            channel = bot.get_channel(CHANNEL_ID)
            
            await delete_messages(channel)
                
            estimated_time = calculate_estimated_time(total_sanity, present_sanity)
            await create_and_send_embed(channel, estimated_time)
            
            status = 'Connected'
            
        # Send discord message when the client is disconnected
        elif status == 'Close':
            channel = bot.get_channel(CHANNEL_ID)
            
            await delete_messages(channel)
            
            estimated_time = calculate_estimated_time(total_sanity, present_sanity)
            await create_and_send_embed(channel, estimated_time)
            status = 'Disconnected'
            server_start_thread()

    except:
        print("failed")
        status = 'Disconnected'
        server_start_thread()        

    if sec == 0:
        sec = int(os.environ.get('INTERVAL'))
        
@bot.command()
async def a(ctx, _present_sanity: int=0, _total_sanity: int=135):
    try:
        global present_sanity
        global total_sanity
        
        channel = bot.get_channel(CHANNEL_ID)
        
        await delete_messages(channel)
        try:
            present_sanity = int(_present_sanity)
            total_sanity = int(_total_sanity)
            print(f'Sanity set from Discord: {present_sanity}/{total_sanity}')
            
            global clientSock
            global status
            
            if status == 'Connected':
                message = f'{total_sanity}, {present_sanity},'
                clientSock.send(message.encode())
                print(f'Message: {message}')
            
        except:
            await ctx.send("이성이 입력되지 않았습니다.\n[ !a (현재 이성) (전체 이성) ] 명령어를 사용해 이성을 입력해주세요.")
            return
        
        estimated_time = calculate_estimated_time(total_sanity, present_sanity)
        await create_and_send_embed(channel, estimated_time)
        
    except Exception as e:
        print(f"Command failed: {e}")

@bot.command()
async def p(ctx):
    try:
        global present_sanity
        global total_sanity
        global status
        # print(total_sanity, present_sanity, estimated_time)

        channel = bot.get_channel(CHANNEL_ID)
    
        await delete_messages(channel)
    
        if present_sanity == '-' or total_sanity == '-':
            await ctx.send("이성이 입력되지 않았습니다.\n[ !a (현재 이성) (전체 이성) ] 명령어를 사용해 이성을 입력해주세요.")
        else:
            estimated_time = calculate_estimated_time(total_sanity, present_sanity)
            await create_and_send_embed(channel, estimated_time)
            
    except Exception as e:
        print(f"Command failed: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    send_message_channel.start()
    # print("start")

bot.run(TOKEN)
