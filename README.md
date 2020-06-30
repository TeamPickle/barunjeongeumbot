# 바른정음
[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)
[![Forum](https://discordapp.com/api/guilds/680026950064275466/widget.png)](http://forum.tpk.kr)

지금바로 초대하기 ===> http://korean.tpk.kr

### 바른 한글 생활 도우미 디스코드 바른정음 봇입니다
파이썬 3.7 ~ 3.8을 지원합니다.
> 한글은 세계 어떤 나라의 문자에서도 볼 수 없는 가장 과학적인 표기체계이다
> (_미국 하버드대 라이샤워 교수_) <br/>

네이버 맞춤법 검사 API를 활용해서 디스코드 채팅에서 발견한 맞춤법 오류를 사용자에게 DM으로 알려줍니다.

## 명령어 목록
- !도움말 : 도움말
- !랭크 : 별별 랭킹 출력
- !수신거부 : DM으로 오는 지적사항을 수신거부 합니다. 다시 한번 입력할 시 거부가 해제됩니다
- !서버수신거부 : 서버에서 DM으로 오는 지적사항을 수신거부 합니다. 다시 한번 입력할 시 거부가 해제됩니다 (관리자)
- !무시 (숫자) : (숫자) 개 이하의 맞춤법 오류는 DM으로 지적사항을 보내지 않습니다
## 어떻게 소스를 실행할 수 있나요?
-----
해당 레포는 [py-hanspell](https://github.com/ssut/py-hanspell), discord.py, pymongo 라이브러리를 필요로 합니다.<br/>
바른정음은 MongoDB를 사용합니다. MongoDB 서버가 필요합니다.
<span style="color:red">반드시 **수동 설치**로 다운로드 하셔야 합니다<span>.
 
클론한 후 .env 파일에 환경변수를 입력해주세요
예시
```python
DB_ID=아이디
DB_PW=비밀번호
DB_HOST=몽고DB서버_아이피
DB_PORT=몽고DB서버_포트
TOKEN=디스코드_봇_토큰
```
다음으로 아래 명령어를 cmd에 입력시켜주세요
```python
python run.py
```
## 바른정음과 함께 바른 한국어 생활로 나아갑시다!
