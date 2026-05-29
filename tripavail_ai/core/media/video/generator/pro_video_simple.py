	def _build_ffmpeg_cmd(self, images: List[str], output: str, hook_text: str) -> List[str]:
		"""Build a simplified FFmpeg command that works reliably"""
		num_images = len(images)
		
		# Inputs: images with loop and duration
		inputs = []
		for img in images:
			inputs += ["-loop", "1", "-t", str(self.image_sec), "-i", img]
		
		# Optional voiceover
		vo_path = self.data_dir / "audio" / "voiceovers" / f"{Path(images[0]).parts[-2]}.mp3"
		vo_exists = vo_path.exists()
		if vo_exists:
			inputs += ["-i", str(vo_path)]
		
		# Build filtergraph: scale each image, then concat
		filters = []
		
		# Scale and pad each image
		for i in range(num_images):
			filters.append(f"[{i}:v]scale={self.target_w}:{self.target_h}:force_original_aspect_ratio=decrease,pad={self.target_w}:{self.target_h}:(ow-iw)/2:(oh-ih)/2,fps={self.fps}[v{i}]")
		
		# Concatenate all images
		concat_inputs = "".join([f"[v{i}]" for i in range(num_images)])
		filters.append(f"{concat_inputs}concat=n={num_images}:v=1:a=0[vout]")
		
		# Add hook text
		hook_sanitized = hook_text.encode('ascii', 'ignore').decode('ascii')
		hook_sanitized = hook_sanitized.replace(':', '\\:').replace("'", "\\'")
		filters.append(f"[vout]drawtext=text='{hook_sanitized}':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.35:boxborderw=15:x=(w-tw)/2:y=h-th-80:enable='lte(t,3)'[vt]")
		
		# Add logo if present
		if self.logo_path.exists():
			inputs += ["-i", str(self.logo_path)]
			logo_idx = num_images + (1 if vo_exists else 0)
			filters.append(f"[vt][{logo_idx}:v]scale2ref=w=iw*0.18:h=ow/mdar[logo][base];[base][logo]overlay=x=W-w-40:y=H-h-40:format=auto[vfinal]")
		else:
			filters.append("[vt]copy[vfinal]")
		
		# Audio handling
		amap = []
		if vo_exists:
			vo_idx = num_images
			filters.append(f"[{vo_idx}:a]volume=1.0,atrim=0:{self.total_sec},asetpts=N/SR/TB[aout]")
			amap = ["-map", "[vfinal]", "-map", "[aout]"]
		else:
			# No audio
			amap = ["-map", "[vfinal]"]
		
		# Join all filters
		filter_complex = ";".join(filters)
		
		# Output options
		out_opts = [
			"-t", str(self.total_sec),
			"-c:v", "libx264",
			"-preset", "medium",
			"-crf", "20",
			"-pix_fmt", "yuv420p",
			"-shortest",
		]
		
		# Add audio codec if we have audio
		if vo_exists:
			out_opts.extend(["-c:a", "aac", "-b:a", "160k"])
		
		cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_complex] + amap + out_opts + [output]
		return cmd
