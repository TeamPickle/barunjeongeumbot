# -*- coding:utf-8 -*-
import asyncio
import discord
import datetime
import re
import os
import requests
from dotenv import load_dotenv
from hanspell import spell_checker
import pymongo
import pickle
load_dotenv("./.env")
token = os.getenv("TOKEN")
def remove(x) :
    m = re.sub(r'(?:[0-9a-zA-Zㄱ-ㅎㅏ-ㅣ]|[?!\W]+)\s*', ' ', x).strip() 
    m = " ".join(m.split())
    return m
config = {'user': os.getenv("DB_ID"), 'pwd': os.getenv(
    "DB_PW"), 'host': os.getenv("DB_HOST"), 'port': int(os.getenv("DB_PORT"))}

client = pymongo.MongoClient("mongodb://%s:%s@%s:%s" %
                             (config['user'], config['pwd'], config['host'], config['port']))
rank_list = ['point', 'point', 'sum_errors', 'error_count', 'korean_grade', 'korean_grade']
rank_list_kr = ['포인트 높은 순', '포인트 낮은 순', '총 오류 높은 순', '총 검사 수 많은 순', '평균 맞춤법 오류 높은 순', '평균 맞춤법 오류 낮은 순']
up_or_down = [-1, 1, -1, -1, -1, 1]

db = client['korean']

def add_point(author):
  data = db.user.find_one({'user_id': author.id})
  if data != None:
    new_data = data
    new_data['point'] += 20
    new_data['error_count'] += 1
    new_data['korean_grade'] = round(new_data['sum_errors'] / new_data['error_count'], 4)
    db.user.replace_one({'user_id': author.id}, new_data)

def minus_point(author, errors):
  data = db.user.find_one({'user_id': author.id})
  if data != None:
    new_data = data
    new_data['point'] -= errors * 5
    new_data['error_count'] += 1
    new_data['sum_errors'] += errors
    new_data['korean_grade'] = round(new_data['sum_errors'] / new_data['error_count'], 4)
    db.user.replace_one({'user_id': author.id}, new_data)

def check_user(author):
  data = db.user.find_one({'user_id': author.id})
  if data == None:
    db.user.insert_one({
      'user_id': author.id,
      'user_name': author.name,
      'point': 0,
      'sum_errors': 0,
      'error_count': 0,
      'korean_grade': 0
    })

async def getUserEmbed(author, ch):
  data = db.user.find_one({'user_id': author.id})
  if data != None:
    embed = discord.Embed(
      title="바른정음 한국어 능력",
      description="바른 한국어 생활이 세종대왕을 기쁘게 합니다",
      color=0x0077aa
    )
    embed.set_thumbnail(url="https://i.ibb.co/YQ0TYVN/image.png")
    embed.add_field(name="포인트", value=str(data['point']), inline=False)
    embed.add_field(name="평균 맞춤법 오류 횟수", value=str(data['korean_grade']), inline=False)
    embed.add_field(name="총 맞춤법 오류 수", value=str(data['sum_errors']), inline=False)
    embed.add_field(name="총 검사 수", value=str(data['error_count']), inline=False)
    try:
      await ch.send(embed=embed)
    except discord.Forbidden:
      print("권한 없음")
  else:
    print('')
async def spell_send(author, msg, ch):
  check_user(author)
  result = spell_checker.check(msg)
  result_dict = result.as_dict()
  if result_dict['result'] and result_dict['errors'] > 0:
    minus_point(author, result_dict['errors'])
    with open('ignore.txt', 'rb') as f:
      data = pickle.load(f)
    if author.id in data:
      return None
    with open('ignoresr.txt', 'rb') as f:
      data = pickle.load(f)
    if ch.guild.id in data:
      return None
    with open('ignore_cnt.txt', 'rb') as f:
      data = pickle.load(f)
    if author.id in data:
      if int(result_dict['errors']) < data[author.id]:
        return None
    embed = discord.Embed(
      title="바른정음 맞춤법 지적 시스템",
      description="올바른 한국어 사용을 위해 한국어 사용을 지적합니다",
      color=0x0077aa
    )
    embed.set_thumbnail(url="https://i.ibb.co/YQ0TYVN/image.png")
    embed.add_field(
      name="수정 전 문장",
      value=result_dict['original'],
      inline=False
    )
    embed.add_field(
      name="수정 후 문장",
      value=result_dict['checked'],
      inline=False
    )
    embed.add_field(
      name="총 맞춤법 에러",
      value=str(result_dict['errors']),
      inline=False
    )
    try:
      await author.send(embed=embed)
    except discord.Forbidden:
      await ch.send(embed=embed)
  else:
    add_point(author)
client = discord.Client()
async def getRanking(cnt, ch):
  datas = db.user.find({"error_count": {"$gt": 10}}).sort(rank_list[cnt], up_or_down[cnt]).limit(10)
  if datas == None:
    await ch.send("충분한 데이터가 모이지 않아서 랭킹을 보여줄 수 없습니다..")
  else:
    embed = discord.Embed(
      title="바른정음 맞춤법 랭킹 시스템 - " + rank_list_kr[cnt],
      description="올바른 한국어 사용을 위해 한국어 사용을 지적합니다",
      color=0x0077aa
    )
    i = 1
    val = ""
    for data in datas:
      val = val + str(i) + "위 " + data['user_name'] + " " + str(data[rank_list[cnt]]) + "\n"
      i += 1
    embed.add_field(
        name="랭킹보드",
        value=val,
        inline=True
      )
    embed.set_thumbnail(url="https://i.ibb.co/YQ0TYVN/image.png")
    await ch.send(embed=embed)
    
    
@client.event
async def on_ready():
  print('봇 작동 시작')
  await client.change_presence(status=discord.Status.online, activity=discord.Game(name='한글 맞춤법 검사 '))

@client.event
async def on_message(message):
  author = message.author
  msg = message.content.strip()
  ch = message.channel
  
  if author.bot and author.id != 680302331992080411:
    return None
  if msg.startswith("!"):
    if msg.startswith("!도움"):
      embed = discord.Embed(
      title="바른정음 명령어 도움",
      description="디스코드 채팅을 맞춤법 검사하여 지적해주는 봇 입니다!",
      color=0x0077aa,
      
    )
      embed.set_footer(text="Made By happycastle in Team Pickle")
      embed.set_thumbnail(url="https://i.ibb.co/YQ0TYVN/image.png")
      embed.add_field(name="!프로필", value="자신의 포인트, 총 에러 수, 총 검사 수, 평균 맞춤법 에러 수를 보여줍니다.",inline=False)
      embed.add_field(name="!프로필 @사람멘션", value="해당 사람의 포인트, 총 에러 수, 총 검사 수, 평균 맞춤법 에러 수를 보여줍니다.",inline=False)
      embed.add_field(name="!랭킹", value="별별 랭킹을 보여줍니다. !랭킹을 입력하면 더 많은 정보를 제공해줍니다",inline=False)
      embed.add_field(name="!수신거부", value="DM으로 오는 지적사항을 수신거부 합니다. 다시 한번 입력할 시 거부가 해제됩니다",inline=False)
      embed.add_field(name="!서버수신거부", value="서버에서 DM으로 오는 지적사항을 수신거부 합니다. 다시 한번 입력할 시 거부가 해제됩니다 (관리자)",inline=False)
      embed.add_field(name="!무시 (숫자)", value="(숫자) 개 이하의 맞춤법 오류는 DM으로 지적사항을 보내지 않습니다",inline=False)
      
      embed.add_field(name="초대링크", value="http://korean.tpk.kr",inline=True)
      embed.add_field(name="공식 포럼 및 버그 신고", value="http://fourm.tpk.kr",inline=True)
      await ch.send(embed=embed)
    if msg.startswith("!프로필"):
      if len(message.mentions) > 0:
        author = message.mentions[0]
      check_user(author)
      await getUserEmbed(author, ch)
    if msg.startswith("!무시"):
      if len(msg.split(" ")) == 2:
        with open('ignore_cnt.txt', 'rb') as f:
          data = pickle.load(f)
        data[author.id] = int(msg.split(" ")[1])
        with open('ignore_cnt.txt', 'wb') as f:
          data = pickle.dump(data, f)
        await ch.send('> 맞춤법 무시 설정 완료\n> 앞으로 ' + str(msg.split(" ")[1])+ '개 이하의 맞춤법 오류는 봇이 DM을 보내지 않습니다.')
      else:
        await ch.send("> 사용법 : !무시설정 (무시할 맞춤법 오류 수)")
    if msg.startswith("!수신거부"):
      val = ""
      with open('ignore.txt', 'rb') as f:
        data = pickle.load(f)
      if not author.id in data:
        data.append(author.id)
        val = "> 수신 거부 설정 완료\n> 앞으로 맞춤법이 틀리더라도 봇이 DM을 보내지 않습니다."
      else:
        data.remove(author.id)
        val = "> 수신 거부 해제 완료\n> 앞으로 맞춤법이 틀리면 봇이 DM을 보내드립니다."
      with open('ignore.txt', 'wb') as f:
        data = pickle.dump(data, f)
      await ch.send(val)
    if msg.startswith("!서버수신거부"):
      if format(author.guild_permissions.value, 'b')[-3] == '1':
        val = ""
        with open('ignoresr.txt', 'rb') as f:
          data = pickle.load(f)
        if not message.guild.id in data:
          data.append(message.guild.id)
          val = "> 수신 거부 설정 완료\n> 앞으로 이 서버에서 보내는 메세지가 맞춤법이 틀리더라도 서버원에게 DM을 보내지 않습니다."
        else:
          data.remove(message.guild.id)
          val = "> 수신 거부 해제 완료\n> 앞으로 이 서버에서 보내는 메세지의 맞춤법이 틀리면 서버원에게 DM을 보냅니다. 단, 개별적으로 수신거부를 설정한 멤버에게는 해당되지 않습니다."
        with open('ignoresr.txt', 'wb') as f:
          data = pickle.dump(data, f)
        await ch.send(val)
      else:
        await ch.send("> 관리자만 사용 가능한 명령어 입니다!")
    if msg.startswith("!랭킹"):
      if len(msg.split(" ")) == 2:
        if int(msg.split()[1]) < 6 and int(msg.split()[1]) >= 0:
          await getRanking(int(msg.split()[1]), ch=ch)
        else:
          embed = discord.Embed(
      title="바른정음 맞춤법 별별 랭킹 시스템",
      description="올바른 한국어 사용을 위해 한국어 사용을 지적합니다",
      color=0x0077aa
    )
          embed.add_field(name="!랭킹 0", value="포인트가 높은 순으로 상위 10명을 보여줍니다",inline=False)
          embed.add_field(name="!랭킹 1", value="포인트가 낮은 순으로 상위 10명을 보여줍니다",inline=False)
          embed.add_field(name="!랭킹 2", value="총 오류 수가 높은 순으로 상위 10명을 보여줍니다",inline=False)
          embed.add_field(name="!랭킹 3", value="총 검사 수가 높은 순으로 상위 10명을 보여줍니다",inline=False)
          embed.add_field(name="!랭킹 4", value="평균 맞춤법 오류가 높은 순으로 상위 10명을 보여줍니다",inline=False)
          embed.add_field(name="!랭킹 5", value="평균 맞춤법 오류가 낮은 순으로 상위 10명을 보여줍니다",inline=False)
          embed.set_thumbnail(url="https://i.ibb.co/YQ0TYVN/image.png")
          await ch.send(embed=embed)
      else:
        embed = discord.Embed(
      title="바른정음 맞춤법 별별 랭킹 시스템",
      description="올바른 한국어 사용을 위해 한국어 사용을 지적합니다",
      color=0x0077aa
    )
        embed.add_field(name="!랭킹 0", value="포인트가 높은 순으로 상위 10명을 보여줍니다",inline=False)
        embed.add_field(name="!랭킹 1", value="포인트가 낮은 순으로 상위 10명을 보여줍니다",inline=False)
        embed.add_field(name="!랭킹 2", value="총 오류 수가 높은 순으로 상위 10명을 보여줍니다",inline=False)
        embed.add_field(name="!랭킹 3", value="총 검사 수가 높은 순으로 상위 10명을 보여줍니다",inline=False)
        embed.add_field(name="!랭킹 4", value="평균 맞춤법 오류가 높은 순으로 상위 10명을 보여줍니다",inline=False)
        embed.add_field(name="!랭킹 5", value="평균 맞춤법 오류가 낮은 순으로 상위 10명을 보여줍니다",inline=False)
        embed.set_thumbnail(url="https://i.ibb.co/YQ0TYVN/image.png")
        await ch.send(embed=embed)
  else:
    msg = remove(msg)
    if len(msg) > 10:
      await spell_send(author, msg, ch)
      
client.run(token)