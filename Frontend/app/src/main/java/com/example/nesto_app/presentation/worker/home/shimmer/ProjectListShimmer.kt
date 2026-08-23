package com.example.nesto_app.presentation.worker.home.shimmer

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import com.example.nesto_app.presentation.commons.rememberAppShimmer
import com.valentinilk.shimmer.shimmer


fun LazyListScope.ProjectListShimmer(
    itemCount: Int = 5
) {
    items(itemCount) {
        ProjectItemShimmer()
    }
}

@Composable
fun ProjectItemShimmer() {
    val shimmer = rememberAppShimmer()
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(125.dp)
            .clip(RoundedCornerShape(6.dp))
            .shimmer(shimmer)
            .background(MaterialTheme.colorScheme.surfaceVariant)
    )
}