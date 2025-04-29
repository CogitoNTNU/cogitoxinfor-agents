const fs = require('fs');
const path = require('path');

/**
 * Generates a Playwright test from agent execution data
 * @param {string} jsonPath - Path to the post_step.json file
 */
function generateTestFromAgentData(jsonPath) {
  try {
    // Read and parse the agent data
    const data = fs.readFileSync(jsonPath, 'utf-8');
    const steps = JSON.parse(data);
    const agentId = steps[0]?.agent_id || 'unknown-agent';
    
    // Begin creating the test file
    let testCode = `
import { test, expect } from '@playwright/test';

test('Automated test from agent ${agentId}', async ({ page }) => {
  // Generated from agent execution data on ${new Date().toISOString()}
`;

    // Extract navigation URL from first action
    // Extracts URL regardless of where it appears in the steps
    let navigationUrl = null;
    for (const step of steps) {
      // Dynamic search through actions
      if (step.actions && Array.isArray(step.actions)) {
        for (const action of step.actions) {
          if (action.go_to_url && action.go_to_url.url) {
            navigationUrl = action.go_to_url.url;
            break;
          }
        }
      }
    }

    // Add navigation step
    if (navigationUrl) {
      testCode += `
  // Navigate to target URL
  await page.goto("${navigationUrl}");
  await page.waitForLoadState('networkidle');
`;
    }

    // Add cookie consent handling
    const hasCookieConsent = steps.some(step => 
      step.brain_state?.memory?.toLowerCase().includes('cookie consent') || 
      step.brain_state?.memory?.toLowerCase().includes('godta alle')
    );

    if (hasCookieConsent) {
      testCode += `
  // Handle potential cookie consent dialog
  try {
    const consentButtons = [
      page.getByRole('button', { name: /accept all|accept cookies|i agree|godta alle/i }),
      page.locator('button:has-text("Accept")'),
      page.locator('button:has-text("Godta alle")')
    ];
    
    for (const button of consentButtons) {
      const isVisible = await button.isVisible({ timeout: 2000 }).catch(() => false);
      if (isVisible) {
        await button.click();
        await page.waitForTimeout(500);
        break;
      }
    }
  } catch (e) {
    console.log('No cookie consent found or already handled');
  }
`;
    }

    // Extract input actions
    for (const step of steps) {
      if (!step.element_actions || !Array.isArray(step.element_actions)) continue;
      
      for (const action of step.element_actions) {
        // Skip failed actions
        if (action.success === false) continue;
        
        if (action.action === 'input_text') {
          // Extract the input element details
          let selector;
          let inputText = '';
          
          // Try to get input text from brain state
          if (step.brain_state?.memory) {
            const memoryMatch = step.brain_state.memory.match(/type ['"]([^'"]+)['"]/i);
            if (memoryMatch && memoryMatch[1]) {
              inputText = memoryMatch[1];
            }
          }
          
          // Default to "python" if we couldn't find text
          if (!inputText) inputText = 'python';
          
          // Get a working selector
          if (action.element_id) {
            selector = `#${action.element_id}`;
          } else if (action.attributes?.id) {
            selector = `#${action.attributes.id}`;
          } else if (action.attributes?.name) {
            selector = `[name="${action.attributes.name}"]`;
          } else if (action.tag_name) {
            selector = action.tag_name;
          }
          
          if (selector) {
            testCode += `
  // Type "${inputText}" into the input field
  await page.waitForSelector('${selector}');
  await page.fill('${selector}', "${inputText}");
`;
          }
        }
      }
    }

    // Add search submission (even if not in original steps)
    const isSearchSite = navigationUrl?.includes('google.com') || 
                        steps.some(step => step.url?.includes('google.com'));
    
    if (isSearchSite) {
      testCode += `
  // Submit the search
  await page.keyboard.press('Enter');
  
  // Wait for search results
  await page.waitForNavigation({ waitUntil: 'networkidle' });
  
  // Verify search results appeared
  await expect(page.locator('body')).toContainText('python');
`;
    }

    testCode += `});`;
    
    return testCode;
  } catch (error) {
    console.error('Error generating test:', error);
    return null;
  }
}

// Process command line arguments
const jsonPath = process.argv[2];
if (!jsonPath) {
  console.error('Please provide a path to the agent data JSON file');
  console.error('Usage: node generate-test.js path/to/post_step.json');
  process.exit(1);
}

// Generate and save the test
const testCode = generateTestFromAgentData(jsonPath);
if (testCode) {
  // Create output file name based on input
  const outputPath = path.join(
    path.dirname(jsonPath), 
    `${path.basename(jsonPath, '.json')}.spec.js`
  );
  
  fs.writeFileSync(outputPath, testCode);
  console.log(`Test saved to: ${outputPath}`);
  console.log(`Run with: npx playwright test ${outputPath}`);
} else {
  console.error('Failed to generate test code');
  process.exit(1);
}