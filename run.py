#-*- coding:utf-8 -*-
import asyncio
import discord
import os
import traceback
import random
import time
import re

client = discord.Client()

token = "NzUxMDg4NzE3NDg1MDQ3OTAw.X1D_4A.jhc_LDnilwBqjYDttmGLhN3Bvks"
gamedata = {}
userdata = dict()
bot = None

#---------------------------------------------------------------------------------------------

#등록
async def getData(author, ch):
    with open("./mafia.txt",'r') as f:
        userdata = eval(f.read())

    if author.id not in userdata:
        embed = discord.Embed(
            title="등록 절차 진행",
            description="마피아봇 이용을 위해서는 최초 1회에 한해 등록이 필요합니다. 자세한 것은 [약관](http://www.naver.com)을 참고하세요.",
            color=0x22aa00
        )
        em = await ch.send(embed=embed)
        await em.add_reaction("✅")

        def check(reaction, user):
            return author == user and reaction.emoji == "✅"
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=30, check=check)
        except asyncio.TimeoutError:
            try:
                await em.clear_reactions()
            except:
                pass
            await ch.send("시간이 만료되었습니다.")
            return False
        else:
            try:
                await em.clear_reactions()
            except:
                pass
            
            userdata[author.id]={'mafia_win':0, 'citizen_win':0, 'mafia_winper':0, 'citizen_winper':0, 'totalgame':0, 'total_winper':0, 'point':0, 'ban':0}

            with open("./mafia.txt", 'w') as f: #save data
                f.write(str(userdata))
            await ch.send("등록이 완료되었습니다! 이제 서비스 이용이 가능합니다.")
            print("신규 유저 등록 |", author, "(", author.id, ")")
            return userdata
    else:
        return userdata

#---------------------------------------------------------------------------------------------

async def game_attend(ch, author, adminid, gamedata):
    #게임 참가
    adminid = int(adminid)
    
    if gamedata[adminid]['onoff']:
        if author not in gamedata[adminid]['member']:
            if len(gamedata[adminid]['member']) <= 8: #정원 준수
                gamedata[adminid]['member'].append(author)
                if adminid != author.id:
                    await ch.send("<@"+str(author.id)+"> 님이 게임에 참가하셨습니다.")
                    print("게임 참여 | ", author.id, "| 방 번호 : ", adminid)
            else:
                await ch.send("<@"+str(author.id)+"> 방이 꽉 찼습니다.")
        else:
            await ch.send("<@"+str(author.id)+"> 이미 참가한 방입니다.")
    else:
        await ch.send("<@"+str(author.id)+"> 게임을 찾을 수 없습니다.")
    
    return gamedata

#---------------------------------------------------------------------------------------------

async def make_gameroom(ch, guild, author, gamedata):
    #채널생성, 기본 권한 설정
    print("게임 생성중... | 방장 : ", author, "(", author.id, ")")
    
    notice_msg = ""
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        bot: discord.PermissionOverwrite(read_messages=True, send_messages=True, create_instant_invite=False, manage_permissions=True, manage_channels=True)
    }
    gch = await guild.create_text_channel(author.name+'의 마피아', overwrites=overwrites)
    try: # 채널 생성
        for user in gamedata[author.id]['member']:
            notice_msg += user.mention + " "
            await gch.set_permissions(user, read_messages=True, send_messages=True, create_instant_invite=False)
        print("게임 생성 완료 | 방장 : ", author, "(", author.id, ")")
        await gch.send(notice_msg)

    except Exception as e: #error
        print("게임 생성 실패|", e, " | 방장 : ", author, "(", author.id, ")")
        await ch.send("채널 관리 또는 채널 생성 권한이 없습니다. 서버 관리자에게 문의해주세요.")
        await endgame(gch, gamedata, author, guild)

    return gch

#---------------------------------------------------------------------------------------------

