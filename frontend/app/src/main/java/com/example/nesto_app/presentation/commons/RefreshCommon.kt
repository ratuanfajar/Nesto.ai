package com.example.nesto_app.presentation.commons

import androidx.compose.foundation.layout.BoxScope
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.material3.pulltorefresh.PullToRefreshDefaults.Indicator
import androidx.compose.material3.pulltorefresh.rememberPullToRefreshState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.example.nesto_app.ui.theme.White

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RefreshCommon(
    modifier: Modifier = Modifier,
    refreshing: Boolean,
    onRefresh: () -> Unit,
    content: @Composable BoxScope.() -> Unit
) {
    val state = rememberPullToRefreshState()

    PullToRefreshBox(
        modifier = modifier,
        state = state,
        isRefreshing = refreshing,
        onRefresh = onRefresh,
        indicator = {
            Indicator(
                modifier = Modifier.align(Alignment.TopCenter),
                isRefreshing = refreshing,
                state = state,
                containerColor = MaterialTheme.colorScheme.primary,
                color = MaterialTheme.colorScheme.onPrimary
            )
        },
        content = content
    )
}