#!/usr/bin/env bash
set -euo pipefail

script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$script_directory/sdk.sh"
enigma_setup_sdk

target="all"
if [[ $# -eq 2 && "$1" == "--target" ]]; then
    target="$2"
elif [[ $# -ne 0 ]]; then
    printf 'Usage: ./scripts/test-lite.sh [--target vm|native|all]\n' >&2
    exit 2
fi
case "$target" in
    all) routes="vm,native" ;;
    vm|native) routes="$target" ;;
    *) printf 'Target must be vm, native, or all.\n' >&2; exit 2 ;;
esac

for project_dir in ext/enigma-lite validation/lite; do
    project="$enigma_project_root/$project_dir/nil.project.nildata"
    "$enigma_sdk_directory/nilbuild" check --project "$project" --sdk "$enigma_sdk_directory"
    "$enigma_sdk_directory/nilbuild" build --project "$project" --sdk "$enigma_sdk_directory" --target "$target"
done
ENIGMA_LITE_TESTS=1 ENIGMA_TEST_TARGETS="$routes" NIL_SDK="$enigma_sdk_directory" \
    python3 -I -m unittest discover -s "$enigma_project_root/tests" -p test_lite.py -v
