import datetime
import json
import nonebot
import requests
from nonebot import on_command, CommandSession


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


@on_command('.recent', aliases='r', only_to_me=False)
async def get_recent_score(session: CommandSession):
    token = "8uwJseEBMkEQwxwlydiUuoSRmXoD1wKit8qho6rQGuEOg1xGqCz6eTvpMpmQ0pmr"
    url = 'https://iot.universal-space.cn/api/mns/mnsGame/recordList?productId=3084&pageNo=1&pageSize=5&orderBy=gameDate'
    playdata = requests.get(url, headers={'token': token})
    json_str = playdata.json()

    i = 0
    a = "FZ.RASIS最近的游戏记录：\n"
    while i < 5:
        a += (str(json_str["data"][i]["musicName"]) + "[" +
              json_str["data"][i]["musicGradeName"].replace("NOVICE", "NOV").replace("ADVANCED", "ADV")
              .replace("EXHAUST", "EXH").replace("MAXIMUM", "MXM").replace("INFINITE", "INF").replace("VIVID",
                                                                                                      "VVD") + "]  " +
              str(json_str["data"][i]["score"]) + "  " +
              json_str["data"][i]["clearTypeName"] + "  " +
              timeDelta(json_str["data"][i]["gameDate"]) + "\n"
              )
        i += 1
    await session.send(a)


@on_command('.last', aliases='.last', only_to_me=False)
async def get_recent_score(session: CommandSession):
    token = "" #在这里填入token

    num = 1
    if num:
        num = session.current_arg_text.strip()

    url = 'https://iot.universal-space.cn/api/mns/mnsGame/recordList?productId=3084&pageNo=' + num + \
          '&pageSize=1&orderBy=gameDate'
    playdata = requests.get(url, headers={'token': token})
    json_str = playdata.json()

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
