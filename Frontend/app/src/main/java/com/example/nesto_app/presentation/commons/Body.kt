package com.example.nesto_app.presentation.commons

import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalFocusManager
import com.example.nesto_app.ui.theme.Dimens
import com.example.nesto_app.utils.ui.clearFocusOnTap

@Composable
fun Body(
    scrollState: ScrollState,
    isRefreshing: Boolean = false,
    onRefresh: () -> Unit = {},
    enableRefresh: Boolean = true,
    verticalAlignment: Arrangement.Vertical = Arrangement.spacedBy(Dimens.SpacePadding),
    content : @Composable ColumnScope.() -> Unit
) {
    val body: @Composable BoxScope.() -> Unit = {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState)
                .padding(Dimens.InnerPadding)
                .padding(top = Dimens.TopPadding)
                .clearFocusOnTap(LocalFocusManager.current),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = verticalAlignment,
            content = content
        )
    }
    if(enableRefresh){
        RefreshCommon(
            modifier = Modifier.fillMaxSize(),
            refreshing = isRefreshing,
            onRefresh = onRefresh,
            content = body
        )
    }else{
        Box(
            modifier = Modifier.fillMaxSize(),
            content = body
        )
    }
}