package com.example.nesto_app.presentation.worker.home.widgets

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import com.example.nesto_app.ui.theme.Dimens

@Composable
fun HeaderProjectListSection(
    searchName: String,
    onSearchNameChange: (String) -> Unit
) {
    Column (
        verticalArrangement = Arrangement.spacedBy(Dimens.SpacePadding)
    ){
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = "Daftar Proyek",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.SemiBold
                )
            )
//                    Text(
//                        text = "Liat Semua ➜",
//                        style = MaterialTheme.typography.titleSmall.copy(
//                            color = MaterialTheme.colorScheme.primary
//                        )
//                    )
        }
        SearchBar(text = searchName, onChanged = onSearchNameChange)
    }
}