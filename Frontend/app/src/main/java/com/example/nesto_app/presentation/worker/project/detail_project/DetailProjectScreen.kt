package com.example.nesto_app.presentation.worker.project.detail_project

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavController
import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.presentation.commons.Body
import com.example.nesto_app.presentation.commons.FailedCommon
import com.example.nesto_app.presentation.worker.project.detail_project.shimmer.DetailProjectShimmer
import com.example.nesto_app.presentation.worker.widgets.DownloadPdfButton
import com.example.nesto_app.presentation.worker.widgets.HeaderWidget
import com.example.nesto_app.presentation.worker.widgets.SheetCanvasVisualizer
import com.example.nesto_app.ui.theme.Dimens
import com.example.nesto_app.utils.State

@Composable
fun DetailProjectScreen(
    modifier: Modifier = Modifier,
    navController: NavController,
    viewModel: DetailProjectViewModel = hiltViewModel<DetailProjectViewModel>()) {

    val context = LocalContext.current
    val state by viewModel.state.collectAsStateWithLifecycle()
    val scrollState = rememberScrollState()
    val cutList: CutList? = when (val projectState = state.project) {
        is State.Success -> projectState.data.cutList
        else -> null
    }
    Body(
        scrollState =scrollState,
        enableRefresh = false
    ) {
        HeaderWidget(cutList = cutList){
            navController.popBackStack()
        }
        when(val state = state.project){
            is State.Error<*> -> {
                FailedCommon(text = state.message)
            }
            is State.Loading<*> -> {
                DetailProjectShimmer()
            }
            is State.Success -> {
                val cutList = state.data.cutList

                DownloadPdfButton(
                    cutList = cutList,
                    onSavePdf = { uri ->
                        viewModel.exportPdf(context.contentResolver,uri, cutList)
                    }
                )
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(bottom = Dimens.BottomPadding)
                        .weight(1f),
                    verticalArrangement = Arrangement.spacedBy(Dimens.SpacePadding)
                ) {
                    items(cutList.sheets, key = { it.sheetId }) { sheet ->
                        SheetCanvasVisualizer(
                            sheet = sheet,
                            settings = cutList.settings
                        )
                    }
                }
            }
        }
    }
}