import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.goto('http://localhost:5174');
  await page.waitForTimeout(3000);
  
  const storage = await page.evaluate(() => ({
    token: localStorage.getItem('jaaz_access_token'),
    userInfo: localStorage.getItem('jaaz_user_info'),
  }));
  
  console.log('localStorage:', JSON.stringify(storage, null, 2));
  
  await browser.close();
})();
