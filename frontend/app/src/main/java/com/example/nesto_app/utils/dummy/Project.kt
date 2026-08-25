package com.example.nesto_app.utils.dummy

import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.domain.entities.JobInfo
import com.example.nesto_app.domain.entities.PlacedPart
import com.example.nesto_app.domain.entities.Project
import com.example.nesto_app.domain.entities.Settings
import com.example.nesto_app.domain.entities.Sheet
import com.example.nesto_app.domain.entities.WasteOffcut
import kotlin.time.Clock
import kotlin.time.ExperimentalTime

val cutList1 = CutList(
    jobInfo = JobInfo(
        jobId = "1",
        furnitureType = "Lemari Pakaian",
        totalPartsPlaced = 7,
        totalSheetsUsed = 2,
        overallWastePercent = 18.55f,
        totalEdgingLengthM = 18.4f
    ),
    settings = Settings(
        sheetWidthMm = 2440f,
        sheetLengthMm = 1220f,
        kerfMm = 3f,
        sheetMarginMm = 10f
    ),
    sheets = listOf(
        Sheet(
            sheetId = "1",
            sheetIndex = 1,
            materialName = "Triplek Meranti",
            thicknessMm = 18f,
            widthMm = 2440f,
            lengthMm = 1220f,
            efficiencyPercent = 84.60f,
            wastePercent = 15.40f,
            placedParts = listOf(
                PlacedPart(
                    partId = "1",
                    furnitureName = "Lemari Pakaian",
                    partName = "Sisi Kiri",
                    x = 10f,
                    y = 10f,
                    width = 2100f,
                    height = 600f,
                    rotated = true,
                    eb = listOf(1, 1, 1, 1),
                    colorCode = "#4E79A7"
                ),
                PlacedPart(
                    partId = "2",
                    furnitureName = "Lemari Pakaian",
                    partName = "Sisi Kanan",
                    x = 10f,
                    y = 613f,
                    width = 2100f,
                    height = 600f,
                    rotated = true,
                    eb = listOf(1, 1, 1, 1),
                    colorCode = "#59A14F"
                )
            ),
            wasteOffcuts = listOf(
                WasteOffcut(
                    offcutId = "1",
                    x = 2113f,
                    y = 10f,
                    width = 317f,
                    height = 1200f,
                    isReusable = true
                )
            )
        ),
        Sheet(
            sheetId = "2",
            sheetIndex = 2,
            materialName = "Triplek Meranti",
            thicknessMm = 18f,
            widthMm = 2440f,
            lengthMm = 1220f,
            efficiencyPercent = 78.30f,
            wastePercent = 21.70f,
            placedParts = listOf(
                PlacedPart(
                    partId = "3",
                    furnitureName = "Lemari Pakaian",
                    partName = "Pintu Kiri",
                    x = 10f,
                    y = 10f,
                    width = 1900f,
                    height = 580f,
                    rotated = true,
                    eb = listOf(1, 1, 1, 1),
                    colorCode = "#76B7B2"
                ),
                PlacedPart(
                    partId = "4",
                    furnitureName = "Lemari Pakaian",
                    partName = "Pintu Kanan",
                    x = 10f,
                    y = 593f,
                    width = 1900f,
                    height = 580f,
                    rotated = true,
                    eb = listOf(1, 1, 1, 1),
                    colorCode = "#EDC949"
                ),
                PlacedPart(
                    partId = "5",
                    furnitureName = "Lemari Pakaian",
                    partName = "Rak Atas",
                    x = 1913f,
                    y = 10f,
                    width = 517f,
                    height = 380f,
                    rotated = false,
                    eb = listOf(1, 1, 0, 0),
                    colorCode = "#F28E2B"
                ),
                PlacedPart(
                    partId = "6",
                    furnitureName = "Lemari Pakaian",
                    partName = "Rak Tengah",
                    x = 1913f,
                    y = 393f,
                    width = 517f,
                    height = 380f,
                    rotated = false,
                    eb = listOf(0, 0, 0, 0),
                    colorCode = "#E15759"
                ),
                PlacedPart(
                    partId = "7",
                    furnitureName = "Lemari Pakaian",
                    partName = "Rak Bawah",
                    x = 1913f,
                    y = 776f,
                    width = 517f,
                    height = 380f,
                    rotated = false,
                    eb = listOf(0, 0, 1, 0),
                    colorCode = "#B07AA1"
                )
            ),
            wasteOffcuts = listOf(
                WasteOffcut(
                    offcutId = "2",
                    x = 10f,
                    y = 1176f,
                    width = 1900f,
                    height = 34f,
                    isReusable = false
                ),
                WasteOffcut(
                    offcutId = "3",
                    x = 1913f,
                    y = 1159f,
                    width = 517f,
                    height = 51f,
                    isReusable = false
                )
            )
        )
    )
)

val cutList2 = CutList(
    jobInfo = JobInfo(
        jobId = "2",
        furnitureType = "Meja Kerja & Rak Buku",
        totalPartsPlaced = 11,
        totalSheetsUsed = 3,
        overallWastePercent = 18.63f,
        totalEdgingLengthM = 22.5f
    ),
    settings = Settings(
        sheetWidthMm = 2440f,
        sheetLengthMm = 1220f,
        kerfMm = 3f,
        sheetMarginMm = 10f
    ),
    sheets = listOf(
        Sheet(
            sheetId = "3",
            sheetIndex = 1,
            materialName = "Multipleks Plywood",
            thicknessMm = 15f,
            widthMm = 2440f,
            lengthMm = 1220f,
            efficiencyPercent = 85.40f,
            wastePercent = 14.60f,
            placedParts = listOf(
                PlacedPart(
                    partId = "9",
                    furnitureName = "Meja Kerja",
                    partName = "Top Table",
                    x = 10f,
                    y = 10f,
                    width = 1400f,
                    height = 650f,
                    rotated = false,
                    eb = listOf(1, 1, 1, 1),
                    colorCode = "#4E79A7"
                ),
                PlacedPart(
                    partId = "10",
                    furnitureName = "Meja Kerja",
                    partName = "Side Panel Kiri",
                    x = 1413f,
                    y = 10f,
                    width = 700f,
                    height = 600f,
                    rotated = false,
                    eb = listOf(1, 1, 1, 1),
                    colorCode = "#59A14F"
                ),
                PlacedPart(
                    partId = "11",
                    furnitureName = "Meja Kerja",
                    partName = "Side Panel Kanan",
                    x = 1413f,
                    y = 613f,
                    width = 700f,
                    height = 600f,
                    rotated = false,
                    eb = listOf(1, 1, 1, 1),
                    colorCode = "#F28E2B"
                ),
                PlacedPart(
                    partId = "12",
                    furnitureName = "Meja Kerja",
                    partName = "Front Panel",
                    x = 10f,
                    y = 663f,
                    width = 1200f,
                    height = 300f,
                    rotated = false,
                    eb = listOf(1, 1, 0, 0),
                    colorCode = "#E15759"
                )
            ),
            wasteOffcuts = listOf(
                WasteOffcut(
                    offcutId = "4",
                    x = 2123f,
                    y = 10f,
                    width = 307f,
                    height = 1200f,
                    isReusable = true
                )
            )
        ),
        Sheet(
            sheetId = "4",
            sheetIndex = 2,
            materialName = "Multipleks Plywood",
            thicknessMm = 15f,
            widthMm = 2440f,
            lengthMm = 1220f,
            efficiencyPercent = 80.50f,
            wastePercent = 19.50f,
            placedParts = listOf(
                PlacedPart(
                    partId = "13",
                    furnitureName = "Rak Buku",
                    partName = "Sisi Kiri",
                    x = 10f,
                    y = 10f,
                    width = 1800f,
                    height = 350f,
                    rotated = true,
                    eb = listOf(1, 1, 1, 1),
                    colorCode = "#B07AA1"
                ),
                PlacedPart(
                    partId = "14",
                    furnitureName = "Rak Buku",
                    partName = "Sisi Kanan",
                    x = 10f,
                    y = 363f,
                    width = 1800f,
                    height = 350f,
                    rotated = true,
                    eb = listOf(1, 1, 1, 1),
                    colorCode = "#76B7B2"
                ),
                PlacedPart(
                    partId = "15",
                    furnitureName = "Rak Buku",
                    partName = "Top",
                    x = 10f,
                    y = 716f,
                    width = 900f,
                    height = 350f,
                    rotated = false,
                    eb = listOf(1, 1, 0, 0),
                    colorCode = "#EDC949"
                ),
                PlacedPart(
                    partId = "16",
                    furnitureName = "Rak Buku",
                    partName = "Bottom",
                    x = 913f,
                    y = 716f,
                    width = 900f,
                    height = 350f,
                    rotated = false,
                    eb = listOf(0, 0, 1, 0),
                    colorCode = "#FF9DA7"
                )
            ),
            wasteOffcuts = listOf(
                WasteOffcut(
                    offcutId = "5",
                    x = 1813f,
                    y = 10f,
                    width = 617f,
                    height = 1200f,
                    isReusable = true
                )
            )
        ),
        Sheet(
            sheetId = "5",
            sheetIndex = 3,
            materialName = "Multipleks Plywood",
            thicknessMm = 15f,
            widthMm = 2440f,
            lengthMm = 1220f,
            efficiencyPercent = 80.40f,
            wastePercent = 19.60f,
            placedParts = listOf(
                PlacedPart(
                    partId = "19",
                    furnitureName = "Rak Buku",
                    partName = "Back Panel",
                    x = 10f,
                    y = 10f,
                    width = 1700f,
                    height = 1100f,
                    rotated = true,
                    eb = listOf(0, 0, 0, 0),
                    colorCode = "#5B9BD5"
                ),
                PlacedPart(
                    partId = "17",
                    furnitureName = "Rak Buku",
                    partName = "Shelf 1",
                    x = 1713f,
                    y = 10f,
                    width = 280f,
                    height = 850f,
                    rotated = true,
                    eb = listOf(0, 0, 0, 0),
                    colorCode = "#9C755F"
                ),
                PlacedPart(
                    partId = "18",
                    furnitureName = "Rak Buku",
                    partName = "Shelf 2",
                    x = 1996f,
                    y = 10f,
                    width = 280f,
                    height = 850f,
                    rotated = true,
                    eb = listOf(0, 0, 0, 0),
                    colorCode = "#BAB0AC"
                )
            ),
            wasteOffcuts = listOf(
                WasteOffcut(
                    offcutId = "6",
                    x = 1713f,
                    y = 863f,
                    width = 717f,
                    height = 347f,
                    isReusable = true
                )
            )
        )
    )
)

@OptIn(ExperimentalTime::class)
val initProjects = listOf<Project>(
//    Project(
//        id = 1,
//        name = "Project Satu - Lemari Pakaian",
//        cutList = cutList1,
//        createdAt = Clock.System.now(),
//    ),
//    Project(
//        id = 2,
//        name = "Project Dua - Meja Kerja",
//        cutList = cutList2,
//        createdAt = Clock.System.now(),
//    ),
)