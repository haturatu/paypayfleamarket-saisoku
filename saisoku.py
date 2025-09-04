import asyncio
from playwright.async_api import async_playwright
import os
import sys
import logging
from dotenv import load_dotenv
import re
import html

load_dotenv()

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("saisoku.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
logger.addHandler(console_handler)


async def auth_mode(profile_path):
    login_url = "https://login.yahoo.co.jp/config/login"
    logging.info("認証モード: headless=False でブラウザ起動")
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--lang=ja-JP"
            ]
        )
        page = await browser.new_page()
        logging.info(f"Yahooログインページを開きます: {login_url}")
        await page.goto(login_url)
        logging.info("ログインしてください。完了後、ブラウザを閉じるとスクリプトが終了します。")
        while True:
            await asyncio.sleep(200)
        await browser.close()


async def main():
    if len(sys.argv) < 2:
        logging.error("Usage: python main.py <URL|auth> [auth]")
        return

    arg = sys.argv[1]
    auth_flag = arg.lower() == "auth"

    user_data_dir = os.getenv("USER_DATA_DIR")
    profile_dir = os.getenv("PROFILE_DIR", "Default")

    if not user_data_dir:
        logging.error("環境変数 USER_DATA_DIR が設定されていません (.env を確認してください)")
        return

    profile_path = os.path.join(user_data_dir, profile_dir)

    if auth_flag:
        await auth_mode(profile_path)
        return

    url = arg
    async with async_playwright() as p:
        logging.info("ブラウザ起動中...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--lang=ja-JP"
            ]
        )

        page = await browser.new_page()
        logging.info(f"ページへアクセス中... {url}")
        await page.goto(url)

        logging.info("DOMの内容を取得...")
        content = await page.content()

        # 「すべての取引が完了しました」がある場合はスキップ
        if "すべての取引が完了しました" in content:
            logging.warning("取引完了済み → メッセージ送信をスキップ")
        else:
            # DOM内からヤマト配送リンクを正規表現で抽出
            links = re.findall(r'href="(https://toi\.kuronekoyamato\.co\.jp/cgi-bin/tneko[^"]+)"', content)
            links = [html.unescape(link) for link in links]

            logging.info(f"見つかったヤマト配送リンク: {links}")

            should_send_message = True  # デフォルトは送信する

            for link in links:
                try:
                    logging.info(f"配送状況チェック: {link}")
                    # Playwrightで新しいタブを開いて配送ページへアクセス
                    track_page = await browser.new_page()
                    await track_page.goto(link)
                    track_content = await track_page.content()
                    await track_page.close()

                    if "配達完了" in track_content:
                        logging.info("配達完了済み → 受取連絡がされていない場合メッセージ送信対象")
                        should_send_message = True
                    else:
                        logging.info("まだ配達されていません → メッセージ送信スキップ")
                        should_send_message = False
                        break
                except Exception as e:
                    logging.error(f"配送リンク取得エラー: {e}")
                    should_send_message = False
                    break

            if should_send_message:
                message = (
                    "配達完了後に受取連絡を行われない場合が多発しているため、"
                    "受取連絡されていない取引に関して自動で送付しております。受取連絡を行ってください。"
                )
                logging.info("メッセージを入力中...")
                await page.fill('textarea[placeholder="メッセージを入力"]', message)

                logging.info("「取引メッセージを送る」ボタンをクリック...")
                await page.click('button[type="button"]:has-text("取引メッセージを送る")')
                logging.info("✅ メッセージを送信しました。")
            else:
                logging.info("条件に合わないためメッセージ送信をスキップ")

        await asyncio.sleep(5)
        logging.info("ブラウザを閉じます。")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