async def draw_jobs(gch, gamedata, author, guild):
    #직업 추첨/DM전송
    smg = await gch.send("직업 추첨을 시작합니다.")
    print("직업 추첨 시작 | 인원 : ", len(gamedata[author.id]['member']),"명 | 방장 : ", author, "(", author.id, ")")
    job_list = [[], [], [], [], []]
    job_msg = []

    if len(gamedata[author.id]['member']) < 0 or len(gamedata[author.id]['member']) > 8: #인원 미달/초과 / 5, 8
        await gch.send("게임에 필요한 최소 인원(5인)에 미달되거나 최대 인원(8인)을 초과하여 게임을 종료합니다.")
        print("최소 인원 미달 | 인원 : ", len(gamedata[author.id]['member']), " | 방장 : ", author, "(", author.id, ")")
        await endgame(gch, gamedata, author, guild)
        return None
    else:

        with open("./jobmsg.txt",'r') as f:
            job_msg = eval(f.read())
        job_list[0] = ["mafia1", "citizen1", "citizen2", "citizen3", "citizen4"] 
        job_list[1] = ["mafia1", "mafia2", "citizen1", "citizen2", "citizen3", "police"]
        job_list[2] = ["mafia1", "mafia2", "citizen1", "citizen2", "citizen3", "citizen4", "police"]
        job_list[3] = ["mafia1", "mafia2", "doctor", "police", "citizen1", "citizen2", "citizen3", "citizen4"]
        
        job = random.sample(gamedata[author.id]['member'], len(gamedata[author.id]['member'])) #추첨

        j=0
        k = int(len(gamedata[author.id]['member'])) - 5
        try:
            try:
                for i in job_list[len(gamedata[author.id]['member'])]:
                    gamedata[author.id][i] = job[j] # 직업 할당
                    user = gamedata[author.id][i]
                    await user.send(str(job_msg[k][j]))
                    j += 1
                    if i == "mafia1" or i == "mafia2":
                        gamedata[author.id]['live_mafia'].append(user)
                    else:
                        gamedata[author.id]['live_citizen'].append(user) 
            except Exception as e:
                await gch.send("오류: " + user.mention + "님, 디스코드 설정에서 DM 수신 거부를 확인해주세요.\n``(개인정보 보호 및 보안 → 서버 맴버가 보내는 개인 메세지 허용하기)``")
                print("DM전송 오류 | ", e, " | 거부자 : ", user.id)
                await endgame(gch, gamedata, author, guild)
                return None
            await smg.edit(content="직업 추첨을 시작합니다...완료")
            return gamedata
        except Exception as e:
            await gch.send("직업 부여 과정에서 오류가 발생했습니다.")
            print("직업 부여 오류 | ", e, " | 방장 : ", author, "(", author.id, ")")
            await endgame(gch, gamedata, author, guild)
            
            return None

#---------------------------------------------------------------------------------------------

async def day(gch, guild, author, gamedata):
    #낮이 되었습니다
    print("낮으로 바꾸는 중... | 방장 : ", author, "(", author.id, ")")

    try: # 채널 권한 수정
        for user in gamedata[author.id]['member']:
            await gch.set_permissions(user, read_messages=True, send_messages=True, create_instant_invite=False)

        await gch.send(str(gamedata[author.id]['day']) + "일차 낮이 되었습니다. `120`초 간 자유롭게 대화하실 수 있습니다.")
        print("낮 설정 완료 | 방장 : ", author, "(", author.id, ")")
        await asyncio.sleep(120.0)

    except Exception as e:
        await gch.send("채널 관리 권한이 없어 낮으로 바꿀 수 없습니다.")
        print("밤→낮 오류 | ", e, " | 방장 : ", author, "(", author.id, ")")
        await endgame(gch, gamedata, author, guild)

    return gch

#---------------------------------------------------------------------------------------------

