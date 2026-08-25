package com.example.nesto_app.presentation.worker.project.detail_project.shimmer

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import com.example.nesto_app.presentation.commons.rememberAppShimmer
import com.example.nesto_app.ui.theme.Dimens
import com.valentinilk.shimmer.shimmer

@Composable
fun DetailProjectShimmer(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(bottom = Dimens.BottomPadding),
        verticalArrangement = Arrangement.spacedBy(Dimens.SpacePadding)
    ) {
        repeat(5) {
            CutListShimmer()
        }
    }
}

@Composable
fun CutListShimmer() {
    val shimmer = rememberAppShimmer()
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(200.dp)
            .clip(RoundedCornerShape(6.dp))
            .shimmer(shimmer)
            .background(MaterialTheme.colorScheme.surfaceVariant)
    )
}