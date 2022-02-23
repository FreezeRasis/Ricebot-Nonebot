import datetime
import json
import sqlite3
import requests
from nonebot import on_command, CommandSession

database = 'myDB.sqlite3'


# 计算自从游玩时间到现在过了多久，返回时间间隔（N秒前、N分钟前、N小时前、N天前）
def timeDelta(string):
    past = datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
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


# 通过QQ在数据库中查询token，如果有则返回token，没有则返回None
def query_token(qq):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('SELECT * FROM info WHERE qq = (?)', (qq,))
    try:
        return c.fetchone()[3]
    except:
        return None
    conn.close()


# 获取新token
def get_new_token(qq):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    try:
        phone = str(c.execute('SELECT phone FROM info WHERE qq = (?)', (qq,)).fetchone()[0])
        url = 'https://iot.universal-space.cn/api/sms/captcha/get/'
        requests.post(url + phone)
        return "获取失败，已重新申请验证码\n指令：.a 验证码"
    except:
        return "请先绑定手机。指令：\n.b 手机号"
    finally:
        conn.close()


# 获取最近5个游戏记录
@on_command('.recent', aliases=('.recent', '.r'), only_to_me=False)
async def get_recent_score(session: CommandSession):
    qq = str(session.ctx['user_id'])
    token = query_token(qq)

    # 获取成绩json
    url = 'https://iot.universal-space.cn/api/mns/mnsGame/recordList?productId=3084&pageNo=1&pageSize=5&orderBy' \
          '=gameDate '
    playdata = requests.get(url, headers={'token': token})
    json_str = playdata.json()
    if json_str["code"] == 403:
        get_new_token(qq)
        await session.send(get_new_token(qq))
    else:

        # json处理和发送最终生成的成绩
        i = 0
        a = "[CQ:at,qq=" + qq + "]" + "最近的游戏记录：\n"
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
@on_command('.last', aliases=('.last', '.l'), only_to_me=False)
async def get_recent_score(session: CommandSession):
    # 从数据库中得到token
    qq = str(session.ctx['user_id'])
    token = query_token(qq)

    # 获取输入的参数，没有输入或者输入错误默认为1
    num = session.current_arg_text.strip()
    if not num:
        num = 1

    # 获取成绩json
    url = 'https://iot.universal-space.cn/api/mns/mnsGame/recordList?productId=3084&pageNo=' + str(num) + \
          '&pageSize=1&orderBy=gameDate'
    playdata = requests.get(url, headers={'token': token})
    json_str = playdata.json()
    if json_str["code"] == 403:
        await session.send(get_new_token(qq))
    else:

        # json处理和发送最终生成的成绩，包含了图片
        a = "[CQ:image,file=" + str(json_str["data"][0]["musicImage"]
                                    #.replace("https://static.universal-space.cn/images/konami/music5/","http://127.0.0.1/img/")
                                    + "]" +
                                str(json_str["data"][0]["musicName"]) + "[" +
                                json_str["data"][0]["musicGradeName"]
                                    .replace("NOVICE", "NOV")
                                    .replace("ADVANCED", "ADV")
                                    .replace("EXHAUST", "EXH")
                                    .replace("MAXIMUM", "MXM")
                                    .replace("INFINITE", "INF")
                                    .replace("VIVID", "VVD") + "]\n" +
                                str(json_str["data"][0]["score"]) + "  " +
                                str(json_str["data"][0]["criticalCount"]) + "/" +
                                str(json_str["data"][0]["nearCount"]) + "/" +
                                str(json_str["data"][0]["errorCount"]) + "\n" +
                                json_str["data"][0]["clearTypeName"] + "  " +
                                timeDelta(json_str["data"][0]["gameDate"])
                                ) + "[CQ:at,qq=" + qq + "]"
        await session.send(a)


@on_command('.bind', aliases=('.bind', '.b'), only_to_me=False)
async def get_captcha(session: CommandSession):
    qq = str(session.ctx['user_id'])
    url = 'https://iot.universal-space.cn/api/sms/captcha/get/'
    phone = session.current_arg_text.strip()

    # 更新数据库中的手机
    conn = sqlite3.connect(database)
    c = conn.cursor()
    try:
        old_phone = str(c.execute('SELECT phone FROM info WHERE qq = (?)', (qq,)).fetchone()[0])
        if old_phone:
            c.execute("UPDATE info SET phone = '%s' WHERE QQ = %s;" % (phone, qq))
    except:
        c.execute(r"INSERT INTO info (qq,phone) VALUES (%s,%s);" % (qq, phone))
    finally:
        conn.commit()
        requests.post(url + phone)
        await session.send("已请求验证码，认证指令：\n.a 验证码")
        conn.close()


@on_command('.auth', aliases=('.auth', '.a'), only_to_me=False)
async def auth_captcha(session: CommandSession):
    qq = str(session.ctx['user_id'])
    url = 'https://iot.universal-space.cn/api/unis/Myself/loginUser?mobile='
    captcha = str(session.current_arg_text.strip())

    conn = sqlite3.connect(database)
    c = conn.cursor()
    a = ""
    try:
        phone = str(c.execute('SELECT phone FROM info WHERE qq = (?)', (qq,)).fetchone()[0])
        if phone:
            response = requests.post(url + phone + "&captcha=" + captcha)
            s = json.loads(response.text)
            print(s)
            if s["retCode"] in [404, 103]:
                a = "绑定失败，可能是验证码错误"
            else:
                token = (s["data"]["token"])
                c.execute("UPDATE info SET token = '%s' WHERE QQ = %s;" % (token, qq))
                conn.commit()
                a = "绑定成功"
        else:
            a = "请先发送验证码。命令：\n.b 手机号"
    finally:
        await session.send(a)
        conn.close()
