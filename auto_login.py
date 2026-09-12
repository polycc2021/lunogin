import os
import sys
import json
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("PANEL_USERNAME")
PASSWORD = os.environ.get("PANEL_PASSWORD")
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
            else:
                print(f"Telegram 通知发送失败，状态码: {response.status}")
    except Exception as e:
        print(f"发送 Telegram 通知出错: {e}")

def run():
    if not USERNAME or not PASSWORD:
        msg = "❌ <b>Betadash 自动登录失败</b>\n未配置 PANEL_USERNAME 或 PANEL_PASSWORD 环境变量。"
        print(msg)
        send_telegram_msg(msg)
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("正在打开登录页面...")
        page.goto("https://betadash.lunes.host/auth/login", timeout=60000)
        page.wait_for_load_state("networkidle")

        print("正在填写账号密码...")
        username_input = page.locator('input[name="username"], input[name="email"], input[name="user"]').first
        password_input = page.locator('input[name="password"]').first

        username_input.fill(USERNAME)
        password_input.fill(PASSWORD)

        print("提交登录...")
        page.locator('button[type="submit"], input[type="submit"]').first.click()

        page.wait_for_timeout(5000)

        current_url = page.url
        print(f"当前页面 URL: {current_url}")

        if "auth/login" not in current_url:
            success_msg = "🎉 <b>Betadash 面板自动登录成功</b>\n项目已成功刷取活跃状态。"
            print("登录成功！已保持活跃状态。")
            send_telegram_msg(success_msg)
        else:
            fail_msg = "⚠️ <b>Betadash 面板自动登录失败</b>\n页面停留在登录页，可能触发了验证码或密码有误。"
            print("登录可能失败，请检查账号密码或是否触发验证码机制。")
            send_telegram_msg(fail_msg)
            sys.exit(1)

        browser.close()

if __name__ == "__main__":
    run()