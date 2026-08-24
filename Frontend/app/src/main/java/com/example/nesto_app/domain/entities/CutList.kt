package com.example.nesto_app.domain.entities

import androidx.compose.ui.graphics.Color
import kotlin.time.ExperimentalTime
import androidx.core.graphics.toColorInt

@OptIn(ExperimentalTime::class)
data class CutList(
    val jobInfo: JobInfo,
    val settings: Settings,
    val sheets: List<Sheet>
) {
    companion object {
        fun empty() = CutList(
            jobInfo = JobInfo(
                jobId = "",
                totalPartsPlaced = 0,
                totalSheetsUsed = 0,
                overallEfficiencyPercent = 0f,
                overallWastePercent = 0f
            ),
            settings = Settings(
                sheetWidthMm = 0f,
                sheetHeightMm = 0f,
                kerfMm = 0f,
                sheetMarginMm = 0f
            ),
            sheets = emptyList()
        )
    }
}

data class JobInfo(
    val jobId: String,
    val totalPartsPlaced: Int,
    val totalSheetsUsed: Int,
    val overallEfficiencyPercent: Float,
    val overallWastePercent: Float
)

data class Settings(
    val sheetWidthMm: Float,
    val sheetHeightMm: Float,
    val kerfMm: Float,
    val sheetMarginMm: Float
)

data class Sheet(
    val sheetId: String,
    val sheetIndex: Int,
    val materialName: String,
    val thicknessMm: Int,
    val efficiencyPercent: Float,
    val wastePercent: Float,
    val placedParts: List<PlacedPart>,
    val wasteOffcuts: List<WasteOffcut>
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
    val eb: List<Int>, // [Top, Right, Bottom, Left]
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


fun String.toColor(): Color {
    return try {
        Color(this.toColorInt())
    } catch (e: Exception) {
        Color.Gray
    }
}