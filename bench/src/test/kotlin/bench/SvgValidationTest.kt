package bench

import kotlin.test.Test
import kotlin.test.assertFailsWith

class SvgValidationTest {
 private val source = "flowchart LR\n A[Start] --> B{Decision}\n B -->|Yes| C[OK]\n B -->|No| D[Cancel]"
 private val wrapped = """<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/><text><tspan>Sta</tspan><tspan>rt</tspan></text><text>Decision</text><text>OK</text><text>Cancel</text><text>Yes</text><text>No</text></svg>"""
 @Test fun acceptsTspanWrapping() { validateRustSvg(wrapped, "simple_flowchart", source) }
 @Test fun rejectsMissingLabel() {
  assertFailsWith<IllegalArgumentException> { validateRustSvg(wrapped.replace("Decision", "Other"), "simple_flowchart", source) }
 }
 @Test fun checksChangedSourceLabel() {
  assertFailsWith<IllegalArgumentException> { validateRustSvg(wrapped, "simple_flowchart", source.replace("Start", "Begin")) }
 }
}
