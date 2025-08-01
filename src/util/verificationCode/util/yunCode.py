import base64

import requests


def verify():
    with open('captcha_screenshot.png', 'rb') as f:
        b = base64.b64encode(f.read()).decode()  ## 图片二进制流base64字符串

    url = "http://api.jfbym.com/api/YmServer/customApi"
    data = {
        ## 关于参数,一般来说有3个;不同类型id可能有不同的参数个数和参数名,找客服获取
        "token": "gXPC0JwRWjEpdGZphzOzDHgCoJvpIPYf5igLg8U7afA",
        "type": "20225",
        "image": b,
    }
    _headers = {
        "Content-Type": "application/json"
    }
    response = requests.request("POST", url, headers=_headers, json=data).json()

    # 检查请求是否成功
    if response.get("code") == 10000 and response.get("msg") == "识别成功":
        # 提取data.data字段的值
        result = response.get("data", {}).get("data")
        print(f"识别结果: {result}")
        return result
    elif response.get("code") == 10002:
        print('余额不足')
        return None
    else:
        print(f"识别失败: {response}")
        return None


if __name__ == '__main__':
    captcha_code = verify()
    if captcha_code:
        print(f"验证码是: {captcha_code}")
