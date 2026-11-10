import sys, pathlib
from playwright.sync_api import sync_playwright
here = pathlib.Path(__file__).parent.resolve()
with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')
    pg = b.new_page(viewport={'width':1440,'height':810})
    pg.goto((here/'trustmesh-ptit.html').as_uri())
    pg.wait_for_timeout(500)
    pg.pdf(path=str(here/'TrustMesh_PTIT.pdf'), width='1440px', height='810px', print_background=True)
    n = pg.evaluate("document.querySelectorAll('section.s').length")
    for i in range(n):
        el = pg.query_selector_all('section.s')[i]
        el.screenshot(path=str(here/f'p{i+1:02d}.png'))
    b.close()
print('done')
