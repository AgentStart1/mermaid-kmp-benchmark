package bench

import java.io.StringReader
import javax.xml.parsers.DocumentBuilderFactory
import org.xml.sax.InputSource

/** Validate the Rust facade's output outside JMH timing; no AST API is exposed. */
internal fun validateRustSvg(svg: String, caseName: String, source: String) {
 val factory = DocumentBuilderFactory.newInstance().apply {
  isNamespaceAware = true
  setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)
  setFeature("http://xml.org/sax/features/external-general-entities", false)
  setFeature("http://xml.org/sax/features/external-parameter-entities", false)
 }
 val document = factory.newDocumentBuilder().parse(InputSource(StringReader(svg)))
 require(document.documentElement.localName == "svg") { "Missing SVG root" }
 val graphicalElements = listOf("path", "rect", "line", "circle", "polygon", "polyline")
 require(graphicalElements.any { document.getElementsByTagNameNS("*", it).length > 0 }) { "SVG has no graphics" }
 val labels = when(caseName) {
  "simple_flowchart" -> listOf(source.substringAfter("A[").substringBefore("]"), "Decision", "OK", "Cancel", "Yes", "No")
  "complex_flowchart" -> listOf("Christmas", "Go shopping", "Let me think", "Laptop", "iPhone", "Car", "Great choice!", "Satisfied?", "Keep it", "Return it", "End", "Shopping Process", "Result")
  "sequence_diagram" -> listOf("Alice", "Bob", "Charlie", "Hello Bob, how are you?", "I'm good thanks!", "Hi Charlie", "Hey Alice!", "Hi there", "Hello!", "Can you help me?", "Sure, what do you need?")
  else -> error("Unknown case: $caseName")
 }
 // SVG text may be wrapped into tspans without inter-span whitespace.
 val elements = document.getElementsByTagNameNS("*", "text")
 val texts = (0 until elements.length).map { elements.item(it).textContent.filterNot(Char::isWhitespace) }
 val missing = labels.filterNot { label -> texts.any { it.contains(label.filterNot(Char::isWhitespace)) } }
 require(missing.isEmpty()) { "SVG missing labels: $missing" }
}
