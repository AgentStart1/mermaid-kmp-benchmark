package bench

import java.io.File
import kotlinx.serialization.json.*

fun main(args: Array<String>) {
 if (args.firstOrNull() != "preflight") {
  org.openjdk.jmh.Main.main(args)
  return
 }
 val adapters = Adapters()
 val operations = listOf("rust-kmp:svg", "native:parse", "native:svg", "lugf:parse", "lugf:svg", "cmp:scene", "diagram:parse")
 val cases = listOf("simple_flowchart", "complex_flowchart", "sequence_diagram")
 val rows = operations.flatMap { operation -> cases.map { caseName ->
  val source = object {}.javaClass.getResource("/$caseName.mmd")!!.readText()
  buildJsonObject {
   put("operation", operation); put("caseName", caseName)
   try {
    val value = adapters.execute(operation, source)
    if (value is String) {
     val file = File("results/samples/${operation.substringBefore(':')}-$caseName.svg")
     file.parentFile.mkdirs(); file.writeText(value)
    }
    adapters.validate(operation, caseName, source)
    // Repeat on the same instance to detect accumulating parser state.
    adapters.validate(operation, caseName, source.replace("Start", "Begin"))
    adapters.validate(operation, caseName, source)
    put("status", "ok")
   } catch (error: LinkageError) { put("status", "failed"); put("error", error.message ?: error.javaClass.name) } catch (error: Exception) { put("status", "failed"); put("error", error.message ?: error.javaClass.name) }
  }
 } }
 val file = File("results/preflight.json"); file.parentFile.mkdirs()
 file.writeText(Json { prettyPrint = true }.encodeToString(JsonArray.serializer(), JsonArray(rows)))
 println(file.readText())
}
