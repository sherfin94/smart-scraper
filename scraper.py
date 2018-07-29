import asyncio
from pyppeteer import launch
import pandas as pd
from sys import argv

async def getdata(url):
    browser = await launch()
    page = await browser.newPage()
    await page.setViewport({'width':1024, 'height': 768})
    await page.goto(url)
    # Take screenshot for debugging
    await page.screenshot({'path': 'screen.png', 'fullPage': True})

    # Pass JavaScript code, to be executed inside chromium console
    data = await page.evaluate(
    '''
     () => {
        let elements = [
          ...document.querySelectorAll('*')
        ];
        return elements.map(element => {
             const text = element.textContent.trim()
             var record = {}
             const bBox = element.getBoundingClientRect()
             // Fetching font size only for text having small length
             // This is done for better performance
             if(text.length <= 30 && !(bBox.x == 0 && bBox.y == 0)) {
                record['fontSize'] = getComputedStyle(element)['fontSize']
             }
             record['y'] = bBox.y
             record['x'] = bBox.x
             record['text'] = text
             return record
        })
     }
    ''')
    await browser.close()
    return data

url = argv[1]
records = asyncio.get_event_loop().run_until_complete(getdata(url))
df = pd.DataFrame(records)
df = df[~df.text.isna()] # we don't need elements without text content
df = df[~df.fontSize.isna()] # we don't need elements whose font size was not obtained
df.fontSize = df.fontSize.apply(lambda font_size: float(font_size[:-2]))

df = df[df.y < 700]

price_regex = '(^(US ){0,1}(rs\.|Rs\.|RS\.|\$|₹|INR|USD|CAD|C\$){0,1}(\s){0,1}[\d,]+(\.\d+){0,1}(\s){0,1}(AED){0,1}$)'
df = df[df.text.str.match(price_regex)]

df = df.sort_values(by=['fontSize','y'], ascending=[False, True]) # Sorting by font size, followed by height

print(df.text.iloc[0])
