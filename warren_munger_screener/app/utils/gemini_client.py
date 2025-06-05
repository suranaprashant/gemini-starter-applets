import google.generativeai as genai
from ..config import GOOGLE_API_KEY
# It's good practice to also handle potential import errors if config structure changes
# For example:
# try:
#     from ..config import GOOGLE_API_KEY
# except ImportError:
#     GOOGLE_API_KEY = None # Or some other fallback

class GeminiClient:
    def __init__(self, api_key=None, model_name='gemini-pro'):
        self.api_key = api_key if api_key else GOOGLE_API_KEY
        self.model = None
        self.api_key_configured = False

        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            print("Warning: GOOGLE_API_KEY is not configured or is set to the placeholder in config.py.")
            print("GeminiClient will not be able to make API calls.")
            return

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model_name)
            self.api_key_configured = True
            # print(f"GeminiClient initialized with model: {model_name}")
        except Exception as e:
            print(f"Error configuring Google Generative AI: {e}")
            print("Please ensure your API key is valid and correctly set.")

    def summarize_text(self, text_to_summarize,
                       prompt_instruction="Summarize the following text for financial analysis, focusing on key business strategies, competitive advantages, risks, and financial performance insights. Provide a concise overview:",
                       max_output_tokens=1024): # Default increased for potentially longer summaries
        """
        Summarizes the given text using the configured Gemini model.
        """
        if not self.api_key_configured or not self.model:
            return "Error: GeminiClient is not configured due to missing or invalid API key."

        if not text_to_summarize or not isinstance(text_to_summarize, str) or not text_to_summarize.strip():
            return "Error: No text provided to summarize or text is empty."

        full_prompt = f"{prompt_instruction}\n\n---\n\nTEXT TO SUMMARIZE:\n{text_to_summarize}\n\n---\n\nSUMMARY:"

        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_output_tokens
            # candidate_count=1 # Default is 1
            # temperature=0.7 # Default is often 0.9 or 1.0. Lower for more factual.
        )

        try:
            # print(f"Sending prompt to Gemini (first 100 chars): {full_prompt[:200]}...")
            response = self.model.generate_content(full_prompt, generation_config=generation_config)

            if response.candidates:
                # Check if the response has parts (common for gemini-pro)
                if response.parts:
                    summary = "".join(part.text for part in response.parts)
                    return summary.strip()
                # Fallback for older response structures or if no parts but text exists
                elif hasattr(response, 'text') and response.text:
                     return response.text.strip()
                else: # No text found, check for safety ratings or other issues
                    finish_reason = safe_get(response.prompt_feedback, ["block_reason"])
                    if finish_reason:
                         return f"Error: Content generation stopped due to safety concerns ({finish_reason})."
                    if response.candidates[0].finish_reason.name != "STOP":
                        return f"Error: Content generation finished due to an unexpected reason: {response.candidates[0].finish_reason.name}."

                    return "Error: Summarization failed - no text in response and no clear error reason."
            else: # No candidates, check for prompt feedback
                finish_reason = safe_get(response.prompt_feedback, ["block_reason"])
                if finish_reason:
                    return f"Error: Prompt blocked due to safety concerns ({finish_reason}). Cannot generate summary."
                return "Error: Summarization failed - no candidates in response."

        except Exception as e:
            # Catching a broader range of potential API errors
            # Specific errors like google.api_core.exceptions.GoogleAPIError can be caught if needed
            print(f"An API error occurred during text summarization: {e}")
            return f"Error: An API error occurred ({type(e).__name__}). Check logs for details."


