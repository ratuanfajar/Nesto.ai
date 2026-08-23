package com.example.nesto_app.presentation.commons

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import com.example.nesto_app.ui.theme.Black
import com.example.nesto_app.ui.theme.Dimens

@Composable
fun TopAppBarCommon(
    title: String,
    titleColor: Color? = null,
    onBackClick: (() -> Unit)? = null,
    ) {
    Row (
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.Start,
        verticalAlignment = Alignment.CenterVertically
    ){
        if (onBackClick != null) {
            IconButton(
                onClick = onBackClick
            ) {
                Icon(
                    Icons.AutoMirrored.Filled.ArrowBack,
                    contentDescription = "Back"
                )
            }
            Spacer(Modifier.padding(Dimens.SpacePadding))
        }
        Text(
            text = title,
            style = MaterialTheme.typography.headlineSmall.copy(
                color = titleColor ?: MaterialTheme.colorScheme.onBackground
            ),
        )
    }
}