// GODOT-002: exercise real CubismNativeFramework v5 with PurismCore v5.
// No Godot, no textured rendering. Test the actual 301003_x.moc3.
#include <CubismFramework.hpp>
#include <ICubismAllocator.hpp>
#include <Model/CubismMoc.hpp>
#include <Model/CubismModel.hpp>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <vector>
#include <algorithm>

namespace Csm = Live2D::Cubism::Framework;

struct Allocator final : Csm::ICubismAllocator {
    void* Allocate(const Csm::csmSizeType size) override {return std::malloc(size);}
    void Deallocate(void* memory) override {std::free(memory);}
    void* AllocateAligned(const Csm::csmSizeType size, const Csm::csmUint32 align) override {
        void* ptr=nullptr;
        size_t boundary=std::max<size_t>(align, sizeof(void*));
        if (posix_memalign(&ptr, boundary, size)) return nullptr;
        return ptr;
    }
    void DeallocateAligned(void* memory) override {std::free(memory);}
};

int main(int argc, char** argv) {
    if(argc!=2) return 2;
    std::ifstream file(argv[1], std::ios::binary);
    if(!file) return 3;
    std::vector<unsigned char> bytes{std::istreambuf_iterator<char>(file), {}};
    if(bytes.size()<64 || bytes.size()>250000000) return 4;
    std::puts("FW_V5_PHASE_MODEL_BYTES_READY"); std::fflush(stdout);
    Allocator allocator;
    if(!Csm::CubismFramework::StartUp(&allocator)) return 5;
    Csm::CubismFramework::Initialize();
    std::puts("FW_V5_PHASE_INITIALIZED"); std::fflush(stdout);
    Csm::CubismMoc* moc = Csm::CubismMoc::Create(bytes.data(), static_cast<Csm::csmSizeInt>(bytes.size()), true);
    if(!moc) return 6;
    std::puts("FW_V5_PHASE_MOC_CREATED"); std::fflush(stdout);
    Csm::CubismModel* model = moc->CreateModel();
    if(!model) return 7;
    std::puts("FW_V5_PHASE_MODEL_CREATED"); std::fflush(stdout);
    std::printf("FW_V5_PARAM_COUNT=%d\n",model->GetParameterCount());
    std::printf("FW_V5_DRAWABLE_COUNT=%d\n",model->GetDrawableCount());
    std::fflush(stdout);
    model->SaveParameters();
    model->Update();
    std::puts("FW_V5_PHASE_UPDATED"); std::fflush(stdout);
    moc->DeleteModel(model);
    Csm::CubismMoc::Delete(moc);
    Csm::CubismFramework::Dispose();
    Csm::CubismFramework::CleanUp();
    std::puts("FW_V5_PHASE_PASS");
    return 0;
}
