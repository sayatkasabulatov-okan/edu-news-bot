"""Service for generating images using OpenAI DALL-E"""
import aiohttp
from loguru import logger
from typing import Optional

from src.config import settings


class ImageGenerationService:
    """Service to generate images for articles using DALL-E"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/images/generations"

    async def generate_image(self, title: str, content: str = None) -> Optional[str]:
        """
        Generate an image based on article title and content

        Args:
            title: Article title
            content: Article content (optional, will be truncated if too long)

        Returns:
            URL of generated image or None if generation failed
        """
        try:
            # Create a prompt for DALL-E
            prompt = self._create_prompt(title, content)

            logger.info(f"Generating image for article: {title[:50]}...")
            logger.debug(f"DALL-E prompt: {prompt}")

            # Call OpenAI DALL-E API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "standard"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"DALL-E API error ({response.status}): {error_text}")
                        return None

                    data = await response.json()

                    # Extract image URL from response
                    if data and 'data' in data and len(data['data']) > 0:
                        image_url = data['data'][0]['url']
                        logger.info(f"Successfully generated image: {image_url}")
                        return image_url
                    else:
                        logger.error("No image URL in DALL-E response")
                        return None

        except Exception as e:
            logger.error(f"Error generating image with DALL-E: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _create_prompt(self, title: str, content: Optional[str] = None) -> str:
        """
        Create a DALL-E prompt from article title and content

        Args:
            title: Article title
            content: Article content (optional)

        Returns:
            Generated prompt for DALL-E
        """
        # Start with base prompt
        base = "Create a professional, educational illustration for an article about: "

        # Add title
        prompt = base + title

        # Optionally add context from content (first 200 chars)
        if content and len(content) > 50:
            context = content[:200].strip()
            # Remove newlines and extra spaces
            context = ' '.join(context.split())
            prompt += f". Context: {context}"

        # Add style guidance
        prompt += ". Style: modern, clean, professional, suitable for educational content about scholarships, internships, and study opportunities."

        # Limit prompt length (DALL-E has a limit)
        if len(prompt) > 1000:
            prompt = prompt[:997] + "..."

        return prompt
