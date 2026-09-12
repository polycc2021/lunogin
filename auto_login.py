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
    except Exception as e:
        print(f"发送 Telegram 通知出错: {e}")

def run():
    if not USERNAME or not PASSWORD:
        msg = "❌ <b>Betadash 自动登录失败</b>\n未配置 PANEL_USERNAME 或 PANEL_PASSWORD 环境变量。"
        print(msg)
        send_telegram_msg(msg)
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()

        print("正在访问 Betadash 首页...")
        try:
            # 更改为直接访问根域名，由面板自行重定向至正确登录页
            page.goto("https://betadash.lunes.host/", timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"页面加载警告: {e}")

        print(f"当前页面标题: {page.title()}")
        print(f"跳转后 URL: {page.url}")

        # 检查 Cloudflare 防护
        if "Just a moment" in page.title() or "Cloudflare" in page.title():
            fail_msg = "⚠️ <b>Betadash 面板自动登录失败</b>\n遇到了 Cloudflare 人机验证盾，无头浏览器被拦截。"
            print(fail_msg)
            send_telegram_msg(fail_msg)
            sys.exit(1)

        try:
            print("正在寻找输入框...")
            username_input = page.locator('input[name="username"], input[name="email"], input[name="user"], input[name="username_or_email"], input[type="text"], input[type="email"]').first
            password_input = page.locator('input[name="password"], input[type="password"]').first

            # 显式等待输入框渲染
            username_input.wait_for(state="visible", timeout=20000)

            print("正在填写账号密码...")
            username_input.fill(USERNAME)
            password_input.fill(PASSWORD)

            print("提交登录...")
            submit_button = page.locator('button[type="submit"], input[type="submit"], button:has-text("Log in"), button:has-text("Login")').first
            submit_button.click()

            page.wait_for_timeout(6000)

            current_url = page.url
            print(f"登录后 URL: {current_url}")

            # 只要不在登录相关路径且能访问面板首页/服务器列表即视作成功
            if "login" not in current_url.lower() and "auth" not in current_url.lower():
                success_msg = "🎉 <b>Betadash 面板自动登录成功</b>\n项目已成功刷取活跃状态。"
                print("登录成功！已保持活跃状态。")
                send_telegram_msg(success_msg)
            else:
                fail_msg = f"⚠️ <b>Betadash 面板自动登录失败</b>\n页面仍停留在登录页 ({current_url})，请检查账号密码是否正确。"
                print("登录失败，页面未跳转。")
                send_telegram_msg(fail_msg)
                sys.exit(1)

        except Exception as e:
            error_msg = f"⚠️ <b>Betadash 面板自动登录异常</b>\n未能在页面找到输入框或操作超时。\n当前页面标题: {page.title()}\n当前 URL: {page.url}\n错误: {e}"
            print(error_msg)
            send_telegram_msg(error_msg)
            sys.exit(1)

        finally:
            browser.close()

if __name__ == "__main__":
    run()
