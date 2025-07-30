import requests


def get_answer(query, conversation_id="", user="admin"):
    """
    发送聊天消息到API，返回answer值

    Args:
        query (str): 外部传入的查询内容
        conversation_id (str): 会话ID，默认为空
        user (str): 用户名，默认为admin

    Returns:
        str: API响应中的answer值，如果出错返回None
    """

    url = "https://agent.sxteyou.com/v1/chat-messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer app-tx6unSm19dlRBCFlOnJClyay"
    }

    payload = {
        "input_data": {},
        "query": query,
        "mode": "blocking",
        "conversation_id": conversation_id,
        "user": user,
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("answer")

    except Exception as e:
        print(f"请求错误: {e}")
        return None


if __name__ == "__main__":
    query = "【中国农业银行】验证码：669149，有效期5分钟，您正在登录掌上银行，请勿泄露或转发他人，谨防资金被骗。如您当前未使用掌银，请联系我行客服95599。"
    answer = get_answer(query)
    print(answer)  # 输出: 926029