if __name__ == '__main__':
    print("--- GeminiClient Test ---")

    # This example will only work if a REAL API key is in app/config.py
    # For testing purposes, we'll check if the key is the placeholder.

    client = GeminiClient()

    if not client.api_key_configured:
        print("\nSkipping live API call test as API key is not configured.")
        print("To run a live test, replace 'YOUR_API_KEY_HERE' in app/config.py with a valid Google API key.")
    else:
        print("\nAttempting live API call (ensure your API key is valid and has Gemini API enabled)...")
        sample_text_short = (
            "Company X reported a 20% increase in revenue for the fiscal year 2023, reaching $1.2 billion. "
            "Net profit grew by 15% to $150 million. The growth was primarily driven by the successful launch of "
            "their new flagship product, the 'Innovator 3000', which saw strong market adoption. "
            "Key risks include increased competition in the sector and supply chain disruptions for critical components. "
            "The company plans to expand into new geographic markets in the upcoming year and invest heavily in R&D."
        )

        sample_text_long = (
            "Management's Discussion and Analysis of Financial Condition and Results of Operations.\n"
            "For the fiscal year ended December 31, 2023, FutureTech Inc. reported significant progress amidst a challenging macroeconomic environment. "
            "Our total revenues reached $5.2 billion, an increase of 18% compared to $4.4 billion in the prior year. This growth was primarily driven by "
            "strong performance in our Cloud Services division, which saw a 35% increase in revenue due to higher adoption rates from enterprise clients and "
            "the successful launch of new AI-powered analytics tools. Our Software Licensing division also contributed positively, with a 10% revenue growth, "
            "reflecting continued demand for our core productivity suite.\n"
            "Gross profit margin improved to 62% from 60% in the previous year, mainly due to economies of scale in our Cloud Services and a favorable product mix. "
            "Operating expenses increased by 15% to $2.1 billion, primarily due to planned investments in research and development ($800 million, up 25%) aimed at "
            "enhancing our AI capabilities and developing next-generation software. Sales and marketing expenses also rose by 12% as we expanded our global sales team.\n"
            "Net income for the year was $1.5 billion, or $5.00 per diluted share, compared to $1.3 billion, or $4.30 per diluted share, in the prior year. "
            "Our effective tax rate was 21%.\n"
            "Key Business Strategies: Our strategy focuses on three pillars: 1) Leadership in AI and Cloud Computing, 2) Expansion of our Enterprise Software Suite, and "
            "3) Growth in Emerging Markets. We believe these strategies will position us for sustained long-term growth.\n"
            "Competitive Advantages: We believe our key competitive advantages include our cutting-edge technology, a strong global brand, a large and loyal customer base, "
            "and our talented workforce. Our continued investment in R&D is crucial to maintaining this edge.\n"
            "Risks: We face several risks, including rapid technological changes, intense competition from both established players and new entrants, potential cybersecurity threats, "
            "and reliance on key personnel. Furthermore, global economic slowdowns and geopolitical uncertainties could adversely affect our business.\n"
            "Financial Performance Insights: The strong revenue growth and margin improvement indicate healthy demand and operational efficiency. The increase in R&D spending, "
            "while impacting short-term profitability, is essential for future innovation. We maintain a strong balance sheet with $3 billion in cash and cash equivalents, "
            "providing financial flexibility for strategic investments or acquisitions."
        )

        print("\n--- Summarizing Short Text ---")
        summary_short = client.summarize_text(sample_text_short, max_output_tokens=150)
        if summary_short:
            print("Summary (Short Text):")
            print(summary_short)
        else:
            print("Summarization failed for short text.")

        print("\n--- Summarizing Long Text (MD&A Excerpt) ---")
        # Using the default prompt instruction from the method
        summary_long = client.summarize_text(sample_text_long, max_output_tokens=512)
        if summary_long:
            print("Summary (Long Text - MD&A):")
            print(summary_long)
        else:
            print("Summarization failed for long text.")

        print("\n--- Testing with Empty Text ---")
        summary_empty = client.summarize_text("")
        print(f"Summary (Empty Text): {summary_empty}")

        print("\n--- Testing with Custom Prompt ---")
        custom_prompt = "Extract only the key risks mentioned in the following text:"
        risks_summary = client.summarize_text(sample_text_long, prompt_instruction=custom_prompt, max_output_tokens=100)
        if risks_summary:
            print("Custom Summary (Risks):")
            print(risks_summary)
        else:
            print("Custom summarization failed.")

    print("\n--- GeminiClient Test Complete ---")
```
