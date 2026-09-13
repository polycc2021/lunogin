import os
import sys
import json
import urllib.request
import requests

SESSION_COOKIE = os.environ.get("PANEL_COOKIE")
TG_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    """发送 Telegram 消息通知"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("提示: 未配置 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID，跳过电报通知。")
        return

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("Telegram 通知发送成功！")
    except Exception as e:
        print(f"发送 Telegram 通知出错: {e}")

def run():
    if not SESSION_COOKIE:
        msg = "❌ <b>Betadash 活跃保鲜失败</b>\n未配置 PANEL_COOKIE 环境变量。"
        print(msg)
        send_telegram_msg(msg)
        sys.exit(1)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cookie": f"pterodactyl_session={SESSION_COOKIE}"  # 如果 cookie 名称不同，可修改此处
    }

    url = "https://betadash.lunes.host/"

    print("正在携带 Cookie 访问面板首页...")
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        
        print(f"响应状态码: {response.status_code}")
        print(f"最终 URL: {response.url}")

        # 判断是否保持在登录后的状态
        if response.status_code == 200 and "auth/login" not in response.url.lower():
            success_msg = "🎉 <b>Betadash 面板 Session 维持成功</b>\n成功访问控制面板，账号活跃状态已更新。"
            print("Session 维持成功！已更新活跃状态。")
            send_telegram_msg(success_msg)
        else:
            fail_msg = f"⚠️ <b>Betadash 面板 Session 已失效</b>\n请求重定向至登录页（{response.url}），请重新在本地登录并更新 PANEL_COOKIE。"
            print("Session 可能已失效。")
            send_telegram_msg(fail_msg)
            sys.exit(1)

    except Exception as e:
        error_msg = f"⚠️ <b>Betadash 面板请求异常</b>\n请求出错: {e}"
        print(error_msg)
        send_telegram_msg(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    run()