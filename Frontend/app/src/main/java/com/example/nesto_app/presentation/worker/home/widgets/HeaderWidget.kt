package com.example.nesto_app.presentation.worker.home.widgets

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.example.nesto_app.presentation.commons.ButtonCustom
import com.example.nesto_app.presentation.commons.TopAppBarCommon
import com.example.nesto_app.ui.theme.Dimens

@Composable
fun HeaderWidget(modifier: Modifier = Modifier) {
    Column(
        verticalArrangement = Arrangement.spacedBy(Dimens.SpacePadding)
    ) {

        TopAppBarCommon("Nesto", MaterialTheme.colorScheme.primary)
        Text("Kelola Proyek Furnitur dengan Presisi", style = MaterialTheme.typography.headlineMedium)
        Text("Pantau potongan furnitur dalam satu dasbor terintegrasi.", style = MaterialTheme.typography.bodyMedium)
        ButtonCustom(
            enabled = true,
            isNotLoading = true,
            title = "+ Buat Proyek",
            onClick = {
//                    confirmAction = clearAction
            }
        )
    }
}