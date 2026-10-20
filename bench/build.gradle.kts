import java.security.MessageDigest
plugins { kotlin("jvm"); application }
kotlin { jvmToolchain(21) }
dependencies {
 implementation(project(":cmp")); implementation(project(":native")); implementation(project(":lugf")); implementation(project(":diagram"))
 implementation("io.github.storytellerf:mermaidffi-kmp:0.0.1-alpha5")
 testImplementation(kotlin("test"))
 implementation("org.openjdk.jmh:jmh-core:1.37")
 annotationProcessor("org.openjdk.jmh:jmh-generator-annprocess:1.37")
 implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.10.0")
}
application { mainClass.set("bench.MainKt") }
sourceSets.main { resources.srcDir("../test-data") }

val verifyRustArtifact by tasks.registering {
 inputs.files(configurations.runtimeClasspath)
 inputs.file(rootProject.file("libraries.lock.json"))
 doLast {
  val lock = groovy.json.JsonSlurper().parse(rootProject.file("libraries.lock.json")) as Map<*, *>
  val rust = lock["rust-kmp"] as Map<*, *>
  val artifact = configurations.runtimeClasspath.get().single { it.name == "mermaidffi-kmp-jvm-0.0.1-alpha5.jar" }
  val digest = MessageDigest.getInstance("SHA-256").digest(artifact.readBytes()).joinToString("") { "%02x".format(it) }
  check(digest == rust["jvm_artifact_sha256"]) { "Rust KMP artifact checksum mismatch" }
  logger.lifecycle("Verified mermaid-rust-kmp alpha5 JVM artifact SHA-256")
 }
}
tasks.named("installDist") { dependsOn(verifyRustArtifact) }
