# 全国三甲医院名称、地址、经纬度
- 源数据来自：http://www.a-hospital.com/w/%E5%85%A8%E5%9B%BD%E4%B8%89%E7%94%B2%E5%8C%BB%E9%99%A2%E5%90%8D%E5%8D%95
- 在浏览器中执行snippet.js代码，输出Json字符串
- 手动编辑部分，并进行地理编码
- 广东药学院附属第一医院激光整形美容中心（广州铁路中心医院激光整形美容中心）手动复制上一行经纬度
- 两个部队医院无法解析经纬度
  - 缺省经纬度：0.0,0.0

# 文件说明
- snipper_result.json
  - 网页输出Json
- result.csv
  - 地理编码结果

# 引用声明
- 该项目使用Apache-2.0协议
- 使用该数据请声明数据来源：Luoyun, https://github.com/46319943/3AHospital