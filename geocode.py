import asyncio
from baidumapapi import geocodeAsync, initSessionAsync, closeSessionAsync
import json
import pandas as pd
from trans_util import bd09_to_wgs84
import re


async def main():
    '''
    根据snipper_result.json文件中的address、name字段进行地理编码
    将结果以WGS84坐标相应字段进行添加，导出为UTF-8编码的CSV
    '''
    df = pd.read_json('snipper_result.json')

    geocode_name_list = df[['address', 'name']].fillna(
        '').agg(' '.join, axis=1).values

    await initSessionAsync()

    loc_list = []
    for loc_name in geocode_name_list:

        # 处理过长的名称
        if len(loc_name) > 30:
            loc_name = re.sub(r'（.*?）', '', loc_name)
        if len(loc_name) > 30:
            loc_name = re.sub(r'[；;，,].*', '', loc_name)
            
        result = await geocodeAsync(loc_name, '')

        if result is None:
            loc_list.append([0, 0])
            continue

        loc = [result['result']['location']['lng'],
               result['result']['location']['lat']]
        loc = bd09_to_wgs84(*loc)
        loc_list.append(loc)

    await closeSessionAsync()

    lon = [loc[0] for loc in loc_list]
    lat = [loc[1] for loc in loc_list]

    df['longitude_wgs84'] = lon
    df['latitude_wgs84'] = lat

    df.to_csv('result.csv', index=False, encoding='UTF-8')

asyncio.run(main())
