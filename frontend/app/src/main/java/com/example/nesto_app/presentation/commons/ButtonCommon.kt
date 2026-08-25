package com.example.nesto_app.presentation.commons

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.nesto_app.ui.theme.Black
import com.example.nesto_app.ui.theme.Dimens
import com.example.nesto_app.ui.theme.Grey

@Composable
fun ButtonCustom(
    modifier: Modifier = Modifier,
    enabled: Boolean,
    isNotLoading: Boolean,
    title: String,
    titleStyle: TextStyle? =  MaterialTheme.typography.titleSmall,
    containerColor: Color = MaterialTheme.colorScheme.primary,
    onClick : () -> Unit
) {
    Button(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(
            vertical = Dimens.ButtonVerticalPadding
        ),
        shape = RoundedCornerShape(Dimens.ButtonCorner),
        enabled = enabled,
        colors = ButtonDefaults.buttonColors(
            containerColor = containerColor,
            disabledContainerColor = Grey,
            disabledContentColor = Black.copy(alpha = 0.38f)
        ),
        onClick = {
            if(enabled && isNotLoading){
                onClick()
            }
        }
    ){
        if (isNotLoading){
            Text(
                text = title,
                style = titleStyle ?: MaterialTheme.typography.titleSmall
            )
        }else{
            CircularProgressIndicator(
                modifier = modifier.size(25.dp),
                color = Grey
            )
        }
    }
}