import email
import imaplib
import time
from datetime import datetime, timedelta
from email.header import decode_header

from src.util.Agent import get_answer


class Email189VerificationTool:
    """189邮箱验证码获取工具类"""

    def __init__(self):
        """
        初始化邮箱连接信息
        """
        self.email_account = "17375743687@189.cn"
        self.email_password = "Pp$7Ky#2s=7Tm)2F"
        self.imap_server = "imap.189.cn"
        self.imap_port = 993

    def get_verification_code(self, tz_text, mail_time):
        """
        获取验证码邮件内容
        :param tz_text: 需要匹配的文本内容（为空则不匹配）
        :param mail_time: 邮件时间筛选基准（datetime对象）
        :return: get_answer的返回值，如果失败返回None
        """
        timeout_seconds = 120  # 2分钟超时
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                # 连接邮箱
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                mail.login(self.email_account, self.email_password)

                # 选择收件箱
                mail.select('inbox')

                # 搜索今天的邮件（避免中文编码问题，先获取所有今天的邮件再本地筛选）
                today = datetime.now().strftime("%d-%b-%Y")
                search_criteria = f'(SINCE "{today}")'
                result, data = mail.search(None, search_criteria)

                if result == 'OK' and data[0]:
                    email_ids = data[0].split()

                    # 存储符合条件的邮件（用于找到最新的一封）
                    valid_emails = []

                    # 从最新邮件开始检查，收集所有符合条件的邮件
                    for email_id in reversed(email_ids):
                        email_content = self._get_email_content(mail, email_id)
                        if email_content:
                            email_time, subject, body = email_content

                            # 检查邮件时间是否大于mail_time
                            if email_time > mail_time:
                                # 检查标题是否包含"验证码"
                                if "验证码" in subject:
                                    # 检查文本内容匹配条件
                                    if not tz_text or tz_text in body:
                                        # 找到符合条件的邮件，因为是从最新开始遍历，第一个就是最新的
                                        mail.close()
                                        mail.logout()
                                        return get_answer(body)

                mail.close()
                mail.logout()

            except Exception as e:
                print(f"邮箱连接或处理出错: {e}")

            # 等待5秒后重试
            time.sleep(5)

        print("获取验证码邮件超时（2分钟）")
        return None

    def _get_email_content(self, mail, email_id):
        """
        获取邮件内容
        :param mail: IMAP连接对象
        :param email_id: 邮件ID
        :return: (邮件时间, 标题, 正文内容) 或 None
        """
        try:
            result, data = mail.fetch(email_id, '(RFC822)')
            if result != 'OK':
                return None

            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)

            # 获取邮件时间（处理时区问题）
            date_str = email_message.get('Date')
            email_time = email.utils.parsedate_to_datetime(date_str)

            # 如果邮件时间有时区信息，转换为本地时间（去除时区信息）
            if email_time.tzinfo is not None:
                email_time = email_time.replace(tzinfo=None)

            # 获取标题
            subject = self._decode_header(email_message.get('Subject', ''))

            # 获取邮件正文
            body = self._get_email_body(email_message)

            return email_time, subject, body

        except Exception as e:
            print(f"解析邮件内容出错: {e}")
            return None

    def _decode_header(self, header):
        """解码邮件头部信息"""
        if not header:
            return ""

        decoded_parts = decode_header(header)
        decoded_string = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part

        return decoded_string

    def _get_email_body(self, email_message):
        """获取邮件正文内容"""
        body = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(email_message.get_payload())

        return body.strip()


if __name__ == "__main__":
    # 初始化工具
    email_tool = Email189VerificationTool()

    # 调用获取验证码
    mail_time = datetime.now() - timedelta(minutes=300)  # 1分钟前的时间
    result = email_tool.get_verification_code("", mail_time)

    if result:
        print(f"获取到验证码结果: {result}")
    else:
        print("未能获取到验证码")
