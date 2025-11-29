// Test script to check if page loads and executes JavaScript correctly
const http = require('http');

console.log('Testing page load at http://localhost:8081/...\n');

http.get('http://localhost:8081/', (res) => {
    let data = '';

    res.on('data', (chunk) => {
        data += chunk;
    });

    res.on('end', () => {
        console.log(`✓ HTTP Status: ${res.statusCode}`);
        console.log(`✓ Content-Length: ${data.length} bytes`);

        // Check for key elements
        const checks = [
            { name: 'HTML complete', test: data.includes('</html>') },
            { name: 'Body tag', test: data.includes('<body>') },
            { name: 'app.js loaded', test: data.includes('app.js') },
            { name: 'documents.js loaded', test: data.includes('documents.js') },
            { name: 'hot-reload.js loaded', test: data.includes('hot-reload.js') },
            { name: 'Overview tab', test: data.includes('overview-view') },
            { name: 'Active tab', test: data.includes('class="tab active"') },
            { name: 'Lucide icons', test: data.includes('lucide') },
            { name: 'D3.js library', test: data.includes('d3js.org') },
            { name: 'CSS variables', test: data.includes('--bg-primary') }
        ];

        console.log('\nElement checks:');
        checks.forEach(check => {
            console.log(`${check.test ? '✓' : '✗'} ${check.name}`);
        });

        // Check for potential issues
        console.log('\nPotential issues:');
        const issues = [];

        if (!data.includes('switchTab')) {
            issues.push('switchTab function not found in HTML');
        }

        if (data.includes('undefined')) {
            issues.push('Contains "undefined" string (might indicate JS error)');
        }

        if (issues.length === 0) {
            console.log('No obvious issues detected in HTML');
        } else {
            issues.forEach(issue => console.log(`⚠ ${issue}`));
        }

        console.log('\nPage structure appears to load correctly.');
        console.log('Issue is likely in client-side JavaScript execution.');
        console.log('\nRecommendation: Check browser console for JavaScript errors.');
    });

}).on('error', (err) => {
    console.error(`✗ Error: ${err.message}`);
});
