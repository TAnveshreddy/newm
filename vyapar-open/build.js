/* Builds dist/VyaparOpen.html — the single-file standalone app — from index.html + css/ + js/.
   Usage: node build.js  (run inside vyapar-open/) */
'use strict';
const fs = require('fs');
const path = require('path');
process.chdir(__dirname);

let html = fs.readFileSync('index.html', 'utf8');
const css = fs.readFileSync('css/style.css', 'utf8');
html = html.replace('<link rel="stylesheet" href="css/style.css">', '<style>\n' + css + '\n</style>');

const scripts = ['utils.js', 'store.js', 'parties.js', 'items.js', 'txns.js', 'import.js', 'billing.js', 'reports.js', 'dashboard.js', 'settings.js', 'sync.js', 'app.js'];
let js = scripts.map(s => fs.readFileSync(path.join('js', s), 'utf8')).join('\n\n');
js = js.replace(/<\/script>/g, '<\\/script>'); // don't terminate the inline script tag early

html = html.replace(/(\s*<script src="js\/[a-z]+\.js"><\/script>)+/g, () => '\n  <script>\n' + js + '\n  </script>');

fs.mkdirSync('dist', { recursive: true });
fs.writeFileSync(path.join('dist', 'Shopkeeper.html'), html);
// identical copy named index.html so static hosts (Netlify, GitHub Pages) serve the site root
fs.writeFileSync(path.join('dist', 'index.html'), html);
console.log('Built dist/Shopkeeper.html + dist/index.html (' + fs.statSync('dist/Shopkeeper.html').size + ' bytes)');
