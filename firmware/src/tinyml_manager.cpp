#if defined(ARDUINO) && !defined(CLASSROOM_NATIVE_TEST)
#include <Chirale_TensorFlowLite.h>
#endif
#include <tensorflow/lite/micro/micro_interpreter.h>
#include <tensorflow/lite/micro/micro_mutable_op_resolver.h>
#include <tensorflow/lite/schema/schema_generated.h>
#include <algorithm>
#include <cmath>
#include "tinyml_manager.h"
#include "classroom_model.h"
alignas(16) static uint8_t arena[24*1024];
static tflite::MicroInterpreter* interpreter=nullptr;
bool initializeML() {
  const auto* model=tflite::GetModel(classroom_model);
  if(model->version()!=TFLITE_SCHEMA_VERSION) return false;
  // Reject unsupported per-channel exports instead of silently misclassifying.
  for(const auto* tensor:*model->subgraphs()->Get(0)->tensors()) {
    auto* q=tensor->quantization();
    if(q && q->scale() && q->scale()->size()>1) return false;
  }
  static tflite::MicroMutableOpResolver<2> resolver;
  resolver.AddFullyConnected(); resolver.AddSoftmax();
  static tflite::MicroInterpreter instance(model,resolver,arena,sizeof(arena));
  if(instance.AllocateTensors()!=kTfLiteOk) return false;
  if(instance.input(0)->type!=kTfLiteInt8 || instance.input(0)->bytes!=6 || instance.output(0)->bytes!=5) return false;
  interpreter=&instance; return true;
}
bool runInference(State& s) {
  if(!interpreter) return false;
  auto* input=interpreter->input(0);
  // Feature order and fixed scales match the training and dashboard model exactly.
  float values[]={s.sensors.temperature/50,s.sensors.humidity/100,s.sensors.light/100,s.sensors.air/100,
                  s.sensors.occupancy?1.0f:0.0f,static_cast<float>(s.power/100)};
  for(int i=0;i<6;i++) {
    int value=static_cast<int>(std::round(values[i]/input->params.scale))+input->params.zero_point;
    input->data.int8[i]=std::max(-128,std::min(127,value));
  }
  if(interpreter->Invoke()!=kTfLiteOk) return false;
  auto* out=interpreter->output(0); int best=0;
  for(int i=1;i<5;i++) if(out->data.int8[i]>out->data.int8[best]) best=i;
  s.mlClass=best; s.confidence=(out->data.int8[best]-out->params.zero_point)*out->params.scale;
  return true;
}
