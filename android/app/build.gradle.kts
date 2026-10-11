plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.sadusor.orionv3"
    compileSdk = 35

    defaultConfig {
        applicationId = if (providers.gradleProperty("orionIsolatedArchiveTest").orNull == "true") "com.sadusor.orionv3.archivequal" else "com.sadusor.orionv3"
        minSdk = 26
        targetSdk = 35
        versionCode = 9
        versionName = "0.5.1"
    }

    buildFeatures { compose = true }

    // Archive qualification uses a distinct install identity and private app data.
    // The normal ORION package, version and Update button are unchanged.
    defaultConfig {
        manifestPlaceholders["orionAppLabel"] = if (providers.gradleProperty("orionIsolatedArchiveTest").orNull == "true") "ORION2" else "ORION"
    }

    // The offline GGUF is already quantized; do not recompress it in the APK.
    androidResources { noCompress += "gguf" }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }
}

kotlin { jvmToolchain(17) }

dependencies {
    implementation(platform("androidx.compose:compose-bom:2024.12.01"))
    implementation("androidx.activity:activity-compose:1.10.0")
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.foundation:foundation")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("dev.ffmpegkit-maintained:llama-android:0.1.1")
    debugImplementation("androidx.compose.ui:ui-tooling")
}
