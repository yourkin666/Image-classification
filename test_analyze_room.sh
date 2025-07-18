#!/bin/bash
# 测试 analyze_room 接口的脚本

# 设置服务URL
SERVICE_URL="http://47.236.238.112/analyze_room"

# 发送测试请求
curl -X POST \
  $SERVICE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://ts1.cn.mm.bing.net/th/id/R-C.29f9d485da9120569fe4d577698d19a6?rik=j4mWHYKyS8IiBQ&riu=http%3a%2f%2fwww.hifidiy.net%2fpics%2f2008%2f04%2f20080428_106035_71166.jpg&ehk=XeJQaUWTjFFX1PuOFg4nsNrPjSXaHk2x5ycPVXZASaM%3d&risl=&pid=ImgRaw&r=0",
    "include_description": true
  }'

echo -e "\n\n访问方式说明:"
echo "1. 通过POST请求访问 http://47.236.238.112/analyze_room"
echo "2. 设置Content-Type为application/json"
echo "3. 请求体格式如下:"
echo '{
  "url": "图片URL地址或图片URL地址数组", 
  "include_description": true或false
}'
echo "4. 返回结果包含图片是否为房间及房间类型的分析"
