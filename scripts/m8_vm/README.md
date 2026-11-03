# M8 manual VM handoff

Use a dedicated Windows x64 VM with PowerShell5.1, a clean snapshot and isolated lab networking. The existing Server2008SP1 x86 VM cannot run the native x64 fixture. These scripts do not configure your VM or execute binaries.

1. Copy `01_environment.ps1` and `02_inventory.ps1` into the guest.
2. Run the environment inventory, then the binary inventory with the directory of the agreed research corpus. Return environment.json and binary_inventory.csv, not executable samples through chat.
3. Confirm original source/hash/labels and build recipes. Establish each functionality oracle before execution.
4. A separate reviewed functional harness is still required; it cannot be generated correctly from filenames or an assumed n-squared-plus-seven behavior. Malware execution stays in the research VM, not on the host.
5. Static target validation on the analysis machine uses `scripts/verify_m8_targets.py`. Its manifest must bind original/edited SHA256, schema fingerprint, canonical feature names, indices, values and tolerances. Target matching does not establish functionality, poisoning success or detector recall.

The old watermark runner has not been repaired or accepted. Do not run it and reuse its hardcoded PASS/recall fields as new evidence.
