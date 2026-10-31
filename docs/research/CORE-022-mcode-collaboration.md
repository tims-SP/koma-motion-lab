# CORE-022 — actual mcode collaboration record

2026-10-30. Work environment, official npm `@minimax-ai/code` 0.7.2.

The user authorized the CN OAuth device flow. A real model turn returned
`MCODE_AUTH_OK`. No account credentials or OAuth tokens are recorded here.

Two broader repository/file-attachment review attempts timed out (CLI exit 6,
including `Runtime shutdown did not complete cleanly`). They yielded no review
and must not be counted as successful independent audits.

A smaller, one-step, tool-free review then completed successfully (CLI exit 0).
It reviewed the stated Three.js `onBeforeCompile` cache defect and proposed fix,
not repository files or rendered images. Exact response follows:

> Yes. Because the callback bodies are textually identical, Three.js’s normal program-cache identity cannot distinguish the closures’ captured constants; it may be reused for both materials. A stable `customProgramCacheKey` that uniquely encodes pass and source category correctly separates those programs, provided values never change and each combination has different shader semantics. The callback may still be needed to inject constants. Caveat: this key must also account for shader-affecting material differences such as alpha-test/cutout behavior, alpha blending, or texture/encoding and color-management configuration. Data textures and vertex colors require explicit `colorSpace`/working-color-space handling; otherwise cached shaders can still produce incorrect final colors or cutouts.

The actual implementation keeps source alpha-test/map/side properties and
Three.js's built-in material cache inputs while adding a custom pass/category
key for injected constants. Structural QA validates exact ID colors, binary
silhouette, matching map coverage and unit-length normals. This targeted mcode
feedback corroborates the cache fix; the executed image tests establish the
observed result. Neither is full Aka source fidelity or continuous 360° acceptance.
