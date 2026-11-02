#include <cassert>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <algorithm>
#include "tinyml_manager.h"
// Host logging port only; the interpreter, kernels, model and inference wrapper are unchanged.
extern "C" void DebugLog(const char* s) { std::fputs(s,stderr); }
int main() {
  assert(initializeML());
  const float inputs[][6]={{24,50,50,20,0,0},{24,50,50,20,1,0},{24,50,80,20,0,100},{35,50,50,70,1,60},{48,50,50,95,1,60}};
  for(int expected=0;expected<5;expected++) {
    State s; const auto& x=inputs[expected];
    s.sensors.temperature=x[0]; s.sensors.humidity=x[1]; s.sensors.light=x[2]; s.sensors.air=x[3];
    s.sensors.occupancy=x[4]; s.sensors.valid=true; s.power=x[5];
    assert(runInference(s));
    std::printf("Micro inference expected=%d actual=%d confidence=%.4f\n",expected,s.mlClass,s.confidence);
    assert(s.mlClass==expected);
  }
  std::puts("Actual TensorFlow Lite Micro allocation and all five classes passed on host CPU.");
  std::ifstream vectors("tinyml/models/micro_test_vectors.csv");
  assert(vectors.good());
  std::string line; std::getline(vectors,line);
  int count=0, correct=0, matches=0;
  while(std::getline(vectors,line)) {
    std::replace(line.begin(),line.end(),',',' ');
    std::istringstream row(line); float x[8]; for(float& value:x) { row>>value; assert(row); }
    State s; s.sensors.temperature=x[0]; s.sensors.humidity=x[1]; s.sensors.light=x[2]; s.sensors.air=x[3];
    s.sensors.occupancy=x[4]; s.sensors.valid=true; s.power=x[5];
    assert(runInference(s)); count++; correct+=(s.mlClass==int(x[6])); matches+=(s.mlClass==int(x[7]));
  }
  std::printf("Held-out Micro test: %d/%d correct; %d/%d agree with desktop int8\n",correct,count,matches,count);
  assert(count==2000); assert(correct>=1900); assert(matches>=1980);
}
