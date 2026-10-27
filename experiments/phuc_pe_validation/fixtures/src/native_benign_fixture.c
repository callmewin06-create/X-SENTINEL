/*
 * X-SENTINEL Research Artifact - Benign Native PE Fixture
 * Author: Phuc (PhucPNHSE203815) - TASK 2 PE Validation
 * Function: Computes f(n) = n^2 + 7 deterministically.
 * Safety: Read-only arithmetic, no network, no persistence, no file I/O.
 */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    long long n = 0;
    if (argc > 1) {
        char *endptr = NULL;
        n = strtoll(argv[1], &endptr, 10);
        if (*endptr != '\0') {
            fprintf(stderr, "Error: Invalid integer input '%s'\n", argv[1]);
            return 2;
        }
    }
    long long result = n * n + 7;
    printf("X_SENTINEL_BENIGN_FIXTURE:%lld\n", result);
    return 0;
}
