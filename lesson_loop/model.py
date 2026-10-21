"""Gemini REST client: API key or Vertex ADC. Tokens never enter run artifacts."""

import json
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class Gemini:
    def __init__(self, model="gemini-3.8-flash", backend=None, project=None, location=None):
        self.backend = backend or os.getenv("LLM_BACKEND", "gemini")
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        if self.location not in ("global", "us", "eu"):
            raise ValueError("Location must be global, us or eu for this model.")
        self.credentials = None
        self.key = None
        if self.backend == "gemini":
            self.key = os.environ.get("GEMINI_API_KEY")
            if not self.key:
                raise ValueError("Set GEMINI_API_KEY before running. See README.md.")
        elif self.backend == "vertex":
            if not self.project or not re.fullmatch(r"[a-z0-9-]+", self.project):
                raise ValueError("Vertex needs a valid GOOGLE_CLOUD_PROJECT or --project.")
            try:
                import google.auth
                self.credentials, _ = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                    quota_project_id=self.project,
                )
            except ImportError:
                raise ValueError("Install requirements-vertex.txt for Vertex ADC.") from None
            except Exception:
                raise ValueError("ADC unavailable. Run gcloud auth application-default login.") from None
        else:
            raise ValueError("Backend must be gemini or vertex.")
        if not re.fullmatch(r"[a-zA-Z0-9._-]+", model):
            raise ValueError("Invalid model ID.")
        self.model = model
        self.calls = []

    def complete(self, role, instructions, data, schema):
        body = {
            "systemInstruction": {"parts": [{"text": instructions}]},
            "contents": [{"role": "user", "parts": [
                {"text": json.dumps(data, ensure_ascii=False)}
            ]}],
            "generationConfig": {
                "maxOutputTokens": 10000,
                "thinkingConfig": {"thinkingLevel": "low"},
                "responseFormat": {"text": {
                    "mimeType": "APPLICATION_JSON", "schema": schema
                }},
            },
        }
        headers = {"Content-Type": "application/json"}
        if self.backend == "vertex":
            from google.auth.transport.requests import Request as AuthRequest
            try:
                if not self.credentials.valid:
                    self.credentials.refresh(AuthRequest())
            except Exception:
                raise RuntimeError("Could not refresh ADC. Check your Google Cloud login.") from None
            headers["Authorization"] = f"Bearer {self.credentials.token}"
            headers["x-goog-user-project"] = self.project
            host = ("aiplatform.googleapis.com" if self.location == "global" else
                    f"aiplatform.{self.location}.rep.googleapis.com")
            url = (f"https://{host}/v1/projects/{self.project}"
                   f"/locations/{self.location}/publishers/google/models/{self.model}:generateContent")
        else:
            headers["x-goog-api-key"] = self.key
            url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{self.model}:generateContent")
        started = time.monotonic()
        for attempt in range(3):
            request = Request(url, data=json.dumps(body).encode(), headers=headers)
            try:
                with urlopen(request, timeout=90) as response:
                    result = json.load(response)
                break
            except HTTPError as exc:
                # Never print request headers, API keys, or raw HTTP bodies.
                if (exc.code == 429 or 500 <= exc.code < 600) and attempt < 2:
                    time.sleep(5 * (2 ** attempt))
                    continue
                raise RuntimeError(
                    f"Gemini HTTP {exc.code}. Check model access, key and quota."
                ) from None
            except (URLError, TimeoutError, OSError):
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError("Gemini connection failed after 3 attempts.") from None
        candidates = result.get("candidates", [])
        if not candidates or candidates[0].get("finishReason") != "STOP":
            raise RuntimeError("Gemini returned blocked or incomplete output; nothing shipped.")
        parts = candidates[0].get("content", {}).get("parts", [])
        raw = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            raise RuntimeError("Gemini returned invalid JSON; nothing shipped.") from None
        self.calls.append({
            "role": role, "model": self.model, "backend": self.backend,
            "location": self.location if self.backend == "vertex" else None,
            "model_version": result.get("modelVersion"),
            "seconds": round(time.monotonic() - started, 2),
            "usage": result.get("usageMetadata", {}),
            "http_attempts": attempt + 1,
        })
        return parsed
