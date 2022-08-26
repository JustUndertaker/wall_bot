import asyncio
import random
import time
from typing import Optional

from httpx import AsyncClient, Cookies
from nonebot import get_bots


class QQZoneScanqr:
    """扫码QQ空间"""

    client: AsyncClient
    """请求客户端"""
    cookies: Cookies
    """保存的cookies"""
    xlogin_url: str
    """xlogin_url"""
    qrshow_url: str
    """qrshow_url"""
    qrlogin_url: str
    """qrlogin_url"""
    is_connecting: bool
    """是否正在连接"""

    def __init__(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"
        }
        self.xlogin_url = "https://xui.ptlogin2.qq.com/cgi-bin/xlogin?"
        self.qrshow_url = "https://ssl.ptlogin2.qq.com/ptqrshow?"
        self.qrlogin_url = "https://ssl.ptlogin2.qq.com/ptqrlogin?"
        self.client = AsyncClient(headers=headers)
        self.cookies = Cookies()
        self.is_connecting = False

    def _decryptQrsig(self, qrsig: str) -> int:
        e = 0
        for c in qrsig:
            e += (e << 5) + ord(c)
        return 2147483647 & e

    async def login(self, user_id: int) -> Optional[bytes]:
        """
        说明:
            尝试登录空间，并返回二维码图片

        参数:
            * `user_id`：交互用户

        返回:
            * `bytes`：二维码图片bytes
        """
        if self.is_connecting:
            return None
        self.is_connecting = True
        # 先清理cookies
        self.cookies.clear()
        params = {
            "proxy_url": "https://qzs.qq.com/qzone/v6/portal/proxy.html",
            "daid": "5",
            "hide_title_bar": "1",
            "low_login": "0",
            "qlogin_auto_login": "1",
            "no_verifyimg": "1",
            "link_target": "blank",
            "appid": "549000912",
            "style": "22",
            "target": "self",
            "s_url": "https://qzs.qq.com/qzone/v5/loginsucc.html?para=izone",
            "pt_qr_app": "手机QQ空间",
            "pt_qr_link": "https://z.qzone.com/download.html",
            "self_regurl": "https://qzs.qq.com/qzone/v6/reg/index.html",
            "pt_qr_help_link": "https://z.qzone.com/download.html",
            "pt_no_auth": "0",
        }
        response = await self.client.get(url=self.xlogin_url, params=params)
        # 获得ptqrtoken
        params = {
            "appid": "549000912",
            "e": "2",
            "l": "M",
            "s": "3",
            "d": "72",
            "v": "4",
            "t": str(random.random()),
            "daid": "5",
            "pt_3rd_aid": "0",
        }
        self.cookies.update(response.cookies)
        pt_login_sig = self.cookies["pt_login_sig"]
        # 获得ptqrtoken
        params = {
            "appid": "549000912",
            "e": "2",
            "l": "M",
            "s": "3",
            "d": "72",
            "v": "4",
            "t": str(random.random()),
            "daid": "5",
            "pt_3rd_aid": "0",
        }
        response = await self.client.get(
            url=self.qrshow_url, params=params, cookies=self.cookies
        )
        self.cookies.update(response.cookies)

        ptqrtoken = self._decryptQrsig(self.cookies["qrsig"])
        # 检测二维码状态
        asyncio.create_task(self._check(ptqrtoken, pt_login_sig, user_id))
        return response.content

    async def _check(self, ptqrtoken: str, pt_login_sig: str, user_id: int):
        """检测二维码状态"""
        while True:
            params = {
                "u1": "https://qzs.qq.com/qzone/v5/loginsucc.html?para=izone",
                "ptqrtoken": ptqrtoken,
                "ptredirect": "0",
                "h": "1",
                "t": "1",
                "g": "1",
                "from_ui": "1",
                "ptlang": "2052",
                "action": "0-0-" + str(int(time.time())),
                "js_ver": "19112817",
                "js_type": "1",
                "login_sig": pt_login_sig,
                "pt_uistyle": "40",
                "aid": "549000912",
                "daid": "5",
                "ptdrvs": "AnyQUpMB2syC5zV6V4JDelrCvoAMh-HP6Xy5jvKJzHBIplMBK37jV1o3JjBWmY7j*U1eD8quewY_",
                "has_onekey": "1",
            }
            response = await self.client.get(
                url=self.qrlogin_url, params=params, cookies=self.cookies
            )
            if "登录成功" in response.text:
                self.cookies.update(response.cookies)
                for _, bot in get_bots().items():
                    await bot.call_api(
                        "send_private_msg", user_id=user_id, message="登录成功！"
                    )
                break
            elif "二维码已经失效" in response.text:
                for _, bot in get_bots().items():
                    await bot.call_api(
                        "send_private_msg", user_id=user_id, message="二维码已失效！"
                    )
                break
            await asyncio.sleep(2)
        self.is_connecting = False
