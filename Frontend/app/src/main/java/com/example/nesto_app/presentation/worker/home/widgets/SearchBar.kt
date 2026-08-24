package com.example.nesto_app.presentation.worker.home.widgets

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.example.nesto_app.presentation.commons.TextFieldCustom
import com.example.nesto_app.ui.theme.White

@Composable
fun SearchBar(
    modifier: Modifier = Modifier,
    text:String,
    enabled: Boolean = true,
    onChanged: (String) -> Unit
) {
    TextFieldCustom(
        modifier = modifier.clip(
            shape = RoundedCornerShape(16.dp)
        ),
        text = text,
        hint = "Cari Proyek",
        imeAction = ImeAction.Done,
        keyboardType = KeyboardType.Text,
        enabled = enabled,
        visualTransformation = VisualTransformation.None,
        leadingIcon = {
            Icon(
                imageVector = Icons.Default.Search,
                tint = MaterialTheme.colorScheme.onPrimary,
                contentDescription = "Search Icon"
            )
        },
    ){
        onChanged(it)
    }
}
