import time

import httpx

BASE_URL = "http://127.0.0.1:8000"
MOCK_MODEL_ID = "00000000-0000-0000-0000-000000000002"


def wait_for_api(client: httpx.Client) -> None:
    for _ in range(40):
        try:
            response = client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    raise RuntimeError("API did not become healthy")


def wait_for_run(client: httpx.Client, run_id: str) -> dict:
    for _ in range(80):
        response = client.get(f"{BASE_URL}/api/v1/runs/{run_id}")
        response.raise_for_status()
        run = response.json()["data"]
        if run["status"] in {"COMPLETED", "FAILED", "CANCELLED"}:
            return run
        time.sleep(0.25)
    raise RuntimeError("Research Run did not finish")


def main() -> None:
    with httpx.Client(timeout=10.0) as client:
        wait_for_api(client)

        models = client.get(f"{BASE_URL}/api/v1/models")
        models.raise_for_status()
        assert any(
            model["id"] == MOCK_MODEL_ID for model in models.json()["data"]
        )

        technology = client.post(
            f"{BASE_URL}/api/v1/capabilities/technologies",
            json={
                "name": "LangGraph",
                "category": "Agent",
                "description": "Smoke-test technology",
            },
        )
        technology.raise_for_status()
        technology_id = technology.json()["data"]["technology"]["id"]

        created = client.post(
            f"{BASE_URL}/api/v1/research",
            json={
                "query": "Compare LangGraph and PydanticAI.",
                "model_id": MOCK_MODEL_ID,
            },
        )
        created.raise_for_status()
        run_id = created.json()["data"]["run_id"]

        run = wait_for_run(client, run_id)
        assert run["status"] == "COMPLETED", run
        assert run["input_tokens"] is not None
        assert run["output_tokens"] is not None
        assert run["estimated_cost"] is not None

        research = client.get(f"{BASE_URL}/api/v1/research/{run_id}")
        research.raise_for_status()
        report = research.json()["data"]["structured_result"]
        assert report["sources"]
        assert report["key_findings"]

        evaluations = client.get(
            f"{BASE_URL}/api/v1/runs/{run_id}/evaluations"
        )
        evaluations.raise_for_status()
        assert len(evaluations.json()["data"]) >= 4

        events = client.get(
            f"{BASE_URL}/api/v1/runs/{run_id}/events/history"
        )
        events.raise_for_status()
        event_types = {event["type"] for event in events.json()["data"]}
        required_events = {
            "run.started",
            "tool.started",
            "model.started",
            "evaluation.completed",
            "run.completed",
        }
        assert required_events.issubset(event_types), event_types

        knowledge = client.post(
            f"{BASE_URL}/api/v1/knowledge/from-research/{run_id}"
        )
        knowledge.raise_for_status()
        knowledge_id = knowledge.json()["data"]["id"]
        detail = client.get(f"{BASE_URL}/api/v1/knowledge/{knowledge_id}")
        detail.raise_for_status()
        linked_technologies = detail.json()["data"]["technologies"]
        assert any(item["name"] == "LangGraph" for item in linked_technologies)

        technology_update = client.patch(
            f"{BASE_URL}/api/v1/capabilities/technologies/{technology_id}",
            json={
                "category": "Agent Framework",
                "description": "Updated by smoke test",
            },
        )
        technology_update.raise_for_status()

        capability = client.put(
            f"{BASE_URL}/api/v1/capabilities/technologies/{technology_id}",
            json={
                "level": 2,
                "reason": "Can run and modify a workflow.",
                "next_target_level": 3,
                "next_action": "Build a real tool integration.",
            },
        )
        capability.raise_for_status()
        capability_id = capability.json()["data"]["capability"]["id"]

        evidence = client.post(
            f"{BASE_URL}/api/v1/capabilities/evidences",
            json={
                "title": "Research Loop Smoke Run",
                "evidence_type": "PROJECT",
                "description": "End-to-end CI evidence",
                "url": None,
            },
        )
        evidence.raise_for_status()
        evidence_id = evidence.json()["data"]["id"]

        evidence_update = client.patch(
            f"{BASE_URL}/api/v1/capabilities/evidences/{evidence_id}",
            json={"description": "Updated end-to-end CI evidence"},
        )
        evidence_update.raise_for_status()

        linked = client.post(
            f"{BASE_URL}/api/v1/capabilities/{capability_id}/evidences/{evidence_id}"
        )
        linked.raise_for_status()

        capability_evidence = client.get(
            f"{BASE_URL}/api/v1/capabilities/{capability_id}/evidences"
        )
        capability_evidence.raise_for_status()
        assert len(capability_evidence.json()["data"]) == 1

        delete_evidence = client.delete(
            f"{BASE_URL}/api/v1/capabilities/evidences/{evidence_id}"
        )
        delete_evidence.raise_for_status()

        delete_technology = client.delete(
            f"{BASE_URL}/api/v1/capabilities/technologies/{technology_id}"
        )
        delete_technology.raise_for_status()

        print(
            "smoke-ok",
            {
                "run_id": run_id,
                "knowledge_id": knowledge_id,
                "capability_id": capability_id,
            },
        )


if __name__ == "__main__":
    main()
