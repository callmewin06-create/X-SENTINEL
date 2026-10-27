# Benign PE Fixtures: Build Instructions & Toolchain

## 1. Native C Fixture (`native_benign_fixture.exe`)
- **Source**: `experiments/phuc_pe_validation/fixtures/src/native_benign_fixture.c`
- **Compiler**: `x86_64-w64-mingw32-gcc` (MinGW-w64 cross-compiler for Win64 PE)
- **Target Subsystem**: Windows Console (PE32+ executable for MS Windows x86-64)
- **Build Command**:
  ```bash
  x86_64-w64-mingw32-gcc -O2 -s -Wl,--build-id=none \
      experiments/phuc_pe_validation/fixtures/src/native_benign_fixture.c \
      -o experiments/phuc_pe_validation/fixtures/native_benign_fixture.exe
  ```
- **Flags**:
  - `-O2`: Standard optimization.
  - `-s`: Strip symbols for clean PE layout.
  - `-Wl,--build-id=none`: Prevent non-standard GNU build-id notes for PE compatibility.

## 2. .NET C# Fixture (`dotnet_benign_fixture.exe`)
- **Source**: `experiments/phuc_pe_validation/fixtures/src/dotnet_benign_fixture.cs`
- **Compiler**: Microsoft (R) Visual C# Compiler (`csc.exe`) or Mono `mcs` / .NET SDK
- **Pre-built Reviewed Fixture**: The verified fixture `ReviewedBenignFixture.exe` (SHA256: `618ef4f50937c5f87b8d80c3caab88365dc137456d9539f01aa6981881dc6773`) is preserved as `experiments/phuc_pe_validation/fixtures/dotnet_benign_fixture.exe`.

## 3. Test Cases for Functional Verification
1. **Case 1 (Default / No Arg)**:
   - Command: `fixture.exe`
   - Expected Output: `X_SENTINEL_BENIGN_FIXTURE:7`
   - Expected Exit Code: `0`
2. **Case 2 (Positive Integer)**:
   - Command: `fixture.exe 5`
   - Expected Output: `X_SENTINEL_BENIGN_FIXTURE:32` (5^2 + 7 = 32)
   - Expected Exit Code: `0`
3. **Case 3 (Negative Integer)**:
   - Command: `fixture.exe -3`
   - Expected Output: `X_SENTINEL_BENIGN_FIXTURE:16` ((-3)^2 + 7 = 16)
   - Expected Exit Code: `0`
4. **Case 4 (Invalid Input)**:
   - Command: `fixture.exe abc`
   - Expected Stderr: contains error message
   - Expected Exit Code: `2`
