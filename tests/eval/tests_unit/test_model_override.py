"""--model: run a local arm with another Ollama model (e.g. gemma4:e4b) under its own arm name."""
import pytest

from mimir_eval.config import load_config, model_tag, resolve


def test_model_override_renames_local_arm():
    cfg = load_config(resolve("configs/e2_blueprint_verifier.yaml"), model="gemma4:e4b")
    assert cfg["name"] == "E2-gemma4-e4b" and cfg["base_arm"] == "E2"
    assert cfg["generator"]["model"] == "gemma4:e4b" and cfg["generator"]["provider"] == "ollama"
    assert cfg["generator"]["think"] is None
    b = load_config(resolve("configs/b_doc_local.yaml"), model="gemma4:e4b", tag="g4", think=False)
    assert b["name"] == "B-doc-L-g4" and "gemma4:e4b" in b["description"] and "qwen2.5" not in b["description"]
    assert b["generator"]["think"] is False
    # E2x keeps its other-family verifier
    x = load_config(resolve("configs/e2x_blueprint_other_verifier.yaml"), model="gemma4:e4b")
    assert x["verifier_llm"]["model"] != "gemma4:e4b"
    # without --model nothing changes
    assert load_config(resolve("configs/e2_blueprint_verifier.yaml"))["name"] == "E2"


def test_model_override_refuses_server_arms():
    with pytest.raises(SystemExit):
        load_config(resolve("configs/e4_server_naive.yaml"), model="gemma4:e4b")


def test_model_tag_and_report_names():
    assert model_tag("gemma4:e4b") == "gemma4-e4b"
    from mimir_eval.report import ARM_HU
    assert ARM_HU["E2-gemma4-e4b"][0] == "Tervezés + ellenőrzés (gemma4-e4b)"
    assert ARM_HU.get("B-doc-L-gemma4-e4b")[0].startswith("Teljes dokumentum, helyi")
    assert ARM_HU.get("E2")[0] == "Tervezés + ellenőrzés"
    assert ARM_HU.get("nope", ("x", "")) == ("x", "")
