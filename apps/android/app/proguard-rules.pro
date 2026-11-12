# Javo Agents ProGuard / R8 rules

# Kotlinx Serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt

-keepclassmembers class kotlinx.serialization.json.** {
    *** Companion;
}
-keepclasseswithmembers class kotlinx.serialization.json.** {
    kotlinx.serialization.KSerializer serializer(...);
}
-keep,includedescriptorclasses class com.javo.agents.data.**$$serializer { *; }
-keepclassmembers class com.javo.agents.data.** {
    *** Companion;
}
-keepclasseswithmembers class com.javo.agents.data.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# Retrofit / OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-keepattributes Signature,Exceptions

# Room
-keep class * extends androidx.room.RoomDatabase
-dontwarn androidx.room.paging.**
