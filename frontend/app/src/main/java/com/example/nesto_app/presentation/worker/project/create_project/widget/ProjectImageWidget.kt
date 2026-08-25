package com.example.nesto_app.presentation.worker.project.create_project.widget

import android.net.Uri
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import com.example.nesto_app.R
import com.example.nesto_app.ui.theme.Dimens
import com.example.nesto_app.ui.theme.SecondaryGrey

@Composable
fun ProjectImagesWidget(
    images: List<Uri>,
    modifier: Modifier = Modifier,
    onImageClick: (Uri) -> Unit = {}
) {
    val context = LocalContext.current

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(
                color = SecondaryGrey,
                shape = RoundedCornerShape(Dimens.CardCorner)
            )
            .padding(Dimens.InnerPadding)
    ) {
        Text(
            text = "Lampiran & Gambar Spesifikasi (${images.size})",
            style = MaterialTheme.typography.titleMedium.copy(
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            ),
            modifier = Modifier.padding(bottom = 12.dp)
        )

        LazyRow(
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(horizontal = 2.dp)
        ) {
            items(images) { uri ->
                val mimeType = context.contentResolver.getType(uri) ?: ""
                val isPdf = mimeType.contains("pdf", ignoreCase = true) || uri.toString().endsWith(".pdf")

                Box(
                    modifier = Modifier
                        .size(width = 110.dp, height = 90.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(MaterialTheme.colorScheme.surface)
                        .border(
                            width = 1.dp,
                            color = MaterialTheme.colorScheme.outline.copy(alpha = 0.3f),
                            shape = RoundedCornerShape(8.dp)
                        )
                        .clickable { onImageClick(uri) },
                    contentAlignment = Alignment.Center
                ) {
                    if (isPdf) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.Center,
                            modifier = Modifier.padding(8.dp)
                        ) {
                            Image(
                                modifier = Modifier.size(20.dp),
                                painter = painterResource(R.drawable.file_uploads),
                                contentDescription = "PDF",
                                colorFilter = ColorFilter.tint(Color.White)
                            )
                            Text(
                                text = "PDF",
                                style = MaterialTheme.typography.labelSmall.copy(
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            )
                        }
                    } else {
                        AsyncImage(
                            model = uri,
                            contentDescription = "Lampiran Gambar",
                            contentScale = ContentScale.Crop,
                            modifier = Modifier.fillMaxSize()
                        )
                    }
                }
            }
        }
    }
}