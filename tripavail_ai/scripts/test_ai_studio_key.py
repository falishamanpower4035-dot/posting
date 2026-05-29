#!/usr/bin/env python3
import os
import sys
import json
import base64
from pathlib import Path
import requests


def get_key() -> str:
    # CLI: --key <KEY>
    if len(sys.argv) >= 3 and sys.argv[1] == "--key":
        return sys.argv[2]
    key = os.getenv("NANOBNANA_API_KEY") or os.getenv("NANONOB_API_KEY")
    if key:
        return key
    print("No AI Studio key found in env (NANOBNANA_API_KEY/NANONOB_API_KEY) or via --key")
    sys.exit(2)


def test_text(key: str) -> bool:
    model_candidates = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
    ]
    versions = ["v1", "v1beta"]
    payload = {
        "contents": [
            {
                "parts": [{"text": "Reply with OK"}],
            }
        ]
    }
    for ver in versions:
        for model in model_candidates:
            url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={key}"
            try:
                r = requests.post(url, json=payload, timeout=30)
                print(f"[TEXT {ver}/{model}] status:", r.status_code)
                if r.status_code == 200:
                    data = r.json()
                    cands = data.get("candidates") or []
                    if cands:
                        parts = (cands[0].get("content") or {}).get("parts", [])
                        if parts:
                            print("[TEXT] response:", parts[0].get("text", "<no text>"))
                    return True
                else:
                    print(f"[TEXT {ver}/{model}] body:", r.text[:300])
            except Exception as e:
                print(f"[TEXT {ver}/{model}] error:", e)
    return False


def test_image(key: str) -> bool:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate:generateContent?key={key}"
    payload = {
        "contents": [
            {
                "parts": [{"text": "Travel thumbnail, vertical 9:16, Maldives at sunset, cinematic lighting"}],
            }
        ]
    }
    try:
        r = requests.post(url, json=payload, timeout=60)
        print("[IMAGE] status:", r.status_code)
        if r.status_code != 200:
            print("[IMAGE] body:", r.text[:500])
            return False
        data = r.json()
        img_bytes = None
        try:
            cands = data.get("candidates") or []
            if cands:
                parts = (cands[0].get("content") or {}).get("parts", [])
                for p in parts:
                    inline = p.get("inline_data") or p.get("inlineData")
                    if inline and (inline.get("mime_type") or "").startswith("image/"):
                        b64 = inline.get("data")
                        if b64:
                            img_bytes = base64.b64decode(b64)
                            break
        except Exception:
            pass
        if not img_bytes:
            print("[IMAGE] no image data in response")
            return False
        out_dir = Path("data/tests/ai_studio_key")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "imagen_test.jpg"
        out_path.write_bytes(img_bytes)
        print("[IMAGE] saved:", out_path)
        return True
    except Exception as e:
        print("[IMAGE] error:", e)
        return False


def main():
    text_only = "--text-only" in sys.argv
    key = get_key()
    print("Testing AI Studio key...")
    # List models - v1 and v1beta
    try:
        lm_v1 = requests.get(f"https://generativelanguage.googleapis.com/v1/models?key={key}", timeout=15)
        print("[LIST v1] status:", lm_v1.status_code)
        if lm_v1.status_code != 200:
            print("[LIST v1] body:", lm_v1.text[:300])
        else:
            try:
                names = [m.get("name") for m in lm_v1.json().get("models", [])][:5]
                print("[LIST v1] models:", names)
            except Exception:
                pass
    except Exception as e:
        print("[LIST v1] error:", e)
    try:
        lm_v1b = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}", timeout=15)
        print("[LIST v1beta] status:", lm_v1b.status_code)
        if lm_v1b.status_code != 200:
            print("[LIST v1beta] body:", lm_v1b.text[:300])
        else:
            try:
                names = [m.get("name") for m in lm_v1b.json().get("models", [])][:5]
                print("[LIST v1beta] models:", names)
            except Exception:
                pass
    except Exception as e:
        print("[LIST v1beta] error:", e)
    ok_text = test_text(key)
    ok_image = False
    if not text_only:
        ok_image = test_image(key)
    print("RESULTS => text:", ok_text, ", image:", ok_image)
    sys.exit(0 if ok_text else 1)


if __name__ == "__main__":
    main()


