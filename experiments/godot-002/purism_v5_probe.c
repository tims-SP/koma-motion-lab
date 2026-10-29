/* GODOT-002: independent v5 Cubism Core ABI and real MOC3 smoke test.
   Uses no Godot or third-party SDK. This does NOT claim image parity. */
#define _POSIX_C_SOURCE 200112L
#define PSM_COMPAT_VERSION 0x05010000L
#include <PurismCore.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PHASE(label) do { puts("PSM_V5_PHASE_" label); fflush(stdout); } while (0)
int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: probe <file.moc3>\n"); return 2; }
    FILE *f = fopen(argv[1], "rb");
    if (!f) { perror("fopen"); return 3; }
    if (fseek(f, 0, SEEK_END) != 0) return 4;
    long sz = ftell(f);
    if (sz < 16 || sz > 250000000L) return 5;
    rewind(f);
    void *memory = NULL;
    if (posix_memalign(&memory, csmAlignofMoc, (size_t)sz) != 0) return 6;
    if (fread(memory, 1, (size_t)sz, f) != (size_t)sz) return 7;
    fclose(f);
    PHASE("LOADED");
    int version = csmGetMocVersion(memory, (unsigned int)sz);
    printf("PSM_V5_VERSION=%d\n", version); fflush(stdout);
    if (!csmHasMocConsistency(memory, (unsigned int)sz)) return 8;
    PHASE("CONSISTENT");
    csmMoc *moc = csmReviveMocInPlace(memory, (unsigned int)sz);
    if (!moc) return 9;
    PHASE("REVIVED");
    unsigned int model_size = csmGetSizeofModel(moc);
    printf("PSM_V5_MODEL_SIZE=%u\n", model_size); fflush(stdout);
    if (model_size < 64 || model_size > 250000000U) return 10;
    void *model_buffer = NULL;
    if (posix_memalign(&model_buffer, csmAlignofModel, model_size) != 0) return 11;
    csmModel *model = csmInitializeModelInPlace(moc, model_buffer, model_size);
    if (!model) return 12;
    PHASE("INITIALIZED");
    printf("PSM_V5_PARAMETER_COUNT=%d\n", csmGetParameterCount(model));
    printf("PSM_V5_DRAWABLE_COUNT=%d\n", csmGetDrawableCount(model));
    fflush(stdout);
    csmUpdateModel(model);
    PHASE("UPDATED");
    free(model_buffer);
    free(memory);
    PHASE("PASS");
    return 0;
}
