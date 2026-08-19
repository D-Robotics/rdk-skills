#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include "dnn/hb_dnn.h"
#include "dnn/hb_sys.h"

namespace {

bool ReadExact(const std::string &path, void *destination, std::size_t size) {
  std::ifstream input(path, std::ios::binary | std::ios::ate);
  if (!input) {
    std::cerr << "Cannot open input: " << path << std::endl;
    return false;
  }
  const std::streamsize length = input.tellg();
  if (length != static_cast<std::streamsize>(size)) {
    std::cerr << "Input bytes must equal alignedByteSize. expected=" << size
              << " actual=" << length << std::endl;
    return false;
  }
  input.seekg(0, std::ios::beg);
  return static_cast<bool>(input.read(static_cast<char *>(destination), length));
}

bool WriteExact(const std::string &path, const void *source, std::size_t size) {
  std::ofstream output(path, std::ios::binary);
  return output && static_cast<bool>(output.write(static_cast<const char *>(source), size));
}

}  // namespace

int main(int argc, char **argv) {
  if (argc != 4) {
    std::cerr << "Usage: " << argv[0]
              << " <model.bin> <aligned-input.bin> <output-prefix>" << std::endl;
    return 2;
  }

  const char *model_file = argv[1];
  hbPackedDNNHandle_t packed_handle = nullptr;
  if (hbDNNInitializeFromFiles(&packed_handle, &model_file, 1) != 0) {
    std::cerr << "hbDNNInitializeFromFiles failed" << std::endl;
    return 1;
  }

  const char **model_names = nullptr;
  int model_count = 0;
  if (hbDNNGetModelNameList(&model_names, &model_count, packed_handle) != 0 || model_count < 1) {
    std::cerr << "hbDNNGetModelNameList failed" << std::endl;
    hbDNNRelease(packed_handle);
    return 1;
  }

  hbDNNHandle_t model_handle = nullptr;
  if (hbDNNGetModelHandle(&model_handle, packed_handle, model_names[0]) != 0) {
    std::cerr << "hbDNNGetModelHandle failed" << std::endl;
    hbDNNRelease(packed_handle);
    return 1;
  }

  int input_count = 0;
  int output_count = 0;
  if (hbDNNGetInputCount(&input_count, model_handle) != 0 || input_count != 1 ||
      hbDNNGetOutputCount(&output_count, model_handle) != 0 || output_count < 1) {
    std::cerr << "This template requires exactly one input and at least one output" << std::endl;
    hbDNNRelease(packed_handle);
    return 1;
  }

  hbDNNTensor input{};
  if (hbDNNGetInputTensorProperties(&input.properties, model_handle, 0) != 0 ||
      hbSysAllocCachedMem(&input.sysMem[0], input.properties.alignedByteSize) != 0) {
    std::cerr << "Input allocation failed" << std::endl;
    hbDNNRelease(packed_handle);
    return 1;
  }
  std::memset(input.sysMem[0].virAddr, 0, input.properties.alignedByteSize);
  if (!ReadExact(argv[2], input.sysMem[0].virAddr, input.properties.alignedByteSize)) {
    hbSysFreeMem(&input.sysMem[0]);
    hbDNNRelease(packed_handle);
    return 1;
  }
  hbSysFlushMem(&input.sysMem[0], HB_SYS_MEM_CACHE_CLEAN);

  std::vector<hbDNNTensor> outputs(static_cast<std::size_t>(output_count));
  for (int index = 0; index < output_count; ++index) {
    if (hbDNNGetOutputTensorProperties(&outputs[index].properties, model_handle, index) != 0 ||
        hbSysAllocCachedMem(&outputs[index].sysMem[0], outputs[index].properties.alignedByteSize) != 0) {
      std::cerr << "Output allocation failed at index " << index << std::endl;
      for (int allocated = 0; allocated < index; ++allocated) {
        hbSysFreeMem(&outputs[allocated].sysMem[0]);
      }
      hbSysFreeMem(&input.sysMem[0]);
      hbDNNRelease(packed_handle);
      return 1;
    }
  }

  hbDNNTaskHandle_t task_handle = nullptr;
  hbDNNInferCtrlParam control;
  HB_DNN_INITIALIZE_INFER_CTRL_PARAM(&control);
  hbDNNTensor *output_pointer = outputs.data();
  const int infer_result = hbDNNInfer(&task_handle, &output_pointer, &input, model_handle, &control);
  const int wait_result = infer_result == 0 ? hbDNNWaitTaskDone(task_handle, 0) : infer_result;
  if (wait_result != 0) {
    std::cerr << "hbDNNInfer/hbDNNWaitTaskDone failed: " << wait_result << std::endl;
  }

  bool output_ok = wait_result == 0;
  for (int index = 0; index < output_count; ++index) {
    hbSysFlushMem(&outputs[index].sysMem[0], HB_SYS_MEM_CACHE_INVALIDATE);
    const std::string output_path = std::string(argv[3]) + "_" + std::to_string(index) + ".bin";
    output_ok = WriteExact(output_path, outputs[index].sysMem[0].virAddr,
                           outputs[index].properties.alignedByteSize) &&
                output_ok;
    hbSysFreeMem(&outputs[index].sysMem[0]);
  }
  if (task_handle != nullptr) {
    hbDNNReleaseTask(task_handle);
  }
  hbSysFreeMem(&input.sysMem[0]);
  hbDNNRelease(packed_handle);
  return output_ok ? 0 : 1;
}
