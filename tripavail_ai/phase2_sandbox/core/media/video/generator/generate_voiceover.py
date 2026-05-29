"""
Generate CTA and Voiceover per post using OpenAI
- Reads data/posts.json
- Creates short CTA line tailored to the news
- Generates voiceover audio (news-anchor tone)
- Saves audio to data/audio/voiceovers/{post_id}.mp3
- Writes CTA manifest to data/cta_manifest.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class VoiceoverGenerator:
	def __init__(self):
		self.data_dir = Path("data")
		self.posts_file = self.data_dir / "posts.json"
		self.output_audio_dir = self.data_dir / "audio" / "voiceovers"
		self.cta_manifest_file = self.data_dir / "cta_manifest.json"
		self.client = OpenAI()
		self.model_chat = os.getenv("OPENAI_MODEL_CHAT", "gpt-4o-mini")
		self.model_tts = os.getenv("OPENAI_MODEL_TTS", "gpt-4o-mini-tts")
		self.voice = os.getenv("VOICE_NAME", "alloy")
		self.output_audio_dir.mkdir(parents=True, exist_ok=True)
		logger.info("VoiceoverGenerator initialized")

	def _load_posts(self) -> List[Dict[str, Any]]:
		data = json.loads(self.posts_file.read_text(encoding="utf-8"))
		posts = data.get("posts", [])
		for idx, p in enumerate(posts, start=1):
			p["post_id"] = p.get("post_id") or f"{idx:03d}"
		return posts

	def _generate_cta(self, post: Dict[str, Any]) -> str:
		title = post.get("original_title", "")
		summary = post.get("original_summary", "")
		region = post.get("region", "")
		prompt = f"""
You are a travel newsroom producer. Write ONE compelling end-card CTA (max 14 words) tailored to this story. Be specific, positive, and action-led. No hashtags. No quotes.

Title: {title}
Summary: {summary}
Region: {region}

Return only the CTA line.
"""
		resp = self.client.chat.completions.create(
			model=self.model_chat,
			messages=[
				{"role": "system", "content": "You write concise, compelling CTAs for global travel news."},
				{"role": "user", "content": prompt},
			],
			max_tokens=40,
		)
		cta = resp.choices[0].message.content.strip()
		return cta.replace("\n", " ")[:120]

	def _build_script(self, post: Dict[str, Any], cta: str) -> str:
		region = post.get("region") or ""
		title = post.get("original_title") or ""
		summary = post.get("original_summary") or ""
		script_prompt = f"""
Write a 35-word voiceover in a warm, credible news-anchor tone.
Structure: Hook (destination/topic) + one concrete detail + CTA.
Avoid hashtags and emojis. Keep it natural and authentic.

Title: {title}
Summary: {summary}
Region: {region}
CTA: {cta}
"""
		resp = self.client.chat.completions.create(
			model=self.model_chat,
			messages=[
				{"role": "system", "content": "You are a concise, trustworthy travel news anchor."},
				{"role": "user", "content": script_prompt},
			],
			max_tokens=120,
		)
		script = resp.choices[0].message.content.strip().replace("\n", " ")
		return script

	def _synthesize(self, text: str, outfile: Path):
		# Create TTS audio (mp3 bytes)
		resp = self.client.audio.speech.create(
			model=self.model_tts,
			voice=self.voice,
			input=text,
		)
		outfile.write_bytes(resp.content)

	def generate_for_post(self, post: Dict[str, Any]) -> bool:
		"""Generate voiceover for a single post"""
		post_id = post.get('topic_id', post.get('post_id', '001'))
		logger.info(f"Generating voiceover for post {post_id}")
		
		try:
			# Generate CTA
			cta = self._generate_cta(post)
			
			# Build script
			script = self._build_script(post, cta)
			
			# Generate TTS
			response = self.client.audio.speech.create(
				model="tts-1",
				voice=self.voice,
				input=script
			)
			
			# Save audio
			output_path = self.output_audio_dir / f"{post_id}.mp3"
			output_path.parent.mkdir(parents=True, exist_ok=True)
			
			with open(output_path, 'wb') as f:
				f.write(response.content)
			
			logger.info(f"Voiceover generated: {output_path}")
			return True
			
		except Exception as e:
			logger.error(f"Failed to generate voiceover for post {post_id}: {e}")
			return False

	def run(self) -> Dict[str, str]:
		posts = self._load_posts()
		cta_map: Dict[str, str] = {}
		for post in posts:
			pid = post["post_id"]
			cta = self._generate_cta(post)
			cta_map[pid] = cta
			script = self._build_script(post, cta)
			out_audio = self.output_audio_dir / f"{pid}.mp3"
			try:
				self._synthesize(script, out_audio)
				logger.info(f"Voiceover generated: {out_audio}")
			except Exception as e:
				logger.error(f"TTS failed for {pid}: {e}")
		# Save CTA manifest
		self.cta_manifest_file.write_text(json.dumps({"generated_at": datetime_now(), "cta": cta_map}, indent=2), encoding="utf-8")
		return cta_map


def datetime_now() -> str:
	from datetime import datetime
	return datetime.now().isoformat()


def main():
	gen = VoiceoverGenerator()
	cta_map = gen.run()
	print(f"[OK] CTA+VO generated for {len(cta_map)} posts")


if __name__ == "__main__":
	main()
