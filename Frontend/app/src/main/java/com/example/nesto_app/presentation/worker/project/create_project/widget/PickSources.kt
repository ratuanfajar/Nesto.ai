package com.example.nesto_app.presentation.worker.project.create_project.widget

import android.net.Uri
import androidx.activity.compose.ManagedActivityResultLauncher
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.nesto_app.R
import com.example.nesto_app.ui.theme.Black
import com.example.nesto_app.ui.theme.Dimens
import com.example.nesto_app.ui.theme.SecondaryGrey

@Composable
fun PickSources(filePickerLauncher: ManagedActivityResultLauncher<Array<String>, List<@JvmSuppressWildcards() Uri>>) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable {
                filePickerLauncher.launch(
                    arrayOf("image/jpeg", "image/png", "application/pdf")
                )
            },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = SecondaryGrey
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(Dimens.SpacePadding)
        )
        {
            Image(
                modifier = Modifier.size(30.dp),
                painter = painterResource(R.drawable.file_uploads),
                contentDescription = "Upload Files",
                colorFilter = ColorFilter.tint(Black)
            )
            Text(
                text = "Pilih Gambar atau PDF Spesifikasi",
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            )
            Text(
                text = "Format yang didukung: JPG, PNG, PDF",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
            )
        }
    }
}