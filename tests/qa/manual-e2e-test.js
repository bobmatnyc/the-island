/**
 * Manual E2E Testing Script
 * This script manually tests the live application
 *
 * Run with: node manual-e2e-test.js
 */

const https = require('https');
const fs = require('fs');

const BASE_URL = 'https://the-island.ngrok.app';
const REPORT_FILE = '/Users/masa/Projects/epstein/tests/qa/test-report.md';

console.log('🚀 Starting Manual E2E Testing\n');
console.log(`📋 Testing URL: ${BASE_URL}\n`);

// Test utilities
function makeRequest(path) {
  return new Promise((resolve, reject) => {
    const url = `${BASE_URL}${path}`;
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    }).on('error', reject);
  });
}

async function runTests() {
  const results = {
    passed: [],
    failed: [],
    warnings: []
  };

  console.log('=' .repeat(60));
  console.log('TEST 1: Home Page Accessibility');
  console.log('=' .repeat(60));

  try {
    const homeRes = await makeRequest('/');
    if (homeRes.status === 200) {
      console.log('✅ Home page loaded successfully');
      console.log(`   Status: ${homeRes.status}`);
      console.log(`   Content-Type: ${homeRes.headers['content-type']}`);
      console.log(`   Body length: ${homeRes.body.length} bytes\n`);
      results.passed.push('Home page loads (HTTP 200)');

      // Check for unified timeline & news card
      if (homeRes.body.includes('Timeline') && homeRes.body.includes('News')) {
        console.log('✅ Timeline & News content found in home page');
        results.passed.push('Timeline & News content present');
      } else {
        console.log('⚠️  Timeline & News content may not be visible');
        results.warnings.push('Timeline & News content unclear');
      }
    } else {
      console.log(`❌ Home page returned status: ${homeRes.status}\n`);
      results.failed.push(`Home page HTTP ${homeRes.status}`);
    }
  } catch (error) {
    console.log(`❌ Home page test failed: ${error.message}\n`);
    results.failed.push(`Home page error: ${error.message}`);
  }

  console.log('=' .repeat(60));
  console.log('TEST 2: Timeline Page');
  console.log('=' .repeat(60));

  try {
    const timelineRes = await makeRequest('/timeline');
    if (timelineRes.status === 200) {
      console.log('✅ Timeline page loaded successfully');
      console.log(`   Status: ${timelineRes.status}`);
      console.log(`   Body length: ${timelineRes.body.length} bytes\n`);
      results.passed.push('Timeline page loads (HTTP 200)');

      if (timelineRes.body.includes('news') || timelineRes.body.includes('News')) {
        console.log('✅ News content found in timeline page');
        results.passed.push('News content in timeline');
      }
    } else {
      console.log(`❌ Timeline page returned status: ${timelineRes.status}\n`);
      results.failed.push(`Timeline page HTTP ${timelineRes.status}`);
    }
  } catch (error) {
    console.log(`❌ Timeline page test failed: ${error.message}\n`);
    results.failed.push(`Timeline page error: ${error.message}`);
  }

  console.log('=' .repeat(60));
  console.log('TEST 3: Flights Page');
  console.log('=' .repeat(60));

  try {
    const flightsRes = await makeRequest('/flights');
    if (flightsRes.status === 200) {
      console.log('✅ Flights page loaded successfully');
      console.log(`   Status: ${flightsRes.status}`);
      console.log(`   Body length: ${flightsRes.body.length} bytes\n`);
      results.passed.push('Flights page loads (HTTP 200)');
    } else {
      console.log(`❌ Flights page returned status: ${flightsRes.status}\n`);
      results.failed.push(`Flights page HTTP ${flightsRes.status}`);
    }
  } catch (error) {
    console.log(`❌ Flights page test failed: ${error.message}\n`);
    results.failed.push(`Flights page error: ${error.message}`);
  }

  console.log('=' .repeat(60));
  console.log('TEST 4: API Endpoints');
  console.log('=' .repeat(60));

  const apiEndpoints = [
    '/api/entities',
    '/api/news',
    '/api/flights'
  ];

  for (const endpoint of apiEndpoints) {
    try {
      const apiRes = await makeRequest(endpoint);
      if (apiRes.status === 200) {
        console.log(`✅ API ${endpoint} - HTTP ${apiRes.status}`);
        results.passed.push(`API ${endpoint} accessible`);
      } else if (apiRes.status === 404) {
        console.log(`⚠️  API ${endpoint} - HTTP ${apiRes.status} (may use different path)`);
        results.warnings.push(`API ${endpoint} returned 404`);
      } else {
        console.log(`❌ API ${endpoint} - HTTP ${apiRes.status}`);
        results.failed.push(`API ${endpoint} HTTP ${apiRes.status}`);
      }
    } catch (error) {
      console.log(`⚠️  API ${endpoint} - ${error.message}`);
      results.warnings.push(`API ${endpoint} error`);
    }
  }

  console.log('\n' + '=' .repeat(60));
  console.log('TEST SUMMARY');
  console.log('=' .repeat(60));
  console.log(`✅ Passed: ${results.passed.length}`);
  console.log(`❌ Failed: ${results.failed.length}`);
  console.log(`⚠️  Warnings: ${results.warnings.length}`);
  console.log('=' .repeat(60) + '\n');

  // Generate report
  generateReport(results);
}

function generateReport(results) {
  const now = new Date().toISOString();
  let report = `# E2E Test Report\n\n`;
  report += `**Test Date:** ${now}\n`;
  report += `**Test URL:** ${BASE_URL}\n\n`;

  report += `## Summary\n\n`;
  report += `- ✅ Passed: ${results.passed.length}\n`;
  report += `- ❌ Failed: ${results.failed.length}\n`;
  report += `- ⚠️ Warnings: ${results.warnings.length}\n\n`;

  if (results.passed.length > 0) {
    report += `## Passed Tests\n\n`;
    results.passed.forEach(test => {
      report += `- ✅ ${test}\n`;
    });
    report += `\n`;
  }

  if (results.failed.length > 0) {
    report += `## Failed Tests\n\n`;
    results.failed.forEach(test => {
      report += `- ❌ ${test}\n`;
    });
    report += `\n`;
  }

  if (results.warnings.length > 0) {
    report += `## Warnings\n\n`;
    results.warnings.forEach(test => {
      report += `- ⚠️ ${test}\n`;
    });
    report += `\n`;
  }

  fs.writeFileSync(REPORT_FILE, report);
  console.log(`📄 Report saved to: ${REPORT_FILE}\n`);
}

// Run tests
runTests().catch(console.error);
