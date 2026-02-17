"""Service for generating images using OpenAI DALL-E"""
import aiohttp
import base64
import uuid
from pathlib import Path
from loguru import logger
from typing import Optional, List

from src.config import settings

# Directory for storing generated images (project root / generated_images)
IMAGES_DIR = Path(__file__).resolve().parent.parent.parent / "generated_images"


class ImageGenerationService:
    """Service to generate images for articles using DALL-E"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/images/generations"

    async def generate_image(self, title: str, content: str = None) -> Optional[str]:
        """
        Generate an image based on article title and content.

        Args:
            title: Article title
            content: Article content (optional, will be truncated if too long)

        Returns:
            Local file path of generated image or None if generation failed
        """
        try:
            prompt = self._create_prompt(title, content)
            logger.info(f"Generating image for article: {title[:50]}...")
            logger.debug(f"DALL-E prompt: {prompt}")
            return await self._call_dalle_and_save(prompt)
        except Exception as e:
            logger.error(f"Error generating image with DALL-E: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def generate_digest_image(self, articles_info: List[dict]) -> Optional[str]:
        """
        Generate an image for a digest based on multiple articles.

        Args:
            articles_info: List of dicts with 'title' (and optionally 'content') keys

        Returns:
            Local file path of generated image or None if generation failed
        """
        try:
            prompt = self._create_digest_prompt(articles_info)
            logger.info(f"Generating digest image from {len(articles_info)} articles...")
            logger.debug(f"DALL-E digest prompt: {prompt}")
            return await self._call_dalle_and_save(prompt)
        except Exception as e:
            logger.error(f"Error generating digest image: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def _call_dalle_and_save(self, prompt: str) -> Optional[str]:
        """
        Call DALL-E API with prompt, save image locally.

        Args:
            prompt: The prompt for DALL-E

        Returns:
            Local file path or None if failed
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "standard",
            "response_format": "b64_json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"DALL-E API error ({response.status}): {error_text}")
                    return None

                data = await response.json()

                if data and 'data' in data and len(data['data']) > 0:
                    b64_data = data['data'][0]['b64_json']
                    image_bytes = base64.b64decode(b64_data)

                    # Save to local file
                    IMAGES_DIR.mkdir(exist_ok=True)
                    filename = f"{uuid.uuid4().hex}.png"
                    filepath = IMAGES_DIR / filename

                    with open(filepath, 'wb') as f:
                        f.write(image_bytes)

                    local_path = str(filepath)
                    logger.info(f"Image saved locally: {local_path} ({len(image_bytes)} bytes)")
                    return local_path
                else:
                    logger.error("No image data in DALL-E response")
                    return None

    def _create_prompt(self, title: str, content: Optional[str] = None) -> str:
        """
        Create a DALL-E prompt from article title and content.

        Args:
            title: Article title
            content: Article content (optional)

        Returns:
            Generated prompt for DALL-E
        """
        base = "Create a professional, educational illustration for an article about: "
        prompt = base + title

        if content and len(content) > 50:
            context = content[:200].strip()
            context = ' '.join(context.split())
            prompt += f". Context: {context}"

        prompt += ". Style: modern, clean, professional, suitable for educational content about scholarships, internships, and study opportunities."

        if len(prompt) > 1000:
            prompt = prompt[:997] + "..."

        return prompt

    def _create_digest_prompt(self, articles_info: List[dict]) -> str:
        """
        Create a DALL-E prompt from multiple articles for a digest image.

        Args:
            articles_info: List of dicts with 'title' keys

        Returns:
            Generated prompt for DALL-E
        """
        titles = [info.get('title', '') for info in articles_info if info.get('title')]

        if not titles:
            return self._create_prompt("Educational digest", None)

        titles_text = "; ".join(titles[:6])

        prompt = (
            f"Create a professional, educational illustration for a news digest "
            f"covering these topics: {titles_text}. "
            f"Style: modern, clean, professional, suitable for educational content "
            f"about scholarships, internships, and study opportunities. "
            f"The image should represent the overall theme of education and global opportunities."
        )

        if len(prompt) > 1000:
            prompt = prompt[:997] + "..."

        return prompt
