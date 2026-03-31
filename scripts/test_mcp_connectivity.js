#!/usr/bin/env node

/**
 * Test MCP connectivity for OpenCode configuration
 * This script tests each MCP server configured in opencode.json
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const opencodePath = path.join(__dirname, '..', 'opencode.json');
const opencodeConfig = JSON.parse(fs.readFileSync(opencodePath, 'utf8'));

console.log('🔍 Testing MCP connectivity for OpenCode configuration');
console.log(`📁 Config file: ${opencodePath}`);
console.log(`📊 Servers configured: ${Object.keys(opencodeConfig.mcpServers || {}).length}\n`);

const servers = opencodeConfig.mcpServers || {};

// Test each server
Object.entries(servers).forEach(([name, config]) => {
  console.log(`🧪 Testing ${name}...`);
  
  if (config.command) {
    console.log(`   Command: ${config.command}`);
    
    // Check if command exists
    const cmdParts = config.command.split(' ');
    const mainCmd = cmdParts[0];
    
    try {
      // Simple test - check if command exists
      require('child_process').execSync(`which ${mainCmd}`, { stdio: 'pipe' });
      console.log(`   ✅ Command exists: ${mainCmd}`);
    } catch (e) {
      console.log(`   ❌ Command not found: ${mainCmd}`);
    }
  }
  
  if (config.args) {
    console.log(`   Args: ${config.args.join(' ')}`);
  }
  
  if (config.url) {
    console.log(`   URL: ${config.url}`);
    // Try to ping the URL
    const https = require('https');
    const url = new URL(config.url);
    
    const req = https.request({
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname,
      method: 'HEAD',
      timeout: 5000
    }, (res) => {
      console.log(`   ✅ HTTP ${res.statusCode}: ${config.url}`);
    });
    
    req.on('error', (err) => {
      console.log(`   ❌ Connection failed: ${err.message}`);
    });
    
    req.on('timeout', () => {
      console.log(`   ⏱️  Timeout connecting to ${config.url}`);
      req.destroy();
    });
    
    req.end();
  }
  
  console.log('');
});

// Test Supabase connection from .env
const envPath = path.join(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  console.log('🔑 Testing Supabase credentials from .env...');
  const envContent = fs.readFileSync(envPath, 'utf8');
  const envVars = envContent.split('\n').filter(line => line.trim() && !line.startsWith('#'));
  
  const supabaseUrl = envVars.find(line => line.includes('SUPABASE_URL'));
  const supabaseKey = envVars.find(line => line.includes('SUPABASE_SERVICE_ROLE_KEY'));
  
  if (supabaseUrl && supabaseKey) {
    console.log('   ✅ SUPABASE_URL found');
    console.log('   ✅ SUPABASE_SERVICE_ROLE_KEY found');
    
    // Test Supabase connection
    const { createClient } = require('@supabase/supabase-js');
    const url = supabaseUrl.split('=')[1];
    const key = supabaseKey.split('=')[1];
    
    try {
      const supabase = createClient(url, key);
      // Simple query to test connection
      supabase.from('accounts').select('count', { count: 'exact', head: true })
        .then(response => {
          if (response.error) {
            console.log(`   ❌ Supabase query error: ${response.error.message}`);
          } else {
            console.log(`   ✅ Supabase connected successfully (accounts table exists)`);
          }
        })
        .catch(err => {
          console.log(`   ❌ Supabase connection error: ${err.message}`);
        });
    } catch (err) {
      console.log(`   ❌ Supabase client creation error: ${err.message}`);
    }
  } else {
    console.log('   ⚠️  Missing Supabase credentials in .env');
  }
}

console.log('\n📋 Summary:');
console.log('Run `npx @modelcontextprotocol/inspector` to interactively test MCP servers');
console.log('Or use OpenCode\'s built-in MCP tools via the agent swarm.');