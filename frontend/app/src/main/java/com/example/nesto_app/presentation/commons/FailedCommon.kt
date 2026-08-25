package com.example.nesto_app.presentation.commons

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.example.nesto_app.R
import com.example.nesto_app.ui.theme.Dimens
import com.example.nesto_app.ui.theme.RedPrimary

@Composable
fun FailedCommon(
    modifier: Modifier = Modifier,
    imageId:Int? = null,
    text: String
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Image(
            modifier = modifier.size(200.dp),
            painter = painterResource(imageId ?: R.drawable.failed),
            contentDescription = "Failed Image"
        )
        Spacer(modifier.height(Dimens.SpacePadding))
        Text(text, style = MaterialTheme.typography.bodyMedium.copy(
            color = RedPrimary
        ))
    }
}