package com.example.nesto_app.mapper

import com.example.nesto_app.data.remotes.response.CutListResponse
import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.domain.entities.JobInfo
import com.example.nesto_app.domain.entities.PlacedPart
import com.example.nesto_app.domain.entities.Settings
import com.example.nesto_app.domain.entities.Sheet
import com.example.nesto_app.ui.theme.ColorPaletteHelper
import com.example.nesto_app.utils.base.Mapper
import java.util.UUID


class CutListMapper : Mapper<CutListResponse, CutList> {

    override fun mapFromResponse(type: CutListResponse): CutList {
        val ebMap = type.parts.associate { it.partName to it.eb }

        val formattedFurnitureName = type.spec?.furnitureType
            ?.replace("_", " ")
            ?.replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
            ?: "Furniture"

        val defaultSheetWidth = type.nesting?.config?.sheetWidthMm ?: 1220f
        val defaultSheetLength = type.nesting?.config?.sheetLengthMm ?: 2440f
        val nestingSummary = type.nesting?.summary
        val bomSummary = type.bomSummary

        return CutList(
            jobInfo = JobInfo(
                jobId = UUID.randomUUID().toString(),
                furnitureType = formattedFurnitureName,
                totalPartsPlaced = nestingSummary?.piecesPlaced ?: 0,
                totalSheetsUsed = nestingSummary?.sheetsUsed ?: 0,
                overallWastePercent = nestingSummary?.totalWastePct ?: 0f,
                totalEdgingLengthM = bomSummary?.edgingLengthM ?: 0f,
                partTypes = bomSummary?.partTypes ?: 0,
                sheetsPerMaterial = nestingSummary?.sheetsPerMaterial ?: emptyMap(),
                areaM2ByThickness = bomSummary?.areaM2ByThickness ?: emptyMap(),
                perSheetWastePercent = nestingSummary?.perSheetWastePct ?: emptyList()
            ),
            settings = Settings(
                sheetWidthMm = defaultSheetWidth,
                sheetLengthMm = defaultSheetLength,
                kerfMm = type.nesting?.config?.kerfMm ?: 3f,
                sheetMarginMm = type.nesting?.config?.trimMm ?: 0f
            ),
            sheets = type.nesting?.sheets?.map { sheetDto ->
                val sheetWidth = sheetDto.sheetWidthMm ?: defaultSheetWidth
                val sheetLength = sheetDto.sheetLengthMm ?: defaultSheetLength

                Sheet(
                    sheetId = "sheet_${sheetDto.index}",
                    sheetIndex = sheetDto.index,
                    materialName = sheetDto.material ?: "",
                    thicknessMm = sheetDto.thicknessMm ?: 0f,
                    widthMm = sheetWidth,
                    lengthMm = sheetLength,
                    efficiencyPercent = sheetDto.utilizationPct ?: 0f,
                    wastePercent = sheetDto.wastePct ?: 0f,
                    placedParts = sheetDto.placements.map { placement ->
                        PlacedPart(
                            partId = "${placement.partName}_${placement.pieceIndex}",
                            furnitureName = formattedFurnitureName,
                            partName = placement.partName,
                            // canvas draws portrait (x = width-axis, y = length-axis),
                            // backend gives landscape coords (x/length along the 2440 axis) — swap them
                            x = placement.yMm,
                            y = placement.xMm,
                            width = placement.widthMm,
                            height = placement.lengthMm,
                            rotated = placement.rotated,
                            eb = ebMap[placement.partName] ?: listOf(0, 0, 0, 0),
                            colorCode = ColorPaletteHelper.getColorForPart(placement.partName)
                        )
                    },
                    wasteOffcuts = emptyList()
                )
            } ?: emptyList()
        )
    }
}