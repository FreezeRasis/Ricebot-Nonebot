import datetime
import sqlite3
import requests
from nonebot import on_command, CommandSession

database = 'myDB.sqlite3'


# 计算自从游玩时间到现在过了多久
def string_toDatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")


def timeDelta(time):
    past = string_toDatetime(time)
    now = datetime.datetime.now()
    deltaSeconds = (now - past).total_seconds()
    if deltaSeconds > 86400:
        return str(round(deltaSeconds / 86400)) + "天前"
    if deltaSeconds > 3600:
        return str(round(deltaSeconds / 3600)) + "小时前"
    if deltaSeconds > 60:
        return str(round(deltaSeconds / 60)) + "分钟前"
    else:
        return str(round(deltaSeconds)) + "秒前"


# 获取最近5个游戏记录
@on_command('.recent', aliases='.recent', only_to_me=False)
async def get_recent_score(session: CommandSession):
    # 从数据库中得到token
    conn = sqlite3.connect(database)
    c = conn.cursor()
    t = str(session.ctx['user_id'])
    c.execute('SELECT * FROM info WHERE qq = (?)', (t,))
    token = (c.fetchone()[3])
    conn.close()

    # 获取成绩json
    url = 'https://iot.universal-space.cn/api/mns/mnsGame/recordList?productId=3084&pageNo=1&pageSize=5&orderBy' \
          '=gameDate '
    playdata = requests.get(url, headers={'token': token})
    json_str = playdata.json()

    # json处理和发送最终生成的成绩
    i = 0
    a = "FZ.RASIS最近的游戏记录：\n"
    while i < 5:
        a += (str(json_str["data"][i]["musicName"]) + "[" +
              json_str["data"][i]["musicGradeName"].replace("NOVICE", "NOV").replace("ADVANCED", "ADV")
              .replace("EXHAUST", "EXH").replace("MAXIMUM", "MXM")
              .replace("INFINITE", "INF").replace("VIVID", "VVD") + "]  " +
              str(json_str["data"][i]["score"]) + "  " +
              json_str["data"][i]["clearTypeName"] + "  " +
              timeDelta(json_str["data"][i]["gameDate"]) + "\n"
              )
        i += 1
    await session.send(a)


# 根据所给的数字查询从现在往前推第n个成绩
@on_command('.last', aliases='.last', only_to_me=False)
async def get_recent_score(session: CommandSession):
    # 从数据库中得到token
    conn = sqlite3.connect(database)
    c = conn.cursor()
    t = str(session.ctx['user_id'])
    c.execute('SELECT * FROM info WHERE qq = (?)', (t,))
    token = (c.fetchone()[3])
    conn.close()

    # 获取输入的参数，没有输入或者输入错误默认为1
    num = 1
    if num:
        num = session.current_arg_text.strip()

    # 获取成绩json
    url = 'https://iot.universal-space.cn/api/mns/mnsGame/recordList?productId=3084&pageNo=' + num + \
          '&pageSize=1&orderBy=gameDate'
    playdata = requests.get(url, headers={'token': token})
    json_str = playdata.json()

    # json处理和发送最终生成的成绩，包含了图片
    a = "[CQ:image,file="

    a += (str(json_str["data"][0]["musicImage"]) + "]" +
          str(json_str["data"][0]["musicName"]) + "[" +
          json_str["data"][0]["musicGradeName"].replace("NOVICE", "NOV").replace("ADVANCED", "ADV")
          .replace("EXHAUST", "EXH").replace("MAXIMUM", "MXM").replace("INFINITE", "INF")
          .replace("VIVID", "VVD") + "]\n" +
          str(json_str["data"][0]["score"]) + "  " +
          str(json_str["data"][0]["criticalCount"]) + "/" +
          str(json_str["data"][0]["nearCount"]) + "/" +
          str(json_str["data"][0]["errorCount"]) + "\n" +
          json_str["data"][0]["clearTypeName"] + "  " +
          timeDelta(json_str["data"][0]["gameDate"])
          )
    await session.send(a)
