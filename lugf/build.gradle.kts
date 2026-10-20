plugins { kotlin("multiplatform"); kotlin("plugin.serialization") }
kotlin {
 jvmToolchain(21)
 jvm()
 sourceSets {
  commonMain { kotlin.srcDirs("../.upstream/lugf/mermaid-core/src/commonMain/kotlin"); dependencies { implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.11.0")
implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.10.0")
 } }
 }
}