async def night(gch, guild, author, gamedata):
    #밤이 되었습니다
    print("밤으로 바꾸는 중... | 방장 : ", author, "(", author.id, ")")

    try: # 채널 권한 수정
        for user in gamedata[author.id]['member']:
            notice_msg += user.mention + " "
            await gch.set_permissions(user, read_messages=True, send_messages=True, create_instant_invite=False)

        gamedata[author.id]['day'] = gamedata[author.id]['day'] + 1
        embed=  discord.Embed(
            title = str(gamedata[author.id]['day']) + "일차 밤이 되었습니다.",
            description =  "마피아, 경찰, 의사 순서대로 DM이 전송되어 능력을 사용할 수 있습니다. \n본인의 차례까지 조금만 기다려주세요.",
            color = 0xffff00
        )
        await gch.send(embed=embed)
        print("밤 설정 완료 | 방장 : ", author, "(", author.id, ")")

    except Exception as e:
        await gch.send("오류가 발생했습니다.")
        print("낮→밤 오류 | ", e, " | 방장 : ", author, "(", author.id, ")")
        await endgame(gch, gamedata, author, guild)
    return gch

#---------------------------------------------------------------------------------------------

async def endgame(gch, gamedata, author, guild):
    await gch.send("오류가 감지되어 잠시 뒤 자동으로 채널을 닫고 게임을 종료합니다.")
    await asyncio.sleep(30.0)

    try:
        await gch.delete()
        gamedata[author.id] = None
        print("게임 강제 종료 | 방장 : ", author, "(", author.id, ")")

    except Exception as e:
        await gch.send("채널 삭제 중 오류가 발생했습니다.")
        print("강제 종료 오류| ", e, " | 방장 : ", author, "(", author.id, ")")
        gamedata[author.id] = None
    return None

#---------------------------------------------------------------------------------------------

async def saveall(userdata): #save userdata
    with open("./mafia.txt", 'w') as f:
        f.write(str(userdata))
    return userdata

#---------------------------------------------------------------------------------------------

async def sendliveuser(bangjang, gamedata):
    userlist = []
    userlist.append(gamedata[bangjang.id]['live_mafia'])
    userlist.append(gamedata[bangjang.id]['live_citizen'])
    userlist = random.sample(userlist, len(userlist))

    des = ""
    if len(userlist) < 2:
        des += ":one: " + str(userlist[0])
    if len(userlist) < 3:
        des += ":seven: " + str(userlist[1])
    if len(userlist) < 4:
        des += ":six: " + str(userlist[2])
    if len(userlist) < 5:
        des += ":five: " + str(userlist[3])
    if len(userlist) < 6:
        des += ":four: " + str(userlist[4])
    if len(userlist) < 7:
        des += ":three: " + str(userlist[5])
    if len(userlist) < 8:
        des += ":two: " + str(userlist[6])
    if len(userlist) == 8:
        des += ":one: " + str(userlist[7])
    if des == "":
        return "오류가 발생했습니다."
    else:
        return des, userlist         

#---------------------------------------------------------------------------------------------

async def police_ability(bangjang, gamedata):
    if gamedata[bangjang.id]['police'] != None and gamedata[bangjang.id]['police'] in gamedata[bangjang.id]['live_citizen']:
        police = gamedata[bangjang.id]['police']
        
        des, userlist = await sendliveuser(bangjang, gamedata)
        embed = discord.Embed(
            title = "검사할 사람의 번호를 숫자만 입력하세요. (제한시간 : 15초)",
            description = des,
            color = 0x0000FF 
        )
        pch = await police.send(embed=embed)
        
        def check(mes):
            return mes.author == police and mes.channel == pch.channel
                                    
        try:
            mes = await client.wait_for('message', check=check, timeout=15)
            answer = mes.content
                            
        except asyncio.TimeoutError:
            await police.send(police.mention + " 시간이 만료되었습니다.")
            answer = ""
        if answer != "":
            if userlist[bangjang.id][answer - 1] in gamedata[bangjang.id]['live_mafia']:
                await police.send(str(userlist[bangjang.id][answer-1].name) + "님은 마피아가 맞습니다.")
            else:
                await police.send(str(userlist[bangjang.id][answer-1].name) + "님은 마피아가 아닙니다.")
        return None
        
    else:
        return None

