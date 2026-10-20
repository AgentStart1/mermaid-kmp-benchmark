package bench;

import org.openjdk.jmh.annotations.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;

@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 8, time = 1)
@Fork(value = 2, jvmArgsAppend = {"-Xms512m", "-Xmx1g"})
@Threads(1)
public class DiagramBenchmark {
 @Param({"rust-kmp:svg", "native:parse", "native:svg", "lugf:parse", "lugf:svg", "cmp:scene", "diagram:parse"})
 public String operation;
 @Param({"simple_flowchart", "complex_flowchart", "sequence_diagram"})
 public String caseName;
 private String source;
 private Adapters adapters;
 @Setup(Level.Trial)
 public void setup() throws Exception {
  try (var stream = getClass().getResourceAsStream("/" + caseName + ".mmd")) {
   if (stream == null) throw new IllegalStateException("Missing corpus: " + caseName);
   source = new String(stream.readAllBytes(), StandardCharsets.UTF_8);
  }
  adapters = new Adapters();
  adapters.validate(operation, caseName, source);
 }
 @Benchmark
 public Object measure() { return adapters.execute(operation, source); }
}
