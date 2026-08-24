package com.example.nesto_app.presentation.worker.widgets

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.presentation.commons.TopAppBarCommon
import com.example.nesto_app.ui.theme.Dimens

@Composable
fun HeaderWidget(cutList: CutList?, onBack: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.Start,
        verticalArrangement = Arrangement.spacedBy(Dimens.SpacePadding)
    ) {
        TopAppBarCommon("Kembali", onBackClick = onBack)
        Text(
            text = "Optimasi Pemotongan 2D", style = MaterialTheme.typography.titleMedium
        )
        if(cutList != null)
            Text(
                text = "Total Lembar: ${cutList.jobInfo.totalSheetsUsed} | Efisiensi Total: ${cutList.jobInfo.overallEfficiencyPercent}%",
                style = MaterialTheme.typography.bodyMedium
            )
    }
}