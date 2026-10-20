package bench

import com.hrm.diagram.parser.mermaid.*
import com.hrm.diagram.core.ir.*
import com.hrm.diagram.core.streaming.*

/** One complete lexer/parser session; internal lexer is compiled in its owning module. */
object DiagramAdapter {
 fun parse(source: String): DiagramModel {
  val lexer = MermaidLexer()
  val step = lexer.feed(lexer.initialState(), source, 0, true)
  require(step.diagnostics.isEmpty()) { step.diagnostics.toString() }
  val sequence = source.trimStart().startsWith("sequenceDiagram")
  val flow = MermaidFlowchartParser()
  val seq = MermaidSequenceParser()
  val line = mutableListOf<Token>()
  fun flush() {
   if (line.isNotEmpty()) {
    val batch = if (sequence) seq.acceptLine(line.toList()) else flow.acceptLine(line.toList())
    require(batch.patches.none { it is IrPatch.AddDiagnostic && it.diagnostic.severity == Severity.ERROR }) { batch.toString() }
    line.clear()
   }
  }
  step.tokens.forEach { token ->
   when (token.kind) {
    MermaidTokenKind.NEWLINE -> flush()
    MermaidTokenKind.COMMENT -> Unit
    MermaidTokenKind.ERROR -> error("Lexer error: $token")
    else -> line.add(token)
   }
  }
  flush()
  return if (sequence) seq.snapshot() else flow.snapshot()
 }
}