async def doctor_ability(author, gamedata):
    if gamedata[author.id]['doctor'] != None and gamedata[author.id]['doctor'] in gamedata[author.id]['live_citizen']:
        doctor = gamedata[author.id]['doctor']

        des, userlist = await sendliveuser(author, gamedata)
        embed = discord.Embed(
            title = "살릴 사람의 번호를 숫자만 입력하세요. (제한시간 : 15초)",
            description = des,
            color = 0x0000FF
        )
        doctorch = await doctor.send(embed=embed)

        def check(mes):
            return mes.author == doctor and mes.channel == doctorch.channel
        try:
            mes = await client.wait_for('message', check=check, timeout=15)
            answer = mes.content
        except asyncio.TimeoutError:
            await doctor.send(doctor.mention + " 시간이 만료되었습니다.")
            answer = ""
        if answer != "":
            doctorsave = userlist[author.id][answer-1]
            return doctorsave
    else:
        return None

async def kill(gch, author, gamedata):
    if gamedata[author.id]['mafia2'] != None: #마피아 2명이면
        #어캐만들까고민좀
        return None

    else: #마피아 1명이면
        if gamedata[author.id]['mafia1'] in gamedata[author.id]['live_mafia']: #생존 체크 - 그닥 의미없음, 혹시나 모를 버그 방지
            mafia = gamedata[author.id]['mafia1']
            des, userlist = await sendliveuser(author, gamedata)
            embed = discord.Embed(
                title = "죽일 사람의 번호를 숫자만 입력하세요. (제한시간 : 15초)",
                description = des,
                color = 0x0000FF
            )
            mch = await mafia.send(embed=embed)

            def check(mes):
                return mes.author == mafia and mes.channel == mch.channel
            try:
                mes = await client.wait_for('message', check=check, timeout=15)
                answer = mes.content
            except asyncio.TimeoutError:
                await mafia.send(mafia.mention + " 시간이 만료되었습니다.")
                answer = ""
            if answer != "":
                mafiakill = userlist[author.id][answer - 1]
                return mafiakill

        else:
            return None
#mafiakill = await kill(gch, author, gamedata) #마피아가 죽이고
'''
async def vote(gamedata, author, gch):
# 투표(다수결)
    for i in range(len(gamedata[author.id]['member'])):
        def 
    return votedata
'''

@client.event
async def on_ready():
    print("on_ready")


