/**
 * Node.js test for ES6 modules
 * Run with: node test-modules-node.mjs
 */

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('🧪 Testing Phase 1 Modules (Static Analysis)\n');

const tests = [];

// Test 1: Check all module files exist
const modules = [
    'core/state-manager.js',
    'core/event-bus.js',
    'utils/dom-cache.js',
    'utils/formatter.js',
    'utils/markdown.js',
    'components/toast.js'
];

console.log('📁 Checking module files...');
modules.forEach(module => {
    try {
        const path = join(__dirname, module);
        const content = readFileSync(path, 'utf8');
        const hasExport = content.includes('export');
        const hasClass = content.includes('class') || content.includes('function');

        console.log(`  ✅ ${module} (${content.split('\n').length} lines, ${hasExport ? 'exports' : 'no exports'})`);
        tests.push({ name: module, passed: hasExport && hasClass });
    } catch (error) {
        console.log(`  ❌ ${module} - Error: ${error.message}`);
        tests.push({ name: module, passed: false });
    }
});

// Test 2: Validate exports
console.log('\n📦 Validating exports...');

const expectedExports = {
    'core/state-manager.js': ['StateManager', 'appState'],
    'core/event-bus.js': ['EventBus', 'eventBus'],
    'utils/dom-cache.js': ['DOMCache', 'domCache', 'getElementById'],
    'utils/formatter.js': ['formatEntityName', 'escapeHtml', 'escapeForJS', 'formatDate'],
    'utils/markdown.js': ['loadMarkedJS', 'renderMarkdown'],
    'components/toast.js': ['Toast']
};

Object.entries(expectedExports).forEach(([module, exports]) => {
    try {
        const path = join(__dirname, module);
        const content = readFileSync(path, 'utf8');
        const allExist = exports.every(exp =>
            content.includes(`export class ${exp}`) ||
            content.includes(`export const ${exp}`) ||
            content.includes(`export function ${exp}`) ||
            content.includes(`export async function ${exp}`)
        );

        console.log(`  ${allExist ? '✅' : '❌'} ${module}: ${exports.join(', ')}`);
        tests.push({ name: `${module} exports`, passed: allExist });
    } catch (error) {
        console.log(`  ❌ ${module} - Error: ${error.message}`);
        tests.push({ name: `${module} exports`, passed: false });
    }
});

// Test 3: Check JSDoc comments
console.log('\n📝 Checking documentation...');
modules.forEach(module => {
    try {
        const path = join(__dirname, module);
        const content = readFileSync(path, 'utf8');
        const hasJSDoc = content.includes('/**');
        const jsdocCount = (content.match(/\/\*\*/g) || []).length;

        console.log(`  ${hasJSDoc ? '✅' : '⚠️'} ${module}: ${jsdocCount} JSDoc blocks`);
        tests.push({ name: `${module} docs`, passed: hasJSDoc });
    } catch (error) {
        console.log(`  ❌ ${module} - Error: ${error.message}`);
        tests.push({ name: `${module} docs`, passed: false });
    }
});

// Test 4: Check backward compatibility
console.log('\n🔄 Checking backward compatibility...');
const backwardCompat = {
    'core/state-manager.js': 'window.__appState',
    'utils/dom-cache.js': 'window.__domCache',
    'utils/formatter.js': 'window.__formatter',
    'components/toast.js': 'window.showToast'
};

Object.entries(backwardCompat).forEach(([module, windowVar]) => {
    try {
        const path = join(__dirname, module);
        const content = readFileSync(path, 'utf8');
        const hasCompat = content.includes(windowVar);

        console.log(`  ${hasCompat ? '✅' : '❌'} ${module}: ${windowVar}`);
        tests.push({ name: `${module} backward compat`, passed: hasCompat });
    } catch (error) {
        console.log(`  ❌ ${module} - Error: ${error.message}`);
        tests.push({ name: `${module} backward compat`, passed: false });
    }
});

// Test 5: Check file structure
console.log('\n📂 Checking file structure...');
const directories = ['core', 'utils', 'components'];
directories.forEach(dir => {
    try {
        const path = join(__dirname, dir);
        const exists = readFileSync(path + '/state-manager.js', 'utf8') || true;
        console.log(`  ✅ ${dir}/ directory exists`);
    } catch (error) {
        // Try other files in directory
        try {
            if (dir === 'core') readFileSync(join(__dirname, dir, 'event-bus.js'));
            if (dir === 'utils') readFileSync(join(__dirname, dir, 'formatter.js'));
            if (dir === 'components') readFileSync(join(__dirname, dir, 'toast.js'));
            console.log(`  ✅ ${dir}/ directory exists`);
        } catch (e) {
            console.log(`  ❌ ${dir}/ directory missing`);
        }
    }
});

// Summary
console.log('\n' + '='.repeat(60));
console.log('📊 Test Summary');
console.log('='.repeat(60));

const passed = tests.filter(t => t.passed).length;
const failed = tests.filter(t => !t.passed).length;
const total = tests.length;
const passRate = ((passed / total) * 100).toFixed(1);

console.log(`Total Tests: ${total}`);
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);
console.log(`Pass Rate: ${passRate}%`);

if (failed === 0) {
    console.log('\n✅ All static tests passed!');
    console.log('\n🎉 Phase 1 modules are ready for browser testing');
    console.log('\n📍 Next Steps:');
    console.log('  1. Start server: cd /Users/masa/Projects/epstein/server && python app.py');
    console.log('  2. Open browser: http://localhost:5001/test-refactoring-phase1.html');
    console.log('  3. Run interactive tests: http://localhost:5001/test-modules-simple.html');
} else {
    console.log('\n❌ Some tests failed. Review output above.');
    process.exit(1);
}
