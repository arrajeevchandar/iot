// Optional external acceptance test: requires trusted HTTPS access to Wokwi.
// Uses an unsaved public template; never publishes a project or credentials.
const {chromium: playwright} = require('playwright');
const chromium = require('@sparticuz/chromium').default;
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');

(async () => {
  const browser = await playwright.launch({executablePath: await chromium.executablePath(), args: chromium.args, headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 1600, height: 1000}});
    await page.goto('https://wokwi.com/projects/305457271083631168', {waitUntil: 'domcontentloaded', timeout: 60000});
    await page.waitForFunction(() => window.monaco?.editor?.getModels().length);
    await page.getByText('diagram.json', {exact: true}).click();
    await page.waitForFunction(() => window.monaco.editor.getModels().some(m => m.getLanguageId() === 'json'));
    await page.evaluate(diagram => window.monaco.editor.getModels().find(m => m.getLanguageId() === 'json').setValue(diagram), fs.readFileSync(path.join(root, 'wokwi/diagram.json'), 'utf8'));
    await page.waitForTimeout(1500);
    const chooser = page.waitForEvent('filechooser');
    const upload = page.evaluate(() => window.monaco.editor.getEditors()[0].getSupportedActions().find(a => /^Upload Firmware/.test(a.label)).run());
    await (await chooser).setFiles(path.join(root, 'runtime/classroom-esp32dev.bin'));
    await upload;
    const serial = page.locator('[class*=serialMonitor]');
    async function expectState(needles) {
      await page.waitForFunction(expected => {
        const text = document.querySelector('[class*=serialMonitor]')?.innerText || '';
        const latest = text.slice(text.lastIndexOf('=== SMART CLASSROOM ==='));
        return expected.every(s => latest.includes(s));
      }, needles, {timeout: 60000});
      console.log('Passed:', needles.join(' / '));
    }
    async function selectPart(selector) {
      // Close a sensor popup before selecting another part it might overlap.
      await page.locator('wokwi-esp32-devkit-v1').click();
      await page.locator(selector).click();
    }
    await expectState(['TinyML EMPTY', 'L1 0 L2 0 Fan 0', 'sensor OK']);
    await page.screenshot({path: path.join(root, 'screenshots/wokwi-initial.png')});
    await selectPart('wokwi-dht22');
    await page.locator('input[type=range][min="-40"]').fill('46');
    await expectState(['T 46.0', 'Vent 180 Alarm 1', 'TinyML ABNORMAL_CONDITION']);
    await page.screenshot({path: path.join(root, 'screenshots/wokwi-emergency.png')});
    await page.locator('input[type=range][min="-40"]').fill('31');
    await selectPart('wokwi-photoresistor-sensor');
    await page.locator('input[type=range][min="-1"]').fill('0');
    await expectState(['T 31.0', 'Light 3.8%', 'Vent 0 Alarm 0']);
    await selectPart('wokwi-pir-motion-sensor');
    await page.getByRole('button', {name: 'Simulate motion', exact: true}).click();
    await expectState(['OCCUPIED | AUTO', 'L1 1 L2 1 Fan 1', 'Power 100.0 W']);
    await page.screenshot({path: path.join(root, 'screenshots/wokwi-occupied.png')});
    await page.locator('wokwi-esp32-devkit-v1').click();
    await page.locator('wokwi-potentiometer input[type=range]').fill('970', {force: true});
    await expectState(['Air 94.8', 'Vent 180 Alarm 1', 'Alert CRITICAL']);
    await page.screenshot({path: path.join(root, 'screenshots/wokwi-air-emergency.png')});
    fs.writeFileSync(path.join(root, 'report/wokwi_serial.log'), await serial.innerText());
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
