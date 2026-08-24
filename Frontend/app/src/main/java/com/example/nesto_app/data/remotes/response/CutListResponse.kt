package com.example.nesto_app.data.remotes.response

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class CutListResponse(
    @SerialName("spec") val spec: SpecDto? = null,
    @SerialName("parts") val parts: List<PartDto> = emptyList(),
    @SerialName("bom_summary") val bomSummary: BomSummaryDto? = null,
    @SerialName("nesting") val nesting: NestingDto? = null,
    @SerialName("raw_output") val rawOutput: String? = null,
    @SerialName("timings") val timings: TimingsDto? = null
)

@Serializable
data class SpecDto(
    @SerialName("furniture_type") val furnitureType: String? = null,
    @SerialName("overall_dimensions") val overallDimensions: DimensionsDto? = null,
    @SerialName("plinth") val plinth: PlinthDto? = null,
    @SerialName("partitions") val partitions: PartitionsDto? = null,
    @SerialName("material") val material: MaterialSpecDto? = null,
    @SerialName("drop_pocket") val dropPocket: String? = null,
    @SerialName("has_curve") val hasCurve: Boolean? = null,
    @SerialName("default_thickness_mm") val defaultThicknessMm: Float? = null,
    @SerialName("default_edging_mm") val defaultEdgingMm: Float? = null
)

@Serializable
data class DimensionsDto(
    @SerialName("length_cm") val lengthCm: Float? = null,
    @SerialName("width_cm") val widthCm: Float? = null,
    @SerialName("height_cm") val heightCm: Float? = null
)

@Serializable
data class PlinthDto(
    @SerialName("has_plinth") val hasPlinth: Boolean? = null,
    @SerialName("height_cm") val heightCm: Float? = null,
    @SerialName("offset_cm") val offsetCm: Float? = null
)

@Serializable
data class PartitionsDto(
    @SerialName("shelves_count") val shelvesCount: Int? = null,
    @SerialName("doors_count") val doorsCount: Int? = null,
    @SerialName("drawers_count") val drawersCount: Int? = null
)

@Serializable
data class MaterialSpecDto(
    @SerialName("board_material") val boardMaterial: String? = null,
    @SerialName("board_thickness_mm") val boardThicknessMm: Float? = null,
    @SerialName("finish") val finish: String? = null,
    @SerialName("finish_color") val finishColor: String? = null,
    @SerialName("finish_code") val finishCode: String? = null
)

@Serializable
data class PartDto(
    @SerialName("part_name") val partName: String,
    @SerialName("length_mm") val lengthMm: Float? = null,
    @SerialName("width_mm") val widthMm: Float? = null,
    @SerialName("thickness_mm") val thicknessMm: Float? = null,
    @SerialName("qty") val qty: Int? = null,
    @SerialName("eb") val eb: List<Int> = listOf(0, 0, 0, 0),
    @SerialName("material") val material: String? = null,
    @SerialName("grain_locked") val grainLocked: Boolean? = null,
    @SerialName("notes") val notes: String? = null,
    @SerialName("cut_length_mm") val cutLengthMm: Float? = null,
    @SerialName("cut_width_mm") val cutWidthMm: Float? = null
)

@Serializable
data class BomSummaryDto(
    @SerialName("part_types") val partTypes: Int? = null,
    @SerialName("total_pieces") val totalPieces: Int? = null,
    @SerialName("area_m2_by_thickness") val areaM2ByThickness: Map<String, Float> = emptyMap(),
    @SerialName("edging_length_m") val edgingLengthM: Float? = null
)

@Serializable
data class NestingDto(
    @SerialName("summary") val summary: NestingSummaryDto? = null,
    @SerialName("sheets") val sheets: List<NestingSheetDto> = emptyList(),
    @SerialName("config") val config: NestingConfigDto? = null,
    @SerialName("svg") val svg: String? = null
)

@Serializable
data class NestingSummaryDto(
    @SerialName("sheets_used") val sheetsUsed: Int? = null,
    @SerialName("sheets_per_material") val sheetsPerMaterial: Map<String, Int> = emptyMap(),
    @SerialName("total_waste_pct") val totalWastePct: Float? = null,
    @SerialName("per_sheet_waste_pct") val perSheetWastePct: List<Float> = emptyList(),
    @SerialName("pieces_placed") val piecesPlaced: Int? = null,
    @SerialName("pieces_unplaced") val piecesUnplaced: Int? = null
)

@Serializable
data class NestingSheetDto(
    @SerialName("index") val index: Int,
    @SerialName("material") val material: String? = null,
    @SerialName("thickness_mm") val thicknessMm: Float? = null,
    @SerialName("sheet_length_mm") val sheetLengthMm: Float? = null,
    @SerialName("sheet_width_mm") val sheetWidthMm: Float? = null,
    @SerialName("placements") val placements: List<PlacementDto> = emptyList(),
    @SerialName("utilization_pct") val utilizationPct: Float? = null,
    @SerialName("waste_pct") val wastePct: Float? = null
)

@Serializable
data class PlacementDto(
    @SerialName("part_name") val partName: String,
    @SerialName("x_mm") val xMm: Float,
    @SerialName("y_mm") val yMm: Float,
    @SerialName("length_mm") val lengthMm: Float,
    @SerialName("width_mm") val widthMm: Float,
    @SerialName("rotated") val rotated: Boolean = false,
    @SerialName("piece_index") val pieceIndex: Int = 0
)

@Serializable
data class NestingConfigDto(
    @SerialName("sheet_length_mm") val sheetLengthMm: Float? = null,
    @SerialName("sheet_width_mm") val sheetWidthMm: Float? = null,
    @SerialName("kerf_mm") val kerfMm: Float? = null,
    @SerialName("trim_mm") val trimMm: Float? = null,
    @SerialName("algorithm") val algorithm: String? = null,
    @SerialName("respect_grain") val respectGrain: Boolean? = null
)

@Serializable
data class TimingsDto(
    @SerialName("inference") val inference: Float? = null,
    @SerialName("bom") val bom: Float? = null,
    @SerialName("nesting") val nesting: Float? = null,
    @SerialName("total") val total: Float? = null
)