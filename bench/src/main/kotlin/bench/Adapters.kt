package bench

import com.storyteller_f.mermaid_kmp.renderMermaid
import build.raft.mermaid.core.*
import build.raft.mermaid.layout.LayoutConfig
import build.raft.mermaid.layout.simple.*
import build.raft.mermaid.render.svg.SvgRenderer
import com.swithun.cmpmermaid.core.*
import io.lugf027.github.mermaid.core.MermaidApi
import io.lugf027.github.mermaid.core.diagram.flowchart.FlowchartDb
import io.lugf027.github.mermaid.core.diagram.sequence.SequenceDb
import com.hrm.diagram.core.ir.GraphIR
import com.hrm.diagram.core.ir.SequenceIR

class Adapters {
 private val engine = MermaidEngine()
 private val context = MermaidRenderContext(TextMetricProvider { request ->
  TextMetrics(request.text.length * request.fontSize * 0.6f, request.fontSize * request.lineHeight, 1)
 })
 init { MermaidApi.initialize() }
 private fun nativeParse(source: String): MermaidParseResult.Success = when(val parsed = MermaidParser.parse(source)) {
  is MermaidParseResult.Success -> parsed
  is MermaidParseResult.Failure -> error(parsed.diagnostics.toString())
 }
 fun execute(operation: String, source: String): Any = when(operation) {
  "native:parse" -> nativeParse(source).diagram
  "native:svg" -> SvgRenderer.render(SimpleMermaidLayout.layout(nativeParse(source), FixedWidthTextMeasurer, LayoutConfig()), "benchmark")
  "lugf:parse" -> MermaidApi.parse(source)
  "lugf:svg" -> MermaidApi.renderToSvg(source, "benchmark")
  "cmp:scene" -> when(val result = engine.render(source, context)) {
   is GMResult.Ok -> result.value
   is GMResult.Err -> error(result.error.toString())
  }
  "rust-kmp:svg" -> renderMermaid(source)
  "diagram:parse" -> DiagramAdapter.parse(source)
  else -> error("Unknown operation: $operation")
 }
 /** Structural preflight is outside timing. Expected counts come from the shared corpus. */
 fun validate(operation: String, caseName: String, source: String): Any {
  val result = execute(operation, source)
  val expected = when(caseName) {
   "simple_flowchart" -> 4 to 3
   "complex_flowchart" -> 11 to 13
   "sequence_diagram" -> 3 to 8
   else -> error("Unknown case: $caseName")
  }
  val counts = when(val model = if (operation.startsWith("lugf")) MermaidApi.parse(source).db else if (operation.startsWith("native")) nativeParse(source).diagram else result) {
   is FlowchartDb -> model.getVertices().size to model.getEdges().size
   is SequenceDb -> model.getActors().size to model.getMessages().size
   is FlowchartDiagram -> model.nodes.size to model.edges.size
   is SequenceDiagram -> model.actors.size to model.messages.size
   is GraphIR -> model.nodes.size to model.edges.size
   is SequenceIR -> model.participants.size to model.messages.size
   else -> null
  }
  require(counts == null || counts == expected) { "Expected $expected nodes/edges or actors/messages, got $counts" }
  when(result) {
   is String -> require(result.contains("<svg") && result.contains("</svg>")) { "Invalid SVG envelope" }
   is MermaidScene -> require(result.width > 0 && result.height > 0 && result.elements.isNotEmpty()) { "Empty scene" }
  }
  if (operation == "rust-kmp:svg") validateRustSvg(result as String, caseName, source)
  return result
 }
}

