from pathlib2 import Path
import json
import requests
from urllib.parse import quote
import aiohttp
import asyncio
import logging

# 初始化日志配置
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)
fileHandler = logging.FileHandler('runtime.log', 'a', 'utf-8')
fileHandler.setLevel(logging.DEBUG)

formatter4Stream = logging.Formatter(
    '%(asctime)s : %(message)s',
    '%H:%M:%S')
formatter4File = logging.Formatter(
    '%(levelname)-8s - %(asctime)s(%(name)s):\n%(message)s',
    '%Y-%m-%d %H:%M:%S')

streamHandler.setFormatter(formatter4Stream)
fileHandler.setFormatter(formatter4File)

logger.addHandler(streamHandler)
logger.addHandler(fileHandler)

# 初始化，读取配置文件
CONFIG_FILE = './setting.json'
if not Path(CONFIG_FILE).exists():
    raise Exception('当前目录下，不存在setting.json配置文件')
with open(CONFIG_FILE, "r", encoding='utf-8') as f:
    SETTING = json.load(f)

logger.info('=' * 30 + '配置文件' + '=' * 30)
logger.info(json.dumps(SETTING, indent=2, sort_keys=True))
logger.info('=' * 65)

# 初始化AK索引
AK_INDEX = -1
# 复制AK列表，初始化无效列表
AK_VALID = SETTING['apiKey'].copy()
AK_INVALID = []
# 初始AK总数
AK_AMOUNT = len(AK_VALID)


def getAK(invalidate=False, invalidAK=None):
    '''
    获取、更换AK
    '''
    global AK_VALID
    global AK_INDEX

    if invalidate:
        if invalidAK:
            ak = invalidAK
        else:
            ak = AK_VALID[AK_INDEX]
        logger.info(
            f'AK:{ak}失效。剩余{len(AK_VALID)-1}个AK'
        )
        AK_INVALID.append(ak)
        if ak in AK_VALID:
            AK_VALID.remove(ak)
        AK_INDEX = -1
    if len(AK_VALID) == 0:
        raise Exception("AK耗尽")

    AK_INDEX += 1
    AK_INDEX %= len(AK_VALID)
    key = AK_VALID[AK_INDEX]

    return key

# 输出AK信息


def akInfo(detail=False):
    '''
    输出AK信息
    '''
    global AK_INDEX
    global AK_VALID
    global AK_INVALID
    global AK_AMOUNT

    logger.info('=' * 30 + 'AK信息' + '=' * 30)
    logger.info(
        '总数/有效/无效：' + f'{AK_AMOUNT} / {len(AK_VALID)} / {len(AK_INVALID)}')
    if detail:
        logger.info('有效AK:\n' + '\n'.join([f'\t{ak}' for ak in AK_VALID]))
        logger.info('无效AK:\n' + '\n'.join([f'\t{ak}' for ak in AK_INVALID]))
    logger.info('=' * 65)


session = requests.Session()


def baiduApi(url, retry=0):
    '''
    添加AK，请求百度API，并处理异常
    一般来说有三种错误
    1、请求是网络原因造成连接失败，自动重新请求
    2、解析json出现异常，重新请求没用，抛出异常
    3、解析json后，AK访问限制，更换AK并重新请求
    '''
    # 超过重试次数
    if retry >= 5:
        logger.info('请求次数超过5次，放弃请求')
        return None

    # 添加AK的url
    url_ak = url + f'&ak={getAK()}'

    # 网络连接
    try:
        res = session.get(url_ak)
    except Exception as e:
        logger.exception(e)
        logger.info(f'请求API接口时发生异常，重试:{retry+1}次')
        return baiduApi(url, retry+1)

    # json解析
    try:
        res = json.loads(res.text)
    except Exception as e:
        logger.info('=' * 30 + 'json文本解析出现异常' + '=' * 30)
        logger.info(url)
        logger.info(res.text)
        logger.info(e)
        logger.info('=' * 65)
        # raise Exception()
        return None

    # AK、请求状态
    if res['status'] != 0:
        '''
        错误代码：
        http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-geocoding-abroad

        201:APP被用户自己禁用
        210:APP IP校验失败
        240:APP服务被禁用
        302:天配额
        401:并发
        '''
        # 如果是并发限制，重新请求
        if res['status'] == 401:
            return baiduApi(url)
        # 如果是AK限制，更换AK
        elif res['status'] == 4 or res['status'] == 302 \
                or res['status'] == 240 or res['status'] == 201 \
                or res['status'] == 401 or res['status'] == 210:
            getAK(True)
            return baiduApi(url)
        # 服务器内部错误，重新请求
        elif res['status'] == 1:
            logger.info('服务器内部错误，重新请求')
            return baiduApi(url, retry+1)
        # 其他不明原因
        else:
            logger.info('=' * 30 + '其他原因错误' + '=' * 30)
            logger.info(url_ak)
            logger.info(res)
            logger.info('=' * 65)
            # raise Exception('返回结果出错')
            return None

    return res


