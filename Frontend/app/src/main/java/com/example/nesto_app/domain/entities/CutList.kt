package com.example.nesto_app.domain.entities

import androidx.compose.ui.graphics.Color

data class CutList(
    val jobInfo: JobInfo,
    val settings: Settings,
    val sheets: List<Sheet>
) {
    companion object {
        fun empty() = CutList(
            jobInfo = JobInfo(
                jobId = "",
                furnitureType = "",
                totalPartsPlaced = 0,
                totalSheetsUsed = 0,
                overallWastePercent = 0f,
                totalEdgingLengthM = 0f
            ),
            settings = Settings(
                sheetWidthMm = 1220f,
                sheetLengthMm = 2440f,
                kerfMm = 3f,
                sheetMarginMm = 0f
            ),
            sheets = emptyList()
        )
    }
}

data class JobInfo(
    val jobId: String,
    val furnitureType: String,
    val totalPartsPlaced: Int,
    val totalSheetsUsed: Int,
    val overallWastePercent: Float,
    val totalEdgingLengthM: Float,
    val partTypes: Int = 0,
    val sheetsPerMaterial: Map<String, Int> = emptyMap(),
    val areaM2ByThickness: Map<String, Float> = emptyMap(),
    val perSheetWastePercent: List<Float> = emptyList()
) {
    val overallEfficiencyPercent: Float
        get() = 100f - overallWastePercent
}

data class Settings(
    val sheetWidthMm: Float,         // Default / fallback width
    val sheetLengthMm: Float,        // Default / fallback height
    val kerfMm: Float,               // Dari BE: nesting.config.kerf_mm
    val sheetMarginMm: Float         // Dari BE: nesting.config.trim_mm
)

data class Sheet(
    val sheetId: String,
    val sheetIndex: Int,
    val materialName: String,
    val thicknessMm: Float,           // Diubah ke Float (support pecahan)
    val widthMm: Float,               // Tambahan: sheet_width_mm khusus lembar ini
    val lengthMm: Float,              // Tambahan: sheet_length_mm khusus lembar ini
    val efficiencyPercent: Float,    // Dari BE: utilization_pct
    val wastePercent: Float,         // Dari BE: waste_pct
    val placedParts: List<PlacedPart>,
    val wasteOffcuts: List<WasteOffcut> = emptyList()
)

data class PlacedPart(
    val partId: String,
    val furnitureName: String,
    val partName: String,
    val x: Float,
    val y: Float,
    val width: Float,
    val height: Float,
    val rotated: Boolean,
    val eb: List<Int>,                // [Top, Right, Bottom, Left] dari array parts BE
    val colorCode: String
)

data class WasteOffcut(
    val offcutId: String,
    val x: Float,
    val y: Float,
    val width: Float,
    val height: Float,
    val isReusable: Boolean
)

fun String.toColor(fallback: Color = Color.Gray): Color {
    return try {
        val cleanHex = this.removePrefix("#")
        val colorLong = when (cleanHex.length) {
            6 -> "FF$cleanHex".toLong(16) // Add 100% alpha (FF)
            8 -> cleanHex.toLong(16)      // ARGB format
            else -> return fallback
        }
        Color(colorLong)
    } catch (e: Exception) {
        fallback
    }
}