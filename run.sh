#!/usr/bin/env bash
set -Eeuo pipefail

PYTHON_BIN="/home/opsnav/shawon_Projects/python312/bin/python3.12"
ENV_NAME="role_env"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="${SCRIPT_DIR}/${ENV_NAME}"
REQUIREMENTS_FILE="requirements.txt"
MAIN_SCRIPT="main.py"
PIP_REQUIREMENTS_STAMP="${ENV_DIR}/.requirements.stamp"

cleanup() {
    local exit_code=$?

    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        deactivate || true
    fi

    if [[ ${exit_code} -eq 0 ]]; then
        echo "[INFO] Script finished successfully. Environment deactivated."
    else
        echo "[ERROR] Script failed with exit code ${exit_code}. Environment deactivated."
    fi

    exit "${exit_code}"
}
trap cleanup EXIT INT TERM

echo "[INFO] Starting role modification runner..."
cd "${SCRIPT_DIR}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
    echo "[ERROR] Python interpreter not found or not executable: ${PYTHON_BIN}"
    exit 1
fi

if [[ ! -f "${REQUIREMENTS_FILE}" ]]; then
    echo "[ERROR] Requirements file not found: ${REQUIREMENTS_FILE}"
    exit 1
fi

if [[ ! -f "${MAIN_SCRIPT}" ]]; then
    echo "[ERROR] Main script not found: ${MAIN_SCRIPT}"
    exit 1
fi

if [[ ! -d "${ENV_DIR}" ]]; then
    echo "[INFO] Creating virtual environment: ${ENV_NAME}"
    "${PYTHON_BIN}" -m venv "${ENV_DIR}"
else
    echo "[INFO] Using existing virtual environment: ${ENV_NAME}"
fi

if [[ ! -x "${ENV_DIR}/bin/python" ]]; then
    echo "[ERROR] Virtual environment Python is missing or not executable: ${ENV_DIR}/bin/python"
    exit 1
fi

# shellcheck source=/dev/null
source "${ENV_DIR}/bin/activate"

echo "[INFO] Active Python: $(python --version)"
echo "[INFO] Checking requirements from ${REQUIREMENTS_FILE}"
if [[ ! -f "${PIP_REQUIREMENTS_STAMP}" ]] || ! cmp -s "${REQUIREMENTS_FILE}" "${PIP_REQUIREMENTS_STAMP}"; then
    echo "[INFO] Installing or updating dependencies"
    python -m pip install --upgrade pip
    python -m pip install -r "${REQUIREMENTS_FILE}"
    cp "${REQUIREMENTS_FILE}" "${PIP_REQUIREMENTS_STAMP}"
else
    echo "[INFO] Requirements are already installed for the current requirements.txt"
fi
python -m pip check

echo "[INFO] Running ${MAIN_SCRIPT}"
python "${MAIN_SCRIPT}"