sessionAsync = None


async def baiduApiAsync(url, retry=0):
    '''
    添加AK，请求百度API，并处理异常
    一般来说有三种错误
    1、请求是网络原因造成连接失败，自动重新请求
    2、解析json出现异常，重新请求没用，抛出异常
    3、解析json后，AK访问限制，更换AK并重新请求
    '''
    # 超过重试次数
    if retry >= 5:
        logger.info('请求次数超过5次，放弃请求')
        logger.info(url)
        return None

    # 添加AK的url
    ak = getAK()
    url_ak = url + f'&ak={ak}'

    # 网络连接
    try:
        # async with aiohttp.ClientSession() as session:
        #     async with session.get(url_ak) as resp:
        #         text = await resp.text()
        async with sessionAsync.get(url_ak) as resp:
            text = await resp.text()

    except Exception as e:
        logger.exception(e)
        logger.info(f'请求API接口时发生异常，重试:{retry+1}次')
        return await baiduApiAsync(url, retry+1)

    # json解析
    try:
        res = json.loads(text)
    except Exception as e:
        logger.info('=' * 30 + 'json文本解析出现异常' + '=' * 30)
        logger.info(url)
        logger.info(res.text)
        logger.info(e)
        logger.info('=' * 65)
        # raise Exception()
        return None

    # AK、请求状态
    if res['status'] != 0:
        '''
        错误代码：
        http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-geocoding-abroad

        201:APP被用户自己禁用
        210:APP IP校验失败
        240:APP服务被禁用
        302:天配额
        401:并发
        '''
        # 如果是并发限制，重新请求
        if res['status'] == 401:
            return await baiduApiAsync(url)
        # 如果是AK限制，更换AK
        elif res['status'] == 4 or res['status'] == 302 \
                or res['status'] == 240 or res['status'] == 201 \
                or res['status'] == 401 or res['status'] == 210:
            getAK(True, ak)
            return await baiduApiAsync(url)
        # 服务器内部错误，重新请求
        elif res['status'] == 1:
            logger.info('服务器内部错误，重新请求')
            return await baiduApiAsync(url, retry+1)
        # 其他不明原因
        else:
            logger.info('=' * 30 + '其他原因错误' + '=' * 30)
            logger.info(url_ak)
            logger.info(res)
            logger.info('=' * 65)
            # raise Exception('返回结果出错')
            return None

    return res


def fetchApi(ori_loc, dest_loc):
    url = (
        f'http://api.map.baidu.com/routematrix/v2/walking?output=json&'
        f'origins={",".join([format(loc,".5f") for loc in reversed(ori_loc)])}&'
        f'destinations={",".join([format(loc,".5f") for loc in reversed(dest_loc)])}'
    )

    return baiduApi(url)


def reverseGeocode(ori_loc):
    url = ('http://api.map.baidu.com/reverse_geocoding/v3/?output=json&'
           f'coordtype=wgs84ll&'
           f'location={",".join([format(loc,".5f") for loc in reversed(ori_loc)])}')
    return baiduApi(url)


def geocode(geo_name, city):
    url = (
        f'http://api.map.baidu.com/geocoding/v3/?address={quote(geo_name)}'
        f'&city={city}&output=json'
    )
    return baiduApi(url)


async def geocodeAsync(geo_name, city):
    url = (
        f'http://api.map.baidu.com/geocoding/v3/?address={quote(geo_name)}'
        f'&city={city}&output=json'
    )
    return await baiduApiAsync(url)


async def initSessionAsync():
    global sessionAsync
    sessionAsync = aiohttp.ClientSession()

# 模块引入时，手动关闭


async def closeSessionAsync():
    await sessionAsync.close()

if __name__ == "__main__":
    # 模块被加载时，初始化Session
    asyncio.run(initSessionAsync())

    # asyncio.run(geocodeAsync('武汉大学', '武汉'))

    # 主程序运行时，主动关闭
    asyncio.run(closeSessionAsync())
    pass
else:
    akInfo(detail=True)
