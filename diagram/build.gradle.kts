plugins { kotlin("multiplatform"); kotlin("plugin.serialization") }
kotlin {
 jvmToolchain(21)
 jvm()
 sourceSets {
 jvmMain { kotlin.srcDir("../.upstream/diagram/diagram-core/src/jvmMain/kotlin") }
  commonMain { kotlin.srcDirs("../.upstream/diagram/diagram-core/src/commonMain/kotlin", "../.upstream/diagram/diagram-parser/src/commonMain/kotlin"); dependencies {  } }
 }
}
