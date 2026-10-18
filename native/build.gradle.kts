plugins { kotlin("multiplatform"); kotlin("plugin.serialization") }
kotlin {
 jvmToolchain(21)
 jvm()
 sourceSets {
  commonMain { kotlin.srcDirs("../.upstream/native/mermaid-core/src/commonMain/kotlin", "../.upstream/native/mermaid-layout-api/src/commonMain/kotlin", "../.upstream/native/mermaid-layout-simple/src/commonMain/kotlin", "../.upstream/native/mermaid-render-svg/src/commonMain/kotlin"); dependencies {  } }
 }
}
