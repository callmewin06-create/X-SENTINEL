#!/bin/bash
# ==============================================================================
# Build Script for X-SENTINEL Benign Control Fixtures
# Target: ReviewedBenignFixture.exe (PE32 x86) & native_original.exe (PE32+ x64)
# ==============================================================================
set -euo pipefail

echo "=== 1. Building native_original.exe (C Native, 64-bit PE32+) ==="
x86_64-w64-mingw32-gcc -O2 -s -Wl,--build-id=none \
    native_benign_fixture.c \
    -o native_original.exe

echo "=== 2. Building ReviewedBenignFixture.exe (.NET C#, 32-bit PE32) ==="
if command -v csc &>/dev/null; then
    csc -target:exe -platform:x86 -optimize+ -out:ReviewedBenignFixture.exe ReviewedBenignFixture.cs
elif command -v mcs &>/dev/null; then
    mcs -target:exe -platform:x86 -optimize+ -out:ReviewedBenignFixture.exe ReviewedBenignFixture.cs
else
    echo "Warning: Neither csc nor mcs found. On Windows, use Developer Command Prompt or csc.exe."
fi

echo "=== 3. Verifying Generated Hashes ==="
sha256sum native_original.exe ReviewedBenignFixture.exe 2>/dev/null || true
echo "Build process completed successfully."
