pluginManagement { repositories { gradlePluginPortal(); mavenCentral() } }
rootProject.name = "mermaid-kmp-benchmark"
include("cmp", "native", "lugf", "diagram", "bench")
