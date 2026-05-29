"""
Enhanced audio mixing for reels using MoviePy
- Loads pro reels and voiceovers
- Adds background music with proper ducking
- Creates energetic final videos
"""

from pathlib import Path
from typing import Optional, List
from loguru import logger
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
import random
import json

from core.media.audio.manager.sound_effects import SoundEffectsManager
from core.media.audio.manager.ambient_sound import AmbientSoundManager
from core.media.video.generator.caption_generator import CaptionGenerator


class AudioMixer:
	def __init__(self):
		self.data_dir = Path("data")
		self.videos_dir = self.data_dir / "videos"
		self.vo_dir = self.data_dir / "audio" / "voiceovers"
		
		# Try multiple music directories
		self.music_dirs = [
			Path("assets") / "audio",
			Path("data") / "audio" / "music",
			Path("assets") / "music"
		]
		
		# ULTRA PREMIUM AUDIO SETTINGS
		self.music_volume = 0.15  # Background music (slightly higher for premium feel)
		self.vo_volume = 1.0      # Keep voiceover at full volume
		self.ambient_volume = 0.10  # PREMIUM: ElevenLabs ambient sounds (enhanced)
		self.audio_bitrate = "320k"  # High quality audio encoding
		self.audio_sample_rate = 48000  # Professional sample rate
		
		# PREMIUM: ElevenLabs Ambient Sound Manager
		try:
			self.ambient_manager = AmbientSoundManager()
			logger.info("✨ ElevenLabs Ambient Sound Manager enabled (PREMIUM)")
		except Exception as e:
			logger.warning(f"ElevenLabs Ambient Sound disabled: {e}")
			self.ambient_manager = None
		
		# Caption Generator for adding subtitles to final videos
		try:
			self.caption_generator = CaptionGenerator()
			logger.info("✨ Caption Generator enabled")
		except Exception as e:
			logger.warning(f"Caption Generator disabled: {e}")
			self.caption_generator = None
		
		logger.info("AudioMixer initialized (Enhanced with PREMIUM ElevenLabs + Captions)")
		
		# Transition timing assumptions (sync with pro_video)
		self.image_sec = 3.5
		self.fade_sec = 0.8

	def _pick_music(self) -> Optional[Path]:
		"""Find and pick energetic background music"""
		candidates = []
		
		# Check all possible music directories
		for music_dir in self.music_dirs:
			if music_dir.exists():
				candidates.extend(list(music_dir.glob("*.mp3")))
				candidates.extend(list(music_dir.glob("*.wav")))
		
		if candidates:
			music = random.choice(candidates)
			logger.info(f"Selected background music: {music.name}")
			return music
		
		logger.warning("No background music found in any directory")
		return None

	def _find_posts(self):
		# find pro reels
		return sorted(self.videos_dir.glob("reel_*_pro.mp4"))

	def mix_for_post(self, pro_video: Path):
		pid = pro_video.name.replace("reel_", "").replace("_pro.mp4", "")
		vo_path = self.vo_dir / f"{pid}.mp3"
		music_path = self._pick_music()
		
		with VideoFileClip(str(pro_video)) as v:
			# Use voiceover duration as the target duration
			target_duration = v.duration
			if vo_path.exists():
				vo_clip = AudioFileClip(str(vo_path))
				target_duration = vo_clip.duration
				vo_clip.close()
			
			tracks: List[AudioFileClip] = []
			
			# Voiceover at full volume for clarity
			if vo_path.exists():
				vo = AudioFileClip(str(vo_path))
				vo = vo.with_duration(target_duration)
				vo = vo.with_volume_scaled(self.vo_volume)  # Full volume
				tracks.append(vo)
				logger.info(f"Added voiceover at {self.vo_volume} volume")
			
			# Background music under VO with proper ducking
			if music_path:
				mu = AudioFileClip(str(music_path))
				# Loop music to match duration
				if mu.duration < target_duration:
					loops_needed = int(target_duration / mu.duration) + 1
					mu = mu.loop(n=loops_needed)
				mu = mu.with_duration(target_duration)
				# Duck music volume so voiceover is clear but music adds energy
				mu = mu.with_volume_scaled(self.music_volume)  # Ducked volume for background
				tracks.append(mu)
				logger.info(f"Added background music at {self.music_volume} volume")
			
			# Add transition SFX overlays (light whooshes at crossfades)
			self._add_transition_sfx(pid, target_duration, tracks)
			
			# PREMIUM: Add ElevenLabs ambient sound (always, regardless of music)
			# Determine content type from post metadata
			content_type = "default"
			voiceover_script = None
			try:
				posts_file = self.data_dir / "posts.json"
				if posts_file.exists():
					data = json.loads(posts_file.read_text(encoding="utf-8"))
					for p in data.get("posts", []):
						if str(p.get("topic_id")) == str(pid):
							content_type = p.get("content_type", "default")
							voiceover_script = p.get("voiceover_script") or p.get("caption", "")
							break
			except:
				pass
			
			self._add_ambient_if_available(pid, target_duration, tracks, content_type)

			if not tracks:
				logger.warning(f"No audio found for {pid}, skipping mix")
				return None
			
			final_audio = CompositeAudioClip(tracks).with_duration(target_duration)
			# Extend video to match voiceover duration
			if target_duration > v.duration:
				# Loop the video to extend it
				loops_needed = int(target_duration / v.duration) + 1
				final = v.loop(n=loops_needed).with_duration(target_duration).with_audio(final_audio)
			else:
				final = v.with_audio(final_audio)
			out = pro_video.with_name(f"reel_{pid}_final.mp4")
			final.write_videofile(str(out), codec="libx264", audio_codec="aac", fps=30)
			logger.info(f"Mixed final reel: {out}")
			
			# Add captions to the final video
			if self.caption_generator and voiceover_script and vo_path.exists():
				logger.info(f"Adding captions to {out}...")
				try:
					captioned_out = self._add_captions_to_final(out, pid, voiceover_script, target_duration)
					if captioned_out:
						logger.info(f"✅ Captions added successfully: {captioned_out}")
						return captioned_out
				except Exception as e:
					logger.error(f"Failed to add captions: {e}, returning non-captioned video")
			
			return out

	def _add_captions_to_final(
		self, 
		video_path: Path, 
		pid: str, 
		voiceover_script: str, 
		duration: float
	) -> Optional[Path]:
		"""
		Add captions to the final video using the caption generator
		
		Args:
			video_path: Path to the final video (without captions)
			pid: Post ID
			voiceover_script: Voiceover script text
			duration: Voiceover duration
			
		Returns:
			Path to captioned video or None if failed
		"""
		try:
			captioned_path = self.caption_generator.generate_for_post(
				post_id=pid,
				video_path=video_path,
				voiceover_script=voiceover_script,
				voiceover_duration=duration
			)
			
			if captioned_path and captioned_path.exists():
				# Remove the non-captioned version to save space
				try:
					video_path.unlink()
					logger.info(f"Removed non-captioned video: {video_path}")
				except Exception as e:
					logger.warning(f"Could not remove non-captioned video: {e}")
				
				# Rename captioned video to final video name
				final_path = video_path.with_name(f"reel_{pid}_final.mp4")
				if captioned_path != final_path:
					captioned_path.rename(final_path)
					logger.info(f"Renamed captioned video to: {final_path}")
					return final_path
				
				return captioned_path
			
			return None
			
		except Exception as e:
			logger.error(f"Failed to add captions: {e}")
			return None
	
	def _add_transition_sfx(self, pid: str, target_duration: float, tracks: List[AudioFileClip]):
		sfx_mgr = SoundEffectsManager()
		fx = sfx_mgr.get_transition_effect("whoosh")
		if not fx:
			return
		try:
			fx_path = Path(fx["file_path"]) if isinstance(fx["file_path"], str) else fx["file_path"]
			if not fx_path.exists():
				return
			base = AudioFileClip(str(fx_path)).with_volume_scaled(fx.get("volume", 0.25))
			gap = max(self.image_sec - self.fade_sec, 1.0)
			t = gap
			while t < target_duration - 0.5:
				tracks.append(base.set_start(t))
				t += gap
		except Exception:
			pass

	def _add_ambient_if_available(self, pid: str, target_duration: float, tracks: List[AudioFileClip], content_type: str = "default"):
		"""
		Add ambient sound layer
		Priority: ElevenLabs AI-generated > Local sound effects
		"""
		# PREMIUM: Try ElevenLabs ambient sound first
		if self.ambient_manager and self.ambient_manager.enabled:
			try:
				logger.info(f"🎵 Generating ElevenLabs ambient sound for {content_type}...")
				ambient_path = self.ambient_manager.get_ambient_for_content_type(
					content_type=content_type,
					duration=target_duration
				)
				
				if ambient_path and ambient_path.exists():
					ambient = AudioFileClip(str(ambient_path))
					# Loop if needed
					if ambient.duration < target_duration:
						loops = int(target_duration / ambient.duration) + 1
						ambient = ambient.loop(n=loops)
					
					ambient = ambient.with_duration(target_duration).with_volume_scaled(self.ambient_volume)
					tracks.append(ambient)
					logger.info(f"✨ Added PREMIUM ElevenLabs ambient sound: {content_type}")
					return  # Success, don't fallback
			except Exception as e:
				logger.warning(f"ElevenLabs ambient failed: {e}, falling back to local SFX")
		
		# Fallback: Use local sound effects
		try:
			posts_file = self.data_dir / "posts.json"
			region = ""
			if posts_file.exists():
				data = json.loads(posts_file.read_text(encoding="utf-8"))
				for p in data.get("posts", []):
					if str(p.get("topic_id")) == str(pid):
						region = p.get("region", "")
						break
			
			sfx_mgr = SoundEffectsManager()
			a = sfx_mgr.get_ambient_effect(region or "")
			if not a:
				return
			apath = Path(a["file_path"]) if isinstance(a["file_path"], str) else a["file_path"]
			if not apath.exists():
				return
			ambient = AudioFileClip(str(apath))
			if ambient.duration < target_duration:
				loops = int(target_duration / ambient.duration) + 1
				ambient = ambient.loop(n=loops)
			ambient = ambient.with_duration(target_duration).with_volume_scaled(0.12)
			tracks.append(ambient)
			logger.info(f"Added local ambient sound: {region}")
		except Exception as e:
			logger.debug(f"Local ambient sound failed: {e}")

	def run(self):
		pro_reels = self._find_posts()
		results = []
		for p in pro_reels:
			res = self.mix_for_post(p)
			if res:
				results.append(res)
		logger.info(f"Audio mix complete: {len(results)} final videos")
		return results


def main():
	m = AudioMixer()
	m.run()


if __name__ == "__main__":
	main()