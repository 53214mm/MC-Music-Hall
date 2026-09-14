// Static artifact checks only; this is not a replacement for browser rendering.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
for (const file of process.argv.slice(2)) {
  const html = fs.readFileSync(file, 'utf8');
  const ids = new Set([...html.matchAll(/id="([^"]+)"/g)].map(m => m[1]));
  let references = 0;
  for (const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    new vm.Script(match[1], { filename: file });
    const refs = [...match[1].matchAll(/\$\('([^']+)'\)/g)].map(m => m[1]);
    const missing = [...new Set(refs)].filter(id => !ids.has(id));
    if (missing.length) throw new Error(`Missing DOM IDs: ${missing}`);
    references += refs.length;
  }
  for (const [,href] of html.matchAll(/href="([^"]+)"/g)) {
    if (/^(https?:|#)/.test(href)) continue;
    const target = path.resolve(path.dirname(file),decodeURIComponent(href));
    if (!fs.existsSync(target)) throw new Error(`Missing local link: ${href}`);
  }
  console.log(`${path.basename(file)}: syntax, ${references} literal DOM references and local links OK.`);
}
