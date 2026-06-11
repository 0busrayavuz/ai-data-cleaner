import os

from backend.environment import load_project_env


def test_project_env_loads_gemini_configuration(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "GEMINI_API_KEY=test-key\nGEMINI_MODEL=test-model\n",
        encoding="utf-8",
    )

    previous_key = os.environ.pop("GEMINI_API_KEY", None)
    previous_model = os.environ.pop("GEMINI_MODEL", None)
    try:
        load_project_env(env_path)
        assert os.environ["GEMINI_API_KEY"] == "test-key"
        assert os.environ["GEMINI_MODEL"] == "test-model"
    finally:
        if previous_key is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = previous_key

        if previous_model is None:
            os.environ.pop("GEMINI_MODEL", None)
        else:
            os.environ["GEMINI_MODEL"] = previous_model


def test_project_env_does_not_override_existing_values(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("GEMINI_API_KEY=file-value\n", encoding="utf-8")

    previous_key = os.environ.get("GEMINI_API_KEY")
    try:
        os.environ["GEMINI_API_KEY"] = "existing-value"
        load_project_env(env_path)
        assert os.environ["GEMINI_API_KEY"] == "existing-value"
    finally:
        if previous_key is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = previous_key
