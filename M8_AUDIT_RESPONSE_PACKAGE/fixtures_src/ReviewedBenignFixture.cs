using System;

/*
 * X-SENTINEL Research Artifact - Managed .NET C# Benign Fixture
 * Purpose: Baseline fixture for PE feature extraction & execution verification.
 * Safety: Read-only deterministic arithmetic f(n) = n^2 + 7. No network, no file I/O, no persistence.
 */
public class RevisionFixture {
    public static int Main(string[] args) {
        int n = 0;
        if (args.Length > 0 && !Int32.TryParse(args[0], out n)) return 2;
        Console.WriteLine("X_SENTINEL_BENIGN_FIXTURE:" + (n * n + 7));
        return 0;
    }
}
