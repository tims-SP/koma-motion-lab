#!/usr/bin/env python3
"""Instrument a temporary upstream GDCubism v0.9.1 checkout; do not fork or commit binaries."""
from pathlib import Path
import sys

root=Path(sys.argv[1])
targets={
    "src/gd_cubism_user_model.cpp":[
        ("void GDCubismUserModel::load_model(const String assets) {",
         'void GDCubismUserModel::load_model(const String assets) {\n    fprintf(stderr, "GODOT002_NATIVE_BEGIN_LOAD_MODEL\\n"); fflush(stderr);'),
        ("this->internal_model = CSM_NEW InternalCubismUserModel(this);",
         'fprintf(stderr, "GODOT002_NATIVE_BEFORE_INTERNAL_NEW\\n"); fflush(stderr);\n    this->internal_model = CSM_NEW InternalCubismUserModel(this);\n    fprintf(stderr, "GODOT002_NATIVE_AFTER_INTERNAL_NEW\\n"); fflush(stderr);'),
        ("this->internal_model->model_load(assets) == false ||",
         '(fprintf(stderr, "GODOT002_NATIVE_BEFORE_MODEL_LOAD_CALL\\n"), fflush(stderr), this->internal_model->model_load(assets)) == false ||'),
    ],
    "src/private/internal_cubism_user_model.cpp":[
        ("bool InternalCubismUserModel::model_load(\n    const String &model_pathname\n) {",
         'bool InternalCubismUserModel::model_load(\n    const String &model_pathname\n) {\n    fprintf(stderr, "GODOT002_NATIVE_ENTRY_INTERNAL_LOAD\\n"); fflush(stderr);'),
        ("this->_model_setting = CSM_NEW CubismModelSettingJson(buffer.ptr(), buffer.size());",
         'fprintf(stderr, "GODOT002_NATIVE_BEFORE_MODEL_JSON\\n"); fflush(stderr);\n    this->_model_setting = CSM_NEW CubismModelSettingJson(buffer.ptr(), buffer.size());\n    fprintf(stderr, "GODOT002_NATIVE_AFTER_MODEL_JSON\\n"); fflush(stderr);'),
        ("this->LoadModel(buffer.ptr(), buffer.size());",
         'fprintf(stderr, "GODOT002_NATIVE_BEFORE_LOAD_MOC\\n"); fflush(stderr);\n        this->LoadModel(buffer.ptr(), buffer.size());\n        fprintf(stderr, "GODOT002_NATIVE_AFTER_LOAD_MOC\\n"); fflush(stderr);'),
        ("this->motion_load();",
         'fprintf(stderr, "GODOT002_NATIVE_BEFORE_MOTION_LOAD\\n"); fflush(stderr);\n        this->motion_load();\n        fprintf(stderr, "GODOT002_NATIVE_AFTER_MOTION_LOAD\\n"); fflush(stderr);'),
        ("this->CreateRenderer();",
         'fprintf(stderr, "GODOT002_NATIVE_BEFORE_CREATE_RENDERER\\n"); fflush(stderr);\n    this->CreateRenderer();\n    fprintf(stderr, "GODOT002_NATIVE_AFTER_CREATE_RENDERER\\n"); fflush(stderr);'),
        ("this->model_load_resource();",
         'fprintf(stderr, "GODOT002_NATIVE_BEFORE_TEXTURE_RESOURCE\\n"); fflush(stderr);\n    this->model_load_resource();\n    fprintf(stderr, "GODOT002_NATIVE_AFTER_TEXTURE_RESOURCE\\n"); fflush(stderr);'),
        ("renderer->DrawModel();",
         'fprintf(stderr, "GODOT002_NATIVE_BEFORE_DRAW_MODEL\\n"); fflush(stderr);\n        renderer->DrawModel();\n        fprintf(stderr, "GODOT002_NATIVE_AFTER_DRAW_MODEL\\n"); fflush(stderr);'),
        ("renderer->build_model(this->_renderer_resource, this->_owner_viewport);",
         'fprintf(stderr, "GODOT002_NATIVE_BEFORE_MESH_BUILD\\n"); fflush(stderr);\n        renderer->build_model(this->_renderer_resource, this->_owner_viewport);\n        fprintf(stderr, "GODOT002_NATIVE_AFTER_MESH_BUILD\\n"); fflush(stderr);')
    ]
}
for rel, replacements in targets.items():
    p=root/rel
    s=p.read_text()
    assert '#include <cstdio>' not in s
    s='#include <cstdio>\n'+s
    for old,new in replacements:
        if s.count(old)<1:
            raise RuntimeError(f"{rel}: expected 1 occurrence of {old[:45]!r}, found {s.count(old)}")
        s=s.replace(old,new,1)
    p.write_text(s)
    print("GODOT002_INSTRUMENTED",rel)
