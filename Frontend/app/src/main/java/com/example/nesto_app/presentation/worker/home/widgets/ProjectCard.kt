package com.example.nesto_app.presentation.worker.home.widgets

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.example.nesto_app.domain.entities.Project
import com.example.nesto_app.ui.theme.Dimens
import com.example.nesto_app.ui.theme.Grey
import com.example.nesto_app.utils.formaters.TimeFormater.toDisplayString
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
@Composable
fun ProjectCard(
    project: Project,
    onClick: (Project) -> Unit,
) {
    val isDarkTheme = isSystemInDarkTheme()

    val shadowColor = if (isDarkTheme) {
        Color.White.copy(alpha = 0.8f)
    } else {
        Color.Black.copy(alpha = 0.6f)
    }
    Surface(
        modifier = Modifier.fillMaxWidth().shadow(
            elevation = 3.dp,
            shape = RoundedCornerShape(Dimens.CardCorner),
            ambientColor = shadowColor,
            spotColor = shadowColor
        ),
        color = MaterialTheme.colorScheme.background,
        shape = RoundedCornerShape(Dimens.CardCorner),
        onClick = {
            onClick(project)
        }
    ) {
        Column(
            modifier = Modifier
                .padding(Dimens.InnerPadding),
            verticalArrangement = Arrangement.spacedBy(Dimens.SpacePadding)
        ) {
            Text(project.name, style = MaterialTheme.typography.titleMedium.copy(
                color = MaterialTheme.colorScheme.primary
            ))
            Text("Daftar Potongan: ${project.cutList.sheets.size}", style = MaterialTheme.typography.bodySmall)
            HorizontalDivider(
                thickness = 0.5.dp,
                color = Grey
            )
            Row {
                Icon(
                    imageVector = Icons.Default.DateRange,
                    contentDescription = "Date"
                )
                Spacer(modifier = Modifier.width(Dimens.SmallSpacePadding))
                Text("Dibuat: ${project.createdAt.toDisplayString()}", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}