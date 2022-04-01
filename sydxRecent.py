import datetime
import json
import os
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


def get_diff_name(music_id, diff_number):
    diff_str = ""
    if diff_number == 0:
        diff_str = "NOV"
    if diff_number == 1:
        diff_str = "ADV"
    if diff_number == 2:
        diff_str = "EXH"
    if diff_number == 4:
        diff_str = "MXM"
    if diff_number == 3:
        conn = sqlite3.connect(database)
        c = conn.cursor()
        c.execute('select infver from diffinfo where ID = (?)', (music_id,))
        diff_str = c.fetchone()[0]
    return diff_str


def get_music(string):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('select id,name from diffinfo where name like "%%%s%%" order by id DESC' % string)
    music = c.fetchone()
    return music


@on_command('.find', aliases=('.find', '.f'), only_to_me=False)
async def get_recent_score(session: CommandSession):
    qq = str(session.ctx['user_id'])
    input_str = session.current_arg_text.strip()
    if not input_str:
        conn = sqlite3.connect(database)
        c = conn.cursor()
        c.execute('SELECT * FROM diffinfo ORDER BY RANDOM() limit 1')
        music = c.fetchone()
        img_file = "jk_" + str(music[0]).zfill(4) + "_3.png"
        if os.path.exists(r'/usr/bot/httpserver/img/' + img_file):
            img_url = "http://127.0.0.1/img/jk_" + str(music[0]).zfill(4) + "_" + str(3) + ".png"
        else:
            img_url = "http://127.0.0.1/img/jk_" + str(music[0]).zfill(4) + "_" + str(1) + ".png"
        await session.send("[CQ:at,qq=" + qq + "]随机抽到的歌曲是：" + music[2] + "[CQ:image,file=" + str(img_url)
                           + "]")

    else:
        img_file = "jk_" + str(get_music(input_str)[0]).zfill(4) + "_3.png"
        if os.path.exists(r'/usr/bot/httpserver/img/' + img_file):
            img_url = "http://127.0.0.1/img/jk_" + str(get_music(input_str)[0]).zfill(4) + "_" + str(
                3) + ".png"
        else:
            img_url = "http://127.0.0.1/img/jk_" + str(get_music(input_str)[0]).zfill(4) + "_" + str(
                1) + ".png"
        print(str(get_music(input_str)))
        await session.send("您要找的歌曲是不是：" + get_music(input_str)[1] + "[CQ:image,file=" + str(img_url)
                           + "]")


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
    try:
        num = int(session.current_arg_text.strip())
    except:
        num = 3
    if not num:
        num = 3
    elif num > 6:
        num = 6

    # 获取成绩json
    url = 'https://iot.universal-space.cn/api/mns/mnsGame/recordList?productId=3084&pageNo=1&pageSize=' + str(
        num) + '&orderBy' \
               '=gameDate '
    playdata = requests.get(url, headers={'token': token})
    json_str = playdata.json()
    if json_str["code"] == 403:
        await session.send(get_new_token(qq))
    else:

        # json处理和发送最终生成的成绩
        i = 0
        a = "[CQ:at,qq=" + qq + "]" + "最近的" + str(num) + "条游戏记录："
        while i < num:
            a += "\n" + (str(json_str["data"][i]["musicName"]) + "[" +
                         get_diff_name(json_str["data"][i]["musicId"], json_str["data"][i]["musicGrade"])
                         + "]\n" +
                         str(json_str["data"][i]["score"]) + "  " +
                         json_str["data"][i]["clearTypeName"] + "  " +
                         timeDelta(json_str["data"][i]["gameDate"])
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
    elif json_str["pageSize"] == 0:
        await session.send("数字过大， 你可能还没有玩那么多首歌")
    else:
        # json处理和发送最终生成的成绩，包含了图片
        score = json_str["data"][0]

        img_file = "jk_" + str(score["musicId"]).zfill(4) + "_" + str(
            score["musicGrade"] + 1) + ".png"
        print(img_file)
        if os.path.exists(r'/usr/bot/httpserver/img/' + img_file):
            img_url = "http://127.0.0.1/img/jk_" + str(score["musicId"]).zfill(4) + "_" + str(
                score["musicGrade"] + 1) + ".png"
        else:
            img_url = "http://127.0.0.1/img/jk_" + str(score["musicId"]).zfill(4) + "_" + str(
                1) + ".png"
        print(img_url)
        a = "[CQ:image,file=" + str(img_url
                                    + "]" +
                                    str(score["musicName"]) + "[" +
                                    get_diff_name(score["musicId"], score["musicGrade"])
                                    + "]\n" +
                                    str(score["score"]) + "  " +
                                    str(score["criticalCount"]) + "/" +
                                    str(score["nearCount"]) + "/" +
                                    str(score["errorCount"]) + "\n" +
                                    score["clearTypeName"] + "  " +
                                    timeDelta(json_str["data"][0]["gameDate"])
                                    ) + "  [CQ:at,qq=" + qq + "]"
        print('\n\n' + a + '\n\n')
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
