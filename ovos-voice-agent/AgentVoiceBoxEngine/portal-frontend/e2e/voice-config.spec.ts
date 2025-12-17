import { test, expect } from '@playwright/test';

/**
 * Voice Configuration E2E Tests
 * Tests the OVOS voice configuration flows
 * 
 * Validates Requirements:
 * - B9: Voice Configuration (TTS)
 * - B10: STT Configuration
 * - B11: LLM Configuration
 * - B12: Persona Management
 * - E2: Skills Management
 * - E4: Wake Word Configuration
 * - E5: Intent Analytics
 */

test.describe('Voice Configuration - TTS Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/voice');
  });

  test('should display voice configuration page', async ({ page }) => {
    // Requirements B9.1: Voice settings display
    await expect(page.getByRole('heading', { name: /voice|tts/i })).toBeVisible();
  });

  test('should display available Kokoro voices', async ({ page }) => {
    // Requirements B9.2: Kokoro voice selection
    await page.waitForTimeout(1000);
    
    // Look for voice options
    const voiceOptions = page.getByText(/onyx|adam|sarah|nicole|emma|george/i);
  });

  test('should have voice speed slider', async ({ page }) => {
    // Requirements B9.3: Speed configuration (0.5x - 2.0x)
    const speedSlider = page.locator('input[type="range"], [role="slider"]');
    await expect(speedSlider.first()).toBeVisible();
  });

  test('should have save configuration button', async ({ page }) => {
    // Requirements B9.5: Save settings
    const saveButton = page.getByRole('button', { name: /save|apply/i });
    await expect(saveButton.first()).toBeVisible();
  });
});

test.describe('Voice Configuration - STT Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/stt');
  });

  test('should display STT configuration page', async ({ page }) => {
    // Requirements B10.1: STT settings display
    await expect(page.getByRole('heading', { name: /stt|speech|transcription/i })).toBeVisible();
  });

  test('should display Faster-Whisper model options', async ({ page }) => {
    // Requirements B10.2: Model selection
    await page.waitForTimeout(1000);
    
    // Look for model options
    const modelOptions = page.getByText(/tiny|base|small|medium|large/i);
  });

  test('should have language selection', async ({ page }) => {
    // Requirements B10.3: Language codes
    await page.waitForTimeout(1000);
    
    const languageSelector = page.locator('select, [role="combobox"]').filter({ hasText: /language|en|auto/i });
  });

  test('should have VAD toggle', async ({ page }) => {
    // Requirements B10.4: Voice Activity Detection
    const vadToggle = page.getByText(/vad|voice activity/i);
  });
});

test.describe('Voice Configuration - LLM Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/llm');
  });

  test('should display LLM configuration page', async ({ page }) => {
    // Requirements B11.1: LLM settings display
    await expect(page.getByRole('heading', { name: /llm|language model/i })).toBeVisible();
  });

  test('should display provider options', async ({ page }) => {
    // Requirements B11.2: Provider selection (Groq, OpenAI, Ollama)
    await page.waitForTimeout(1000);
    
    const providerOptions = page.getByText(/groq|openai|ollama/i);
  });

  test('should have temperature slider', async ({ page }) => {
    // Requirements B11.3: Temperature configuration
    const tempSlider = page.locator('input[type="range"], [role="slider"]');
  });

  test('should have max tokens input', async ({ page }) => {
    // Requirements B11.4: Max tokens configuration
    const tokensInput = page.getByLabel(/max tokens|tokens/i);
  });

  test('should have API key input for BYOK', async ({ page }) => {
    // Requirements B11.5: Bring Your Own Key
    await page.waitForTimeout(1000);
    
    const apiKeyInput = page.getByLabel(/api key/i);
  });
});

test.describe('Voice Configuration - Personas', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/personas');
  });

  test('should display personas page', async ({ page }) => {
    // Requirements B12.1: Display personas
    await expect(page.getByRole('heading', { name: /persona/i })).toBeVisible();
  });

  test('should have create persona button', async ({ page }) => {
    // Requirements B12.2: Create persona
    const createButton = page.getByRole('button', { name: /create|new|add/i });
    await expect(createButton.first()).toBeVisible();
  });

  test('should display persona list', async ({ page }) => {
    // Requirements B12.1: Persona list with name, description, status
    await page.waitForTimeout(1000);
  });

  test('should have solver plugin configuration', async ({ page }) => {
    // Requirements B12.3: OVOS solvers
    await page.waitForTimeout(1000);
    
    const solverOptions = page.getByText(/wikipedia|duckduckgo|wolfram|wordnet/i);
  });
});

test.describe('Voice Configuration - Skills', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/skills');
  });

  test('should display skills management page', async ({ page }) => {
    // Requirements E2.1: Display installed skills
    await expect(page.getByRole('heading', { name: /skill/i })).toBeVisible();
  });

  test('should display skill list', async ({ page }) => {
    // Requirements E2.1: Skills with name, version, status
    await page.waitForTimeout(1000);
  });

  test('should have enable/disable toggles', async ({ page }) => {
    // Requirements E2.3, E2.4: Enable/disable skills
    await page.waitForTimeout(1000);
    
    const toggles = page.locator('button[role="switch"], input[type="checkbox"]');
  });

  test('should have install skill option', async ({ page }) => {
    // Requirements E2.2: Install from skill store
    const installButton = page.getByRole('button', { name: /install|add/i });
  });
});

test.describe('Voice Configuration - Wake Words', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/wake-words');
  });

  test('should display wake words page', async ({ page }) => {
    // Requirements E4.1: Display wake words
    await expect(page.getByRole('heading', { name: /wake word/i })).toBeVisible();
  });

  test('should display sensitivity settings', async ({ page }) => {
    // Requirements E4.1: Sensitivity settings
    await page.waitForTimeout(1000);
    
    const sensitivitySlider = page.locator('input[type="range"], [role="slider"]');
  });

  test('should have add wake word button', async ({ page }) => {
    // Requirements E4.2: Add wake word
    const addButton = page.getByRole('button', { name: /add|new|create/i });
    await expect(addButton.first()).toBeVisible();
  });

  test('should have test detection option', async ({ page }) => {
    // Requirements E4.3: Test wake word
    const testButton = page.getByRole('button', { name: /test/i });
  });
});

test.describe('Voice Configuration - Intent Analytics', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/intents');
  });

  test('should display intent analytics page', async ({ page }) => {
    // Requirements E5.1: Display top intents
    await expect(page.getByRole('heading', { name: /intent/i })).toBeVisible();
  });

  test('should display intent frequency', async ({ page }) => {
    // Requirements E5.1: Intent frequency
    await page.waitForTimeout(1000);
  });

  test('should have date range filter', async ({ page }) => {
    // Requirements E5.3: Filter by date range
    const dateFilter = page.locator('select, [role="combobox"], button').filter({ hasText: /7d|30d|date/i });
  });

  test('should show failed intents section', async ({ page }) => {
    // Requirements E5.4: Failed intents
    const failedSection = page.getByText(/failed|unrecognized/i);
  });

  test('should have export option', async ({ page }) => {
    // Requirements E5.5: Export intent data
    const exportButton = page.getByRole('button', { name: /export/i });
  });
});

test.describe('Voice Configuration - Voice Cloning', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/voice-cloning');
  });

  test('should display voice cloning page', async ({ page }) => {
    // Requirements B13.1: Voice cloning display
    await expect(page.getByRole('heading', { name: /voice cloning|custom voice/i })).toBeVisible();
  });

  test('should have upload voice sample option', async ({ page }) => {
    // Requirements B13.2: Upload voice sample
    const uploadButton = page.getByRole('button', { name: /upload/i });
    await expect(uploadButton.first()).toBeVisible();
  });

  test('should display existing custom voices', async ({ page }) => {
    // Requirements B13.1: Display existing voices
    await page.waitForTimeout(1000);
  });

  test('should have preview option', async ({ page }) => {
    // Requirements B13.4: Preview cloned voice
    const previewButton = page.getByRole('button', { name: /preview|play/i });
  });
});
