package com.example.nesto_app.presentation.worker.widgets

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.nesto_app.domain.entities.Settings
import com.example.nesto_app.domain.entities.Sheet
import com.example.nesto_app.domain.entities.toColor
import com.example.nesto_app.ui.theme.CanvasColor
import com.example.nesto_app.ui.theme.Dimens
import com.example.nesto_app.ui.theme.Green
import com.example.nesto_app.ui.theme.GreenShadow
import com.example.nesto_app.ui.theme.RedPrimary
import com.example.nesto_app.ui.theme.RedShadow
import com.example.nesto_app.ui.theme.White

@Composable
fun SheetCanvasVisualizer(
    sheet: Sheet,
    settings: Settings,
    modifier: Modifier = Modifier
) {
    val textMeasurer = rememberTextMeasurer()
    val aspectRatio = sheet.widthMm / sheet.lengthMm
    val density = LocalDensity.current
    val baseTypography = MaterialTheme.typography.labelSmall

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(CanvasColor, RoundedCornerShape(Dimens.CardCorner))
            .padding(Dimens.InnerPadding)
    ) {
        // Header Info Lembaran
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.Bottom
        ) {
            Text(
                text = "${sheet.sheetId} (${sheet.materialName})",
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.SemiBold,
                    color = White
                )
            )
            Spacer(modifier = Modifier.width(Dimens.SpacePadding))
            Text(
                text = "Efisiensi Area: ${"%.1f".format(sheet.efficiencyPercent)}%",
                style = MaterialTheme.typography.titleSmall.copy(
                    fontWeight = FontWeight.Bold,
                    color = Green
                )
            )
        }

        Canvas(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(aspectRatio)
                .clipToBounds()
                .background(Color(0xFF0F172A))
                .border(1.dp, Color(0xFF475569))
        ) {
            val scale = size.width / sheet.widthMm

            // 1. Render Waste
            sheet.wasteOffcuts.forEach { waste ->
                val wx = waste.x * scale
                val wy = waste.y * scale
                val ww = waste.width * scale
                val wh = waste.height * scale

                val fillColor = if (waste.isReusable) GreenShadow else RedShadow
                val borderColor = if (waste.isReusable) Green else RedPrimary

                drawRect(color = fillColor, topLeft = Offset(wx, wy), size = Size(ww, wh))
                drawRect(
                    color = borderColor,
                    topLeft = Offset(wx, wy),
                    size = Size(ww, wh),
                    style = Stroke(width = 1.dp.toPx())
                )
            }

            // 2. Render Placed Parts
            sheet.placedParts.forEach { part ->
                val px = part.x * scale
                val py = part.y * scale
                val pw = part.width * scale
                val ph = part.height * scale

                val baseColor = part.colorCode.toColor()

                drawRect(
                    color = baseColor.copy(alpha = 0.85f),
                    topLeft = Offset(px, py),
                    size = Size(pw, ph)
                )

                drawRect(
                    color = Color.White.copy(alpha = 0.5f),
                    topLeft = Offset(px, py),
                    size = Size(pw, ph),
                    style = Stroke(width = 1.dp.toPx())
                )

                // 3. Edge Banding
                val ebThickness = 3.dp.toPx()
                val ebColor = Color(0xFFDC2626)

                if (part.eb.getOrNull(0) == 1) drawLine(ebColor, Offset(px, py), Offset(px + pw, py), strokeWidth = ebThickness)
                if (part.eb.getOrNull(1) == 1) drawLine(ebColor, Offset(px + pw, py), Offset(px + pw, py + ph), strokeWidth = ebThickness)
                if (part.eb.getOrNull(2) == 1) drawLine(ebColor, Offset(px, py + ph), Offset(px + pw, py + ph), strokeWidth = ebThickness)
                if (part.eb.getOrNull(3) == 1) drawLine(ebColor, Offset(px, py), Offset(px, py + ph), strokeWidth = ebThickness)

                // 4. Render Teks Dinamis
                val minDimensionDp = with(density) { minOf(pw, ph).toDp().value }

                // Hitung Font Size Otomatis Berdasarkan Ukuran Kotak
                val fontSize = when {
                    minDimensionDp < 18f -> 6.sp
                    minDimensionDp < 35f -> 8.sp
                    minDimensionDp < 55f -> 10.sp
                    else -> 12.sp
                }

                // Hanya gambar jika ukuran kotak mencukupi (minimal 10dp)
                if (minDimensionDp >= 10f) {
                    val labelText = "${part.partName}\n${part.width.toInt()}x${part.height.toInt()}"
                    val centerX = px + pw / 2f
                    val centerY = py + ph / 2f
                    val isTall = ph > pw

                    val textStyle = baseTypography.copy(
                        color = Color.White,
                        fontSize = fontSize,
                        fontWeight = FontWeight.Medium,
                        textAlign = TextAlign.Center,
                        lineHeight = fontSize * 1.1f
                    )

                    val textLayoutResult = textMeasurer.measure(
                        text = labelText,
                        style = textStyle,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )

                    val textW = textLayoutResult.size.width.toFloat()
                    val textH = textLayoutResult.size.height.toFloat()

                    if (isTall) {
                        // Rotasi 90 Derajat: Lebar teks (textW) dibandingkan dengan TINGGI kotak (ph)
                        if (textW <= ph * 1.1f && textH <= pw * 1.1f) {
                            rotate(degrees = 90f, pivot = Offset(centerX, centerY)) {
                                drawText(
                                    textLayoutResult = textLayoutResult,
                                    topLeft = Offset(centerX - textW / 2f, centerY - textH / 2f)
                                )
                            }
                        }
                    } else {
                        // Horizontal Biasa: Lebar teks (textW) dibandingkan dengan LEBAR kotak (pw)
                        if (textW <= pw * 1.1f && textH <= ph * 1.1f) {
                            drawText(
                                textLayoutResult = textLayoutResult,
                                topLeft = Offset(centerX - textW / 2f, centerY - textH / 2f)
                            )
                        }
                    }
                }
            }
        }
    }
}