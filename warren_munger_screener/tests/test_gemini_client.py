import unittest
from unittest.mock import patch, MagicMock # Added MagicMock
from ..app.utils.gemini_client import GeminiClient
from ..app.config import GOOGLE_API_KEY # To check if placeholder is used

# Define a mock response structure that matches what genai.GenerativeModel().generate_content() might return
# This needs to align with how GeminiClient processes the response.
class MockGenAIResponse:
    def __init__(self, text_parts=None, prompt_feedback=None, candidates=None):
        self.parts = []
        if text_parts:
            for part_text in text_parts:
                mock_part = MagicMock()
                mock_part.text = part_text
                self.parts.append(mock_part)

        self.text = "".join(text_parts) if text_parts else "" # Keep .text for fallback if client uses it

        self.prompt_feedback = prompt_feedback
        # Simplified candidates structure for this mock
        if candidates is not None:
            self.candidates = candidates
        elif text_parts: # if we have text parts, assume a successful candidate
             mock_candidate = MagicMock()
             mock_candidate.finish_reason.name = "STOP"
             self.candidates = [mock_candidate]
        else: # if no text and no specific candidates, assume empty or problematic
            self.candidates = []


class TestGeminiClient(unittest.TestCase):

    def setUp(self):
        # This setup runs for each test method
        self.sample_text = "This is a sample text to be summarized."
        self.api_key_to_use = "TEST_API_KEY" # Use a fake key for most tests

        # Patch genai.configure and genai.GenerativeModel for all tests in this class
        # to avoid actual API calls unless specifically intended.
        self.patcher_configure = patch('warren_munger_screener.app.utils.gemini_client.genai.configure')
        self.patcher_model = patch('warren_munger_screener.app.utils.gemini_client.genai.GenerativeModel')

        self.mock_genai_configure = self.patcher_configure.start()
        self.mock_genai_model_class = self.patcher_model.start()

        # Configure the mock model class to return a mock model instance
        self.mock_model_instance = MagicMock()
        self.mock_genai_model_class.return_value = self.mock_model_instance


    def tearDown(self):
        self.patcher_configure.stop()
        self.patcher_model.stop()

    def test_initialization_with_valid_key(self):
        client = GeminiClient(api_key=self.api_key_to_use)
        self.mock_genai_configure.assert_called_once_with(api_key=self.api_key_to_use)
        self.mock_genai_model_class.assert_called_once_with('gemini-pro')
        self.assertTrue(client.api_key_configured)
        self.assertIsNotNone(client.model)

    def test_initialization_with_placeholder_key_from_config(self):
        # Temporarily set GOOGLE_API_KEY to placeholder for this test if it's not already
        # This test assumes the default GOOGLE_API_KEY from config is "YOUR_API_KEY_HERE"
        with patch('warren_munger_screener.app.utils.gemini_client.GOOGLE_API_KEY', "YOUR_API_KEY_HERE"):
            client = GeminiClient() # Relies on the config
            self.mock_genai_configure.assert_not_called() # Should not try to configure
            self.assertFalse(client.api_key_configured)
            self.assertIsNone(client.model) # Model should not be set

    def test_initialization_failure_on_configure(self):
        self.mock_genai_configure.side_effect = Exception("Configuration failed")
        client = GeminiClient(api_key=self.api_key_to_use)
        self.assertFalse(client.api_key_configured)

    def test_summarize_text_success(self):
        # Configure the mock model instance's generate_content method
        mock_response = MockGenAIResponse(text_parts=["This is a mock summary."])
        self.mock_model_instance.generate_content.return_value = mock_response

        client = GeminiClient(api_key=self.api_key_to_use) # Ensures client.api_key_configured is True
        summary = client.summarize_text(self.sample_text)

        self.mock_model_instance.generate_content.assert_called_once()
        self.assertEqual(summary, "This is a mock summary.")

    def test_summarize_text_api_error(self):
        self.mock_model_instance.generate_content.side_effect = Exception("API Call Failed")

        client = GeminiClient(api_key=self.api_key_to_use)
        summary = client.summarize_text(self.sample_text)

        self.assertTrue(summary.startswith("Error: An API error occurred"))

    def test_summarize_text_no_api_key(self):
        with patch('warren_munger_screener.app.utils.gemini_client.GOOGLE_API_KEY', "YOUR_API_KEY_HERE"):
            client = GeminiClient() # API key not configured
            summary = client.summarize_text(self.sample_text)
            self.assertEqual(summary, "Error: GeminiClient is not configured due to missing or invalid API key.")

    def test_summarize_text_empty_input(self):
        client = GeminiClient(api_key=self.api_key_to_use)
        summary = client.summarize_text("")
        self.assertEqual(summary, "Error: No text provided to summarize or text is empty.")

    def test_summarize_text_prompt_blocked(self):
        # This test assumes prompt_feedback is directly on the response object and indicates a block reason.
        mock_response = MockGenAIResponse(text_parts=None, candidates=None, prompt_feedback={'block_reason': 'SAFETY'})
        self.mock_model_instance.generate_content.return_value = mock_response

        client = GeminiClient(api_key=self.api_key_to_use)
        summary = client.summarize_text(self.sample_text)
        self.assertIn("Error: Prompt blocked due to safety concerns (SAFETY)", summary)


    def test_summarize_text_content_generation_stopped_safety_via_candidate(self):
        # This test assumes no parts, no direct prompt_feedback block, but a candidate finish reason indicates safety.
        mock_candidate_safety = MagicMock()
        mock_candidate_safety.finish_reason.name = "SAFETY"
        # Important: The client logic checks for response.parts first. If parts are empty, it falls back to other checks.
        # To hit the candidate check, prompt_feedback should also be None or not have a block_reason.
        response_candidate_safety = MockGenAIResponse(text_parts=None, candidates=[mock_candidate_safety], prompt_feedback=None)

        self.mock_model_instance.generate_content.return_value = response_candidate_safety
        client = GeminiClient(api_key=self.api_key_to_use)
        summary = client.summarize_text(self.sample_text)
        self.assertIn("Error: Content generation finished due to an unexpected reason: SAFETY", summary)


    # Add more test methods for:
    # - Different model names during initialization.
    # - Various API response structures if they differ significantly (e.g., errors in candidates).
    # - Test max_output_tokens being passed to generation_config.
    # - Live API call test (optional, and should be marked clearly to run only if API key is valid and present).
    #   This would require not patching the genai calls for that specific test. Example:
    #   @unittest.skipIf(GOOGLE_API_KEY == "YOUR_API_KEY_HERE", "Skipping live API test, API key not configured")
    #   def test_summarize_text_live(self):
    #       # Important: Stop class-level patches for this specific live test.
    #       # This requires setUp and tearDown to be instance methods, not class methods,
    #       # or use a different patching approach for the live test.
    #       # For simplicity, if you had class-level patchers, you might need to stop them here.
    #       # TestGeminiClient.patcher_configure.stop()
    #       # TestGeminiClient.patcher_model.stop()
    #       # A better way for a single live test is often to not use class-level patching
    #       # or to manage the start/stop carefully.

    #       # Assuming patches are stopped for this specific test:
    #       # (This example assumes patches are managed outside this snippet for a live test)
    #       # try:
    #       #     client = GeminiClient() # Uses actual key from config
    #       #     if client.api_key_configured:
    #       #         summary = client.summarize_text("This is a simple live test.")
    #       #         self.assertIsNotNone(summary)
    #       #         self.assertNotIn("Error:", summary)
    #       #     else:
    #       #         self.skipTest("Live API key not configured, skipping live test.")
    #       # finally:
    #       #      TestGeminiClient.patcher_configure.start() # Restart patches
    #       #      TestGeminiClient.patcher_model.start()
    #       pass # Placeholder for actual live test structure


if __name__ == '__main__':
    unittest.main()
```
