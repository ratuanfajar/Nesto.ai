package com.example.nesto_app.utils

import android.content.ContentResolver
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.graphics.pdf.PdfDocument
import android.net.Uri
import androidx.core.graphics.toColorInt
import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.domain.entities.Sheet
import java.io.FileOutputStream
import javax.inject.Inject
import androidx.core.graphics.withSave

class PdfExporter @Inject constructor() {

    fun generateAndSavePdf(
        contentResolver: ContentResolver,
        uri: Uri,
        cutList: CutList
    ): Result<Unit> {
        return runCatching {
            val pdfDocument = PdfDocument()

            try {
                // Ukuran standar kertas A4: 595 x 842 pt (72 DPI)
                val pageWidth = 595
                val pageHeight = 842
                val margin = 40f

                var pageNumber = 1

                cutList.sheets.forEach { sheet ->
                    var page = pdfDocument.startPage(
                        PdfDocument.PageInfo.Builder(pageWidth, pageHeight, pageNumber).create()
                    )
                    var canvas = page.canvas
                    pageNumber++

                    // 1. Render Header Halaman
                    val headerPaint = Paint().apply {
                        color = Color.BLACK
                        textSize = 16f
                        isFakeBoldText = true
                    }
                    canvas.drawText("JOB #${cutList.jobInfo.jobId} - LEMBARAN ${sheet.sheetIndex}/${cutList.sheets.size}", margin, 45f, headerPaint)

                    val subHeaderPaint = Paint().apply {
                        color = Color.DKGRAY
                        textSize = 10f
                    }
                    val infoText = "Material: ${sheet.materialName} (${sheet.thicknessMm}mm) | Efisiensi: ${sheet.efficiencyPercent}% | Kerf: ${cutList.settings.kerfMm}mm"
                    canvas.drawText(infoText, margin, 62f, subHeaderPaint)

                    val linePaint = Paint().apply {
                        color = Color.LTGRAY
                        strokeWidth = 1f
                    }
                    canvas.drawLine(margin, 72f, pageWidth - margin, 72f, linePaint)

                    // 2. Kalkulasi Area Gambar Lembaran
                    val drawAreaWidth = pageWidth - (margin * 2)
                    val scale = drawAreaWidth / cutList.settings.sheetWidthMm
                    val drawAreaHeight = cutList.settings.sheetHeightMm * scale

                    val sheetStartX = margin
                    val sheetStartY = 85f

                    // 3. Gambar Diagram Pemotongan Lembaran
                    drawSheetDiagram(
                        canvas = canvas,
                        sheet = sheet,
                        startX = sheetStartX,
                        startY = sheetStartY,
                        drawWidth = drawAreaWidth,
                        drawHeight = drawAreaHeight,
                        scale = scale
                    )

                    // 4. Gambar Tabel List Potongan (BOM) — mulai tepat di bawah diagram,
                    // lanjut ke halaman baru hanya jika tidak muat
                    var partStartIndex = 0
                    var tableStartY = sheetStartY + drawAreaHeight + 25f
                    var isFirstTablePage = true

                    while (partStartIndex < sheet.placedParts.size) {
                        partStartIndex = drawPartTable(
                            canvas = canvas,
                            sheet = sheet,
                            startY = tableStartY,
                            margin = margin,
                            pageWidth = pageWidth.toFloat(),
                            startIndex = partStartIndex,
                            showHeaderAndLegend = isFirstTablePage
                        )

                        pdfDocument.finishPage(page)

                        if (partStartIndex < sheet.placedParts.size) {
                            // Belum selesai — lanjutkan tabel di halaman baru
                            page = pdfDocument.startPage(
                                PdfDocument.PageInfo.Builder(pageWidth, pageHeight, pageNumber).create()
                            )
                            canvas = page.canvas
                            pageNumber++
                            tableStartY = 40f
                            isFirstTablePage = false
                        }
                    }
                }

                // Simpan ke File Descriptor
                contentResolver.openFileDescriptor(uri, "w")?.use { pfd ->
                    FileOutputStream(pfd.fileDescriptor).use { outputStream ->
                        pdfDocument.writeTo(outputStream)
                    }
                } ?: throw Exception("Gagal membuka lokasi penyimpanan file")
            } finally {
                pdfDocument.close()
            }
        }
    }

    private fun drawSheetDiagram(
        canvas: android.graphics.Canvas,
        sheet: Sheet,
        startX: Float,
        startY: Float,
        drawWidth: Float,
        drawHeight: Float,
        scale: Float
    ) {
        // A. Background Lembaran Kayu (Warna Dasar Papan)
        val bgPaint = Paint().apply {
            color = "#0F172A".toColorInt()
            style = Paint.Style.FILL
        }
        canvas.drawRect(RectF(startX, startY, startX + drawWidth, startY + drawHeight), bgPaint)

        // Border Lembaran Papan
        val borderPaint = Paint().apply {
            color = "#475569".toColorInt()
            style = Paint.Style.STROKE
            strokeWidth = 1.5f
        }
        canvas.drawRect(RectF(startX, startY, startX + drawWidth, startY + drawHeight), borderPaint)

        // B. Render Sisa Kayu / Waste Offcuts
        sheet.wasteOffcuts.forEach { waste ->
            val wx = startX + (waste.x * scale)
            val wy = startY + (waste.y * scale)
            val ww = waste.width * scale
            val wh = waste.height * scale

            val wasteBgPaint = Paint().apply {
                color = (if (waste.isReusable) "#10332B" else "#3B181E").toColorInt()
                style = Paint.Style.FILL
            }
            val wasteBorderPaint = Paint().apply {
                color = (if (waste.isReusable) "#10B981" else "#EF4444").toColorInt()
                style = Paint.Style.STROKE
                strokeWidth = 1f
            }

            val rect = RectF(wx, wy, wx + ww, wy + wh)
            canvas.drawRect(rect, wasteBgPaint)
            canvas.drawRect(rect, wasteBorderPaint)
        }

        // C. Render Placed Parts (Potongan Kayu)
        sheet.placedParts.forEach { part ->
            val px = startX + (part.x * scale)
            val py = startY + (part.y * scale)
            val pw = part.width * scale
            val ph = part.height * scale

            val partBgColor = try {
                part.colorCode.toColorInt()
            } catch (e: Exception) {
                "#4E79A7".toColorInt()
            }

            // Isi Warna Part
            val partPaint = Paint().apply {
                color = partBgColor
                style = Paint.Style.FILL
            }
            val partBorderPaint = Paint().apply {
                color = Color.WHITE
                style = Paint.Style.STROKE
                strokeWidth = 0.8f
            }

            val rect = RectF(px, py, px + pw, py + ph)
            canvas.drawRect(rect, partPaint)
            canvas.drawRect(rect, partBorderPaint)

            // D. Render Edge Banding (Garis Merah Pelapis Sisi Kayu)
            val ebPaint = Paint().apply {
                color = "#DC2626".toColorInt()
                strokeWidth = 2.5f
            }

            if (part.eb.getOrNull(0) == 1) canvas.drawLine(px, py, px + pw, py, ebPaint)             // Top
            if (part.eb.getOrNull(1) == 1) canvas.drawLine(px + pw, py, px + pw, py + ph, ebPaint)  // Right
            if (part.eb.getOrNull(2) == 1) canvas.drawLine(px, py + ph, px + pw, py + ph, ebPaint)  // Bottom
            if (part.eb.getOrNull(3) == 1) canvas.drawLine(px, py, px, py + ph, ebPaint)             // Left

            // E. Render Label Nama Part & Ukuran
            if (pw > 15f && ph > 10f) {
                val labelText = part.partName
                val dimText = "${part.width.toInt()}x${part.height.toInt()}"

                val textPaint = Paint().apply {
                    color = Color.WHITE
                    textSize = if (minOf(pw, ph) < 20f) 5f else 7f
                    isAntiAlias = true
                    textAlign = Paint.Align.CENTER
                }

                val centerX = px + (pw / 2f)
                val centerY = py + (ph / 2f)

                canvas.withSave {
                    if (ph > pw) {
                        rotate(90f, centerX, centerY)
                    }
                    drawText(labelText, centerX, centerY - 2f, textPaint)
                    drawText(dimText, centerX, centerY + 6f, textPaint)
                }
            }
        }
    }
    private fun drawPartTable(
        canvas: android.graphics.Canvas,
        sheet: Sheet,
        startY: Float,
        margin: Float,
        pageWidth: Float,
        startIndex: Int,
        showHeaderAndLegend: Boolean
    ): Int {
        var currentY = startY

        if (showHeaderAndLegend) {
            val legendPaint = Paint().apply {
                color = "#DC2626".toColorInt()
                textSize = 8f
                isAntiAlias = true
            }
            canvas.drawText("* Garis Merah = Indikator Sisi Pelapis Edge Banding", margin, currentY, legendPaint)
            currentY += 14f

            val titlePaint = Paint().apply {
                color = Color.BLACK
                textSize = 11f
                isFakeBoldText = true
            }
            canvas.drawText("DAFTAR POTONGAN (PARTS LIST)", margin, currentY, titlePaint)
            currentY += 12f
        } else {
            val titlePaint = Paint().apply {
                color = Color.BLACK
                textSize = 11f
                isFakeBoldText = true
            }
            canvas.drawText("DAFTAR POTONGAN (LANJUTAN)", margin, currentY, titlePaint)
            currentY += 12f
        }

        val tableHeaderBg = Paint().apply {
            color = "#F1F5F9".toColorInt()
            style = Paint.Style.FILL
        }
        canvas.drawRect(RectF(margin, currentY, pageWidth - margin, currentY + 18f), tableHeaderBg)

        val headerTextPaint = Paint().apply {
            color = Color.BLACK
            textSize = 8f
            isFakeBoldText = true
        }

        currentY += 12f
        canvas.drawText("NO", margin + 5f, currentY, headerTextPaint)
        canvas.drawText("NAMA PART", margin + 30f, currentY, headerTextPaint)
        canvas.drawText("UKURAN (MM)", margin + 200f, currentY, headerTextPaint)
        canvas.drawText("ROTASI", margin + 320f, currentY, headerTextPaint)
        canvas.drawText("EDGE BANDING (Atas,Kanan,Bawah,Kiri)", margin + 380f, currentY, headerTextPaint)

        currentY += 15f

        val rowTextPaint = Paint().apply {
            color = Color.DKGRAY
            textSize = 8f
        }

        var index = startIndex
        while (index < sheet.placedParts.size) {
            if (currentY > 800f) {
                return index // halaman penuh, lanjut ke halaman berikutnya
            }

            val part = sheet.placedParts[index]
            val ebStr = part.eb.joinToString(",")
            val rotateStr = if (part.rotated) "90° (Ya)" else "0° (Tidak)"

            canvas.drawText("${index + 1}", margin + 5f, currentY, rowTextPaint)
            canvas.drawText(part.partName, margin + 30f, currentY, rowTextPaint)
            canvas.drawText("${part.width.toInt()} x ${part.height.toInt()}", margin + 200f, currentY, rowTextPaint)
            canvas.drawText(rotateStr, margin + 320f, currentY, rowTextPaint)
            canvas.drawText(ebStr, margin + 380f, currentY, rowTextPaint)

            val linePaint = Paint().apply {
                color = "#E2E8F0".toColorInt()
                strokeWidth = 0.5f
            }
            canvas.drawLine(margin, currentY + 4f, pageWidth - margin, currentY + 4f, linePaint)

            currentY += 14f
            index++
        }

        return index
    }
}