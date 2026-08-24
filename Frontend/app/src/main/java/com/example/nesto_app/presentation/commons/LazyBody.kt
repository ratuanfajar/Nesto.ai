package com.example.nesto_app.presentation.commons

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.example.nesto_app.ui.theme.Dimens

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LazyBody(
    modifier: Modifier = Modifier,
    isRefreshing: Boolean = false,
    onRefresh: () -> Unit = {},
    content: LazyListScope.() -> Unit
) {
    val listState = rememberLazyListState()

    RefreshCommon(
        modifier = modifier,
        refreshing = isRefreshing,
        onRefresh = onRefresh
    ) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background,
            contentColor = MaterialTheme.colorScheme.onBackground
        ) {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(Dimens.InnerPadding),
                state = listState,
                verticalArrangement = Arrangement.spacedBy(Dimens.SpacePadding),
                horizontalAlignment = Alignment.CenterHorizontally,
                contentPadding = PaddingValues(
                    top = Dimens.TopPadding,
                    bottom = Dimens.InnerPadding
                ),
                content = content
            )
        }
    }
}