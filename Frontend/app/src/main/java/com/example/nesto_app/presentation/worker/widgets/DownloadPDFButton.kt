package com.example.nesto_app.presentation.worker.widgets

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.example.nesto_app.R
import com.example.nesto_app.domain.entities.CutList

@Composable
fun DownloadPdfButton(
    cutList: CutList,
    modifier: Modifier = Modifier,
    onSavePdf: (Uri) -> Unit
) {
    val savePdfLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument("application/pdf")
    ) { uri: Uri? ->
        uri?.let { destinationUri ->
            onSavePdf(destinationUri)
        }
    }

    Button(
        onClick = {
            val defaultFileName = "Optimasi_Pemotongan_Job_${cutList.jobInfo.jobId}.pdf"
            savePdfLauncher.launch(defaultFileName)
        },
        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981)),
        modifier = modifier
    ) {
        Image(
            modifier = Modifier.size(20.dp), // Perbaikan: Gunakan Modifier lokal
            painter = painterResource(R.drawable.file_download),
            contentDescription = "Download PDF",
            colorFilter = ColorFilter.tint(Color.White)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = "Download Laporan PDF",
            color = Color.White
        )
    }
}