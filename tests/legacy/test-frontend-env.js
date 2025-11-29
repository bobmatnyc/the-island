// Test script to verify frontend environment variable
const fetch = require('node-fetch');

async function testFrontendEnv() {
  try {
    // Fetch the main page
    const response = await fetch('http://localhost:5173/');
    const html = await response.text();

    console.log('=== Frontend Environment Test ===\n');

    // Check for old URL
    if (html.includes('e25a8b2fa7a5.ngrok.app')) {
      console.log('❌ ERROR: Old ngrok URL (e25a8b2fa7a5) found in HTML!');
    } else {
      console.log('✅ SUCCESS: Old ngrok URL not found in HTML');
    }

    // Check for new URL
    if (html.includes('the-island.ngrok.app')) {
      console.log('✅ SUCCESS: New ngrok URL (the-island) found in HTML');
    } else {
      console.log('⚠️  INFO: New URL not in initial HTML (expected - it\'s in JS modules)');
    }

    // Fetch a JavaScript module to check env var
    const mainResponse = await fetch('http://localhost:5173/src/services/newsApi.ts');
    const mainJs = await mainResponse.text();

    if (mainJs.includes('VITE_API_BASE_URL')) {
      console.log('✅ SUCCESS: VITE_API_BASE_URL reference found in source');
    }

    console.log('\n=== Environment Variable Configuration ===');
    console.log('Expected: VITE_API_BASE_URL=https://the-island.ngrok.app');
    console.log('Frontend should use this URL for all API calls');

    console.log('\n=== Next Steps ===');
    console.log('1. Open browser to http://localhost:5173/');
    console.log('2. Open browser console (F12)');
    console.log('3. Check Network tab for API calls');
    console.log('4. Verify API calls use: https://the-island.ngrok.app');

  } catch (error) {
    console.error('Error testing frontend:', error.message);
  }
}

testFrontendEnv();
