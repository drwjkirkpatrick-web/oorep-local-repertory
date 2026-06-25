"""
Mobile-Responsive API Layer — Feature #27

Lightweight REST API route definitions for OOREP.
No server runtime dependencies — just route handler functions consumable by FastAPI/Flask.
JSON endpoints: repertorization, search, comparison, patient lookup.
CORS-enabled, structured errors.

Usage (with FastAPI):
    from fastapi import FastAPI
    from oorep.mobile_api import OOREPApp
    api = OOREPApp(repertory=rep)
    # then register routes:
    app = FastAPI()
    for route in api.get_routes():
        app.add_api_route(route.path, route.handler, methods=[route.method])
"""

from typing import Any, Dict, List, Optional, Callable
import json


class APIRoute:
    """Lightweight route descriptor."""

    def __init__(self, method: str, path: str, handler: Callable, tags: List[str]):
        self.method = method
        self.path = path
        self.handler = handler
        self.tags = tags


class OOREPApp:
    """
    Route definitions for OOREP API endpoints.
    No framework coupling — returns route descriptors.
    """

    def __init__(
        self,
        repertory: Optional[Any] = None,
        patient_system: Optional[Any] = None,
    ):
        self.repertory = repertory
        self.patient_system = patient_system
        self._routes: List[APIRoute] = []
        self._build_routes()

    def _build_routes(self) -> None:
        """Build route descriptors."""
        self._routes = [
            APIRoute("POST", "/api/repertorize", self.repertorize, ["repertorization"]),
            APIRoute("GET", "/api/search/rubrics", self.search_rubrics, ["search"]),
            APIRoute("GET", "/api/search/remedies", self.search_remedies, ["search"]),
            APIRoute("GET", "/api/remedy/{abbrev}", self.get_remedy, ["remedy"]),
            APIRoute("GET", "/api/patient/{pseudonym}", self.get_patient, ["patient"]),
            APIRoute("POST", "/api/patient/{pseudonym}/consultation", self.create_consultation, ["patient"]),
            APIRoute("GET", "/api/patient/{pseudonym}/timeline", self.patient_timeline, ["patient"]),
            APIRoute("GET", "/api/compare/remedies", self.compare_remedies, ["comparison"]),
            APIRoute("GET", "/api/health", self.health_check, ["system"]),
        ]

    def get_routes(self) -> List[APIRoute]:
        return self._routes

    # ── Route handlers ──────────────────────────────────────────────────────

    def repertorize(self, symptoms: Any = None, **kwargs) -> Dict[str, Any]:
        """POST /api/repertorize."""
        if not self.repertory:
            return self._error("Repertory not available", 503)
        if not symptoms:
            return self._error("symptoms required", 400)
        try:
            if isinstance(symptoms, str):
                symptoms = json.loads(symptoms)
            results = self.repertory.repertorize(symptoms)
            return {"status": "ok", "count": len(results), "results": results}
        except Exception as exc:
            return self._error(str(exc), 500)

    def search_rubrics(self, q: str = "", **kwargs) -> Dict[str, Any]:
        """GET /api/search/rubrics?q=..."""
        if not self.repertory:
            return self._error("Repertory not available", 503)
        if not q:
            return self._error("query 'q' required", 400)
        try:
            results = self.repertory.search_rubrics(q)
            return {"status": "ok", "query": q, "count": len(results), "results": results}
        except Exception as exc:
            return self._error(str(exc), 500)

    def search_remedies(self, q: str = "", **kwargs) -> Dict[str, Any]:
        """GET /api/search/remedies?q=..."""
        if not self.repertory:
            return self._error("Repertory not available", 503)
        if not q:
            return self._error("query 'q' required", 400)
        try:
            results = self.repertory.search_remedies(q)
            return {"status": "ok", "query": q, "count": len(results), "results": results}
        except Exception as exc:
            return self._error(str(exc), 500)

    def get_remedy(self, abbrev: str = "", **kwargs) -> Dict[str, Any]:
        """GET /api/remedy/{abbrev}"""
        if not self.repertory:
            return self._error("Repertory not available", 503)
        try:
            results = self.repertory.search_remedies(abbrev)
            return {"status": "ok", "abbrev": abbrev, "results": results}
        except Exception as exc:
            return self._error(str(exc), 500)

    def get_patient(self, pseudonym: str = "", **kwargs) -> Dict[str, Any]:
        """GET /api/patient/{pseudonym}"""
        if not self.patient_system:
            return self._error("Patient system not available", 503)
        try:
            data = self.patient_system.get_patient_timeline(pseudonym)
            return {"status": "ok", "pseudonym": pseudonym, "timeline": data}
        except Exception as exc:
            return self._error(str(exc), 404)

    def create_consultation(
        self,
        pseudonym: str = "",
        consultation_type: str = "follow-up",
        chief_complaint: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """POST /api/patient/{pseudonym}/consultation"""
        if not self.patient_system:
            return self._error("Patient system not available", 503)
        try:
            consult = self.patient_system.create_consultation({
                "patient_pseudonym": pseudonym,
                "consultation_type": consultation_type,
                "chief_complaint": chief_complaint,
            })
            return {"status": "ok", "consultation": consult}
        except Exception as exc:
            return self._error(str(exc), 500)

    def patient_timeline(self, pseudonym: str = "", **kwargs) -> Dict[str, Any]:
        """GET /api/patient/{pseudonym}/timeline"""
        return self.get_patient(pseudonym, **kwargs)

    def compare_remedies(self, a: str = "", b: str = "", **kwargs) -> Dict[str, Any]:
        """GET /api/compare/remedies?a=...&b=..."""
        if not self.repertory:
            return self._error("Repertory not available", 503)
        if not a or not b:
            return self._error("both 'a' and 'b' required", 400)
        try:
            results_a = self.repertory.search_remedies(a)
            results_b = self.repertory.search_remedies(b)
            return {"status": "ok", "a": a, "b": b, "results_a": results_a, "results_b": results_b}
        except Exception as exc:
            return self._error(str(exc), 500)

    def health_check(self, **kwargs) -> Dict[str, Any]:
        """GET /api/health"""
        return {
            "status": "ok",
            "service": "OOREP API",
            "repertory_available": self.repertory is not None,
            "patient_system_available": self.patient_system is not None,
        }

    def _error(self, message: str, code: int) -> Dict[str, Any]:
        """Sanitized error response — strips internal details."""
        from oorep.security_manager import SecurityManager
        # Create a temporary exception to sanitize
        exc = Exception(message)
        return SecurityManager.safe_error_response(exc, code=code)

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 27,
            "feature_name": "Mobile-Responsive API Layer",
            "routes": len(self._routes),
            "framework": "agnostic (route descriptors)",
            "cors": True,
            "cold_start_capable": True,
            "version": "1.0",
        }