@client.event
async def on_message(message):
    msg = message.content
    author = message.author
    ch = message.channel
    guild = message.guild

    global gamedata
    global userdata
    global bot

    if author.id == 751088717485047900:
        bot = author
    
    if author.bot: 
        return None
    
    if msg == "마피아":
        await ch.send("명령어 사용법 : `마피아 도움`")

    elif msg.startswith("마피아 ") and type(ch) == discord.TextChannel:
        msg = msg[4:]
        try:
            userdata = await getData(author, ch)

        except Exception as e:
            await ch.send("등록에 오류가 발생했습니다.")
            print("등록 오류 발생 |", e, " | id : ", author.id)
            return None

        if userdata[author.id]['ban'] == 0: #밴 안먹었으면 작동
            if msg == "도움":
                embed = discord.Embed(
                    title = "마피아봇 도움말",
                    description = "디스코드로 마피아게임을 즐겨보세요.",
                    color = 0x0077aa
                )
                embed.set_footer(text="Madt By Team Pickle")
                embed.add_field(name = "마피아 개최", value = "마피아 게임이 가능한 방을 생성합니다.", inline = False)
                embed.add_field(name = "마피아 참여 @방 개설자", value = "개설된 방에 참가합니다.", inline = False)
                embed.add_field(name = "마피아 관전 @방 개설자", value = "개설된 방의 게임을 관전합니다.", inline = False)
                await ch.send(embed=embed)

            elif msg == "시작" or msg == "개최" or msg == "개설":
                gamedata = {}
                try:
                    if gamedata[author.id]['onoff']:
                        await ch.send("진행중인 게임이 있습니다.")
                        return None
                except:
                    pass
                
                gamedata[author.id]={
                    'game':False, 'onoff':True, 'member':[],'mafia1':0, 'mafia2':0, 
                    'doctor':0, 'police':0, 'day':0, 'citizen1':0, 'citizen2':0, 
                    'citizen3':0, 'citizen4':0, 'live_mafia':[], 'live_citizen':[], 'watch_user':[],
                    'channel':ch
                }
                #game: 게임 진행중?, onoff : 새로운 맴버 출입 가능?, member: 유저정보 저장, day: n일차, mafia~citizen:직업 별 데이터, \
                #live_mafia:생존마피아팀, live_citizen:생존시민팀, dead_user:죽은유저, watch_user:관전/사망 유저
                print("새 게임 생성 | 방장 : ", author,"(", author.id, ")")
                embed=discord.Embed(
                    title = "60초 후 게임을 시작합니다.",
                    description = "`마피아 참여 @" + str(author.name + "`을(를) 입력해 게임에 참가하세요.\n모집을 종료하려면 `마피아 모집종료`를 입력하세요."),
                    color=0xffff00
                )
                await ch.send(embed=embed)
                gamedata = await game_attend(ch, author, author.id, gamedata)
                temp=0
                while temp < 60:
                    if gamedata[author.id]['onoff']:
                        if temp == 30:
                            await ch.send("참가자 모집 마감까지 `30초` 남았습니다.")
                        elif temp == 45:
                            await ch.send("참가자 모집 마감까지 `15초` 남았습니다.")
                        temp += 1
                        await asyncio.sleep(1) 
                    else:
                        temp = 60
                        
                if len(gamedata[author.id]['member']) >= 1: #최소참가인원 - 5
                    gamedata[author.id]['onoff'] = False #모집마감
            
                    if not gamedata[author.id]['onoff']:
                        embed = discord.Embed(
                            title = "인원 모집이 마감되었습니다.", 
                            description = "참가 인원은 `" + str(len(gamedata[author.id]['member'])) + "명` 입니다.\n게임을 시작하시겠습니까? [ㅇ/ㄴ]",
                            color=0xffff00
                        )
                        await ch.send("<@"+str(author.id)+">")
                        await ch.send(embed=embed)
                        #나중에 수정하기
                                
                        def check(mes):
                            return mes.author == author and mes.channel == ch
                                    
                        try:
                            mes = await client.wait_for('message', check=check, timeout=15)
                            answer = mes.content
                            
                        except asyncio.TimeoutError:
                            await ch.send("<@" + str(author.id) + "> 시간이 만료되어 게임을 취소합니다.")

                        if answer == "ㅇ" or answer == "d":
                            gamedata[author.id]['game'] = True
                            gch = await make_gameroom(ch, guild, author, gamedata) #채널 생성
                            gamedata[author.id]['channel'] = gch
                            gamedata = await draw_jobs(gch, gamedata, author, guild) # 직업 추첨
                            embed = discord.Embed(
                                title = "게임을 시작합니다.",
                                description = "각자의 직업이 DM으로 전송되었습니다.\n60초의 자기소개 시간이 주어집니다. 오늘 밤부터 능력을 사용할 수 있습니다.",
                                color = 0xffff00
                            )
                            try:
                                await gch.send(embed=embed)
                                await asyncio.sleep(30.0)
                                embed = discord.Embed(
                                    title = "30초 남았습니다.",
                                    color = 0xffff00
                                )
                                await gch.send(embed=embed)
                                await asyncio.sleep(20.0)
                                embed = discord.Embed(
                                    title = "10초 남았습니다.",
                                    color = 0xffff00
                                )
                                await gch.send(embed=embed)
                                await asyncio.sleep(10.0)
                                while 1:
                                    gch = await night(gch, guild, author, gamedata) # 밤 만들기
                                    
                                    await police_ability(author, gamedata) #경찰능력사용/출력
                                    doctorsave = await doctor_ability(author, gamedata) #의사능력사용
                                    mafiakill = await kill(gch, author, gamedata) #마피아가 죽이고
                                    #gch = awiat day_broadcast(gch, author) #아침 방송하기
                                    if doctorsave.id == mafiakill.id: #같으면 살리고
                                        embed = discord.Embed(
                                            title = "사건 발생 알림",
                                            description = doctorsave.mention + "님이 마피아의 공격을 받았지만, 의사의 치료를 받고 살아났습니다.",
                                            color = 0x81c147
                                        )
                                        await gch.send(embed=embed)
                                    
                                    else: # 다르면 죽임
                                        embed = discord.Embed(
                                            title = "사건 발생 알림",
                                            description = mafiakill.mention + "님이 마피아의 공격을 받고 살해된 채로 발견되었습니다.",
                                            color = 0xff0000
                                        )
                                        await gch.send(embed=embed)
                                        gamedata[author.id]['dead_user'].append(mafiakill)
                                        if mafiakill in gamedata[author.id]['live_mafia']:
                                            gamedata[author.id]['live_mafia'].remove()
                                        elif mafiakill in gamedata[author.id]['live_citizen']:
                                            gamedata[author.id]['live_citizen'].remove()
                                        else:
                                            await gch.send("오류가 발생했습니다.")
                                            print("킬 오류 | 방장 : ", author, "(", author.id, ")")
                                            await endgame(gch, gamedata, author, guild)

                                    gch = await day(gch, guild, author, gamedata) #아침 만들기(채팅 가능하게 만들기) 
                                
                                    #투표하기
                                    #제일 많은 표를 받은 사람 가려내기
                                    #최후의 진술
                                    #투표하기
                                    #투표결과 비교하기
                                    #처형하기
                                    #처형된사람 권한 조정하기
                                    #한쪽 팀 승리여부 판별하기 (남은시민<=남은마피아 or 남은마피아 == 0)
                                    #if gamedata[author.id]['live_mafia'] == 0: # 시민 승리
                                        
                                #elif gamedata[author.id]['live_citizen'] <= gamedata[author.id]['live_mafia']: # 

                                    #계속반복 or 승리메세지 출력
                                #승리/패배팀 각각 포인트 지급
                            except:
                                None
                        else:
                            await ch.send("게임이 취소되었습니다. `마피아 시작`을 입력해 다시 시작할 수 있습니다.")
                                

                    else:
                        await ch.send("<@" + str(author.id) + "> 참가인원이 부족하여 게임이 취소되었습니다.")

            elif msg.startswith("참가") or msg.startswith("참여"):
                if msg == "참가" or msg == "참여":
                    await ch.send("``마피아 참가 @개설자`` 형식으로 사용하세요.")
                else:
                    adminid = message.mentions[0].id 
                    gamedata = await game_attend(ch, author, adminid, gamedata)
                    
            elif msg.startswith("관전"):
                if msg == "관전":
                    await ch.send("``마피아 관전 @개설자`` 형식으로 사용하세요.")
                else:
                    adminid = message.mentions[0].id 
                    if gamedata[adminid]['game']:
                        gch = gamedata[adminid]['channel']
                        
                        try: # 채널 권한 수정
                            await gch.set_permissions(author, read_messages=True, send_messages=False, create_instant_invite=False)
                            await gch.send(author.mention + "님이 관전을 시작했습니다.")
                            print("관전 시작 | 요청자 : ", author, "(", author.id, ") | 관전 대상 방 : ", adminid)
                            embed = discord.Embed(
                                title = "주의하세요!",
                                description = "관전 중 채팅은 금지되며, 게임 진행에 참견하는 행위(훈수) 등은 절대 자제해 주시기 바랍니다.",
                                color = 0xFF0000
                            )
                            await author.send(embed=embed)
                        except Exception as e:
                            await ch.send("오류가 발생하여 관전할 수 없습니다.")
                            print("관전 오류 | ", e, " | 요청자 : ", author, "(", author.id, ")")


            elif msg.startswith("전적") or msg.startswith("정보") or msg.startswith("프로필"):
                if msg == "전적" or msg == "정보" or msg == "프로필":
                    #자기 자신의 정보 출력
                    embed = discord.Embed(
                        title = author.name + "님의 프로필",
                        description = "",
                        color = 0x0077aa
                    )
                    embed.add_field(name = "마피아로 이긴 판", value = str(userdata[author.id]['mafia_win']) + "(" + str(userdata[author.id]['mafia_winper']) + "%)", inline = False)
                    embed.add_field(name = "시민으로 이긴 판", value = str(userdata[author.id]['citizen_win']) + "(" + str(userdata[author.id]['citizen_winper']) + "%)", inline = False)
                    embed.add_field(name = "총 플레이한 횟수", value = str(userdata[author.id]['totalgame']) + "판", inline = False)
                    embed.add_field(name = "누적 포인트", value = str(userdata[author.id]['point']), inline = False)
                    await ch.send(embed=embed)
                else:
                    
                    userid = message.mentions[0]
                    try:
                        embed = discord.Embed(
                            title = userid.name + "님의 프로필",
                            description = "",
                            color = 0x0077aa
                        )
                        embed.add_field(name = "마피아로 이긴 판", value = str(userdata[userid.id]['mafia_win']) + "(" + str(userdata[userid.id]['mafia_winper']) + "%)", inline = False)
                        embed.add_field(name = "시민으로 이긴 판", value = str(userdata[userid.id]['citizen_win']) + "(" + str(userdata[userid.id]['citizen_winper']) + "%)", inline = False)
                        embed.add_field(name = "총 플레이한 횟수", value = str(userdata[userid.id]['totalgame']) + "판", inline = False)
                        embed.add_field(name = "누적 포인트", value = str(userdata[userid.id]['point']), inline = False)
                        await ch.send(embed=embed)
                    except:
                        await ch.send("등록된 유저가 아닙니다.")
            elif msg.startswith("너밴"):
                banid = message.mentions[0].id
                await ch.send(str(banid) +"이(가) 당신에 의해 차단되었습니다.")
                userdata[banid]['ban'] = 1
                await saveall(userdata)
                print("밴 | 처리자: |", author, "(",author.id, ") | 대상자 : ", banid)

            elif msg.startswith("풀어줄게"):
                banid = message.mentions[0].id 
                await ch.send("unbanid : " + str(banid))
                userdata[banid]['ban'] = 0
                await saveall(userdata)
                print("언밴 | 처리자: |", author, "(",author.id, ") | 대상자 : ", banid)

            elif msg == "모집종료" or msg == "모집 종료" or msg == "모집중단" or msg == "모집 중단":
                try:
                    if gamedata[author.id]['onoff']:
                        gamedata[author.id]['onoff'] = False
                        await ch.send("참가자 모집을 종료합니다.")
                        print("조기 모집 종료 | 방장 : ", author, "(", author.id, ")")
                except:
                    await ch.send("참가자 모집 중인 게임이 없습니다.")
        else:
            embed = discord.Embed(
                title="게임을 이용할 수 없습니다.",
                description="다른 사용자들의 게임을 방해하는 플레이가 발견되어 게임 이용이 일시 제한되었습니다.\n나중에 다시 시도하세요.",
                color=0xff4848
            )
            await ch.send(embed=embed)

client.run(token)
