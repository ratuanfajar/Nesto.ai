package com.example.nesto_app.ui.theme

import androidx.compose.ui.graphics.Color
import kotlin.math.abs

// Brand Colors
val PrimaryOrange = Color(0xFFFFA909)
val RedSecondary = Color(0xFFC46A48)
val RedPrimary = Color(0xFFF04B11)
val SecondaryGrey = Color(0xFFF6F6F6)
val Grey = Color(0xFFC9C9CB)

val DarkGreen = Color(0xFF40813F)
val Green = Color(0xFF53A654)

val CanvasColor = Color(0xFF1E293B)



// Shadows (~10% alpha variants)
val PrimaryShadow = Color(0x1AFFA909)
val GreyShadow = Color(0x1AC9C9CB)
val WhiteShadow = Color(0x1AF6F6F6)
val RedShadow = Color(0x33EF4444)
val GreenShadow = Color(0x3310B981)


val White = Color(0xFFFFFFFF)
val Black = Color(0xFF1C1B1F)

object ColorPaletteHelper {
    // Palette warna kontras yang ramah mata untuk Canvas
    private val partColors = listOf(
        "#2563EB", // Royal Blue
        "#059669", // Emerald Green
        "#D97706", // Amber / Brown
        "#7C3AED", // Deep Violet
        "#DB2777", // Pink
        "#0891B2", // Cyan
        "#EA580C", // Orange
        "#4F46E5", // Indigo
        "#65A30D"  // Lime
    )

    fun getColorForPart(partName: String): String {
        // Math.abs(hashCode()) memastikan partName yang sama SELALU menghasilkan indeks warna yang sama
        val index = abs(partName.hashCode()) % partColors.size
        return partColors[index]
    }
}
