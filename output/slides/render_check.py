# Chụp các slide ở trạng thái cuối. Chạy: python -m http.server 8766 (trong output/), rồi python render_check.py <thư-mục-ảnh> 1,2,3 [ms-chờ]
import os, sys, asyncio
from playwright.async_api import async_playwright

EXE = os.path.expandvars(r'%LOCALAPPDATA%\ms-playwright\chromium_headless_shell-1243\chrome-headless-shell-win64\chrome-headless-shell.exe')
OUT = sys.argv[1]
NS = [int(x) for x in sys.argv[2].split(',')]
WAIT = int(sys.argv[3]) if len(sys.argv) > 3 else 6500


async def one(b, n):
    p = await b.new_page(viewport={'width': 1600, 'height': 900})
    await p.goto(f'http://localhost:8766/slides/trustmesh-deck.html?x={n}#{n}')
    await p.wait_for_timeout(WAIT)
    await p.screenshot(path=f'{OUT}/s{n:02d}.jpg', type='jpeg', quality=80)
    await p.close()


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=EXE)
        await asyncio.gather(*[one(b, n) for n in NS])
        await b.close()

asyncio.run(main())
