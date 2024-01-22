import threading
import time
from socket import *

import asyncio
import datetime
import time
import discord
from discord.ext import tasks

import os


global present_sanity
global total_sanity
global status
global sec

present_sanity = '-'
total_sanity = '-'
status = 'waiting...'


def receive():
    port = 8080

    serverSock = socket(AF_INET, SOCK_STREAM)
    serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSock.bind(('', port))
    serverSock.listen(1)

    print('\n%d번 포트로 접속 대기중...' % port)

    sock, addr = serverSock.accept()
    print('\n', str(addr), '에서 접속되었습니다.')

    global status
    while True:
        if status == 'waiting...' or status == 'Detect':
            global total_sanity
            global present_sanity
            recvData = sock.recv(1024)
            if recvData.decode():
                recvData = (recvData.decode()).split(',')
                total_sanity = recvData[0]
                present_sanity = recvData[1]
                status = recvData[2]
                if status != 'Bye':
                    status = 'Off'
        elif status == 'Off':
            try:
                print('\n%d번 포트로 접속 대기중...' % port)

                sock, addr = serverSock.accept()
                print('\n', str(addr), '에서 접속되었습니다.')
                status = 'waiting...'
            except:
                print("\nError: Address already in use!")


while True:
    try:
        receiver = threading.Thread(target=receive)
        receiver.start()
        break
    except:
        print("Error: Address already in use!")


########################################################################################################################

def timer():
    while True:
        global sec
        sec = 360
        while sec != 0:
            sec -= 1
            time.sleep(1)
        global total_sanity
        global present_sanity
        if present_sanity != '-' and int(present_sanity) != int(total_sanity):
            present_sanity = int(present_sanity) + 1


timer = threading.Thread(target=timer)
timer.start()


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
    os.system('ifconfig|grep [[INPUT YOUR 6 IP NUMBERS(ex: xxx.xxx.123.456)]]')
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


need_input = threading.Thread(target=need_input)
need_input.start()


########################################################################################################################

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
TOKEN = '[[INPUT YOUR DISCORD TOKEN]]'
CHANNEL_ID = int('[[INPUT YOUR DISCORD CHANNEL ID]]')

client = discord.Client(intents=discord.Intents.default())


@tasks.loop(seconds=1)
async def loop():
    global status
    global sec

    try:
        if present_sanity != '-' and (int(total_sanity) - int(present_sanity)) <= 10 and status != 'Bye' and sec == 0:
            estimated_time = (int(total_sanity) - int(present_sanity)) * 6
            channel = client.get_channel(CHANNEL_ID)
            _, _, _, hh, mm, _, _, _, _ = time.localtime(time.time())
            hh = int(hh + estimated_time / 60)
            mm += (estimated_time % 60)
            if mm >= 60:
                mm -= 60
                hh += 1
            if hh >= 24:
                hh -= 24
            embed = discord.Embed(title="🚨 1시간 이내 이성 충전 완료 예정 🚨", color=0xCC0000)
            embed.set_thumbnail(url="[[INPUT URL OF IMAGE]]")
            text0 = str(present_sanity) + '/' + str(total_sanity)
            text0 = text0.replace("\n", "")
            embed.add_field(name="ㅤ", value="ㅤ", inline=False)
            embed.add_field(name="⚡ 현재 이성", value=text0, inline=False)
            embed.add_field(name="⏳ 예상 소요 시간", value=(str(estimated_time)+'분'), inline=False)
            embed.add_field(name="⏰ 충전 완료 시각", value=(str(int(hh)) + ':' + format(mm, '02')), inline=False)
            embed.timestamp = datetime.datetime.now()
            embed.set_footer(text='\u200b')
            await channel.send(embed=embed)
    except:
        print("failed")


@client.event
async def on_ready():
    loop.start()

client.run(TOKEN)
