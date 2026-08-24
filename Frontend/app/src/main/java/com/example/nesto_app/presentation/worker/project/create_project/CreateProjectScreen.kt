package com.example.nesto_app.presentation.worker.project.create_project

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavController
import com.example.nesto_app.presentation.commons.Body
import com.example.nesto_app.presentation.commons.FailedCommon
import com.example.nesto_app.presentation.worker.project.create_project.widget.FileSelected
import com.example.nesto_app.presentation.worker.widgets.HeaderWidget
import com.example.nesto_app.presentation.worker.project.create_project.widget.LoadingWidget
import com.example.nesto_app.presentation.worker.project.create_project.widget.PickSources
import com.example.nesto_app.presentation.worker.project.create_project.widget.ProjectImagesWidget
import com.example.nesto_app.presentation.worker.widgets.DownloadPdfButton
import com.example.nesto_app.presentation.worker.widgets.SheetCanvasVisualizer
import com.example.nesto_app.ui.theme.Dimens

@Composable
fun CreateProjectScreen(
    modifier: Modifier = Modifier,
    navController: NavController,
    viewModel: CreateProjectViewModel = hiltViewModel<CreateProjectViewModel>()
) {
    val context = LocalContext.current
    val state by viewModel.state.collectAsStateWithLifecycle()
    val scrollState = rememberScrollState()

    // File Picker Launcher untuk Gambar (JPG/PNG) & PDF
    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenMultipleDocuments()
    ) { uris ->
        if (uris.isNotEmpty()) {
            viewModel.onFilesSelected(uris)
        }
    }

    Body(
        scrollState = scrollState,
        enableRefresh = false
    ) {
        HeaderWidget(cutList = state.cutList) {
            navController.popBackStack()
        }
        when {
            state.isLoading -> {
                LoadingWidget()
            }

            state.cutList != null -> {
                val cutList = state.cutList!!
                LazyColumn(
                    modifier = Modifier.fillMaxSize()
                        .weight(1f),
                    contentPadding = PaddingValues(
                        top = Dimens.SpacePadding,
                        bottom = Dimens.BottomPadding
                    ),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(Dimens.SpacePadding)
                ) {
                    item {
                        DownloadPdfButton(
                            cutList = cutList,
                            onSavePdf = { uri ->
                                viewModel.exportPdf(context.contentResolver,uri, cutList)
                            }
                        )
                    }

                    if (state.selectedUris.isNotEmpty()) {
                        item {
                            ProjectImagesWidget(images = state.selectedUris)
                        }
                    }

                    items(cutList.sheets, key = { it.sheetId }) { sheet ->
                        SheetCanvasVisualizer(
                            sheet = sheet,
                            settings = cutList.settings
                        )
                    }
                }
            }

            else -> {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(Dimens.SpacePadding),
                    verticalArrangement = Arrangement.spacedBy(Dimens.SpacePadding)
                ) {
                    state.errorMessage?.let { errorMsg ->
                        FailedCommon(text = errorMsg)
                    }
                    PickSources(filePickerLauncher)
                    if (state.selectedUris.isNotEmpty()) {
                        FileSelected(state.selectedUris,context,
                            onRemoveFile = viewModel::onRemoveFile,
                            onProcessProjectFiles = viewModel::onProcessProjectFiles)
                    }
                }
            }
        }
    }
}