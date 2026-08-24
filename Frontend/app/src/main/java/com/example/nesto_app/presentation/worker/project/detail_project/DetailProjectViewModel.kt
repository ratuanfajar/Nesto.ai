package com.example.nesto_app.presentation.worker.project.detail_project


import WorkerRoutes
import android.content.ContentResolver
import android.net.Uri
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.toRoute
import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.utils.PdfExporter
import com.example.nesto_app.utils.State
import com.example.nesto_app.utils.dummy.initProjects
import com.example.nesto_app.utils.ui.AppEventBus
import com.example.nesto_app.utils.ui.CustomSnackbarVisuals
import com.example.nesto_app.utils.ui.SnackbarType
import com.example.nesto_app.utils.ui.UiEvent
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject
import kotlin.time.Duration.Companion.milliseconds

@HiltViewModel
class DetailProjectViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val pdfExporter: PdfExporter
): ViewModel(){
    private val projectId: Int = checkNotNull(
        savedStateHandle.toRoute<WorkerRoutes.DetailProject>().projectId
    )
    private val _state = MutableStateFlow<DetailProjectState>(DetailProjectState())
    val state = _state.asStateFlow()

    init {
        onLoad()
    }

    fun onLoad(){
        viewModelScope.launch {
            delay(500.milliseconds)
            val project = initProjects.find { project -> project.id == projectId }
            if(project == null){
                updateState {
                    copy(
                        project = State.Error("Proyek tidak ditemukan")
                    )
                }
                return@launch
            }

            updateState {
                copy(project = State.Success(project))
            }
        }
    }



    fun exportPdf(contentResolver: ContentResolver, uri: Uri, cutList: CutList) {
        viewModelScope.launch(Dispatchers.IO) {
            val result = pdfExporter.generateAndSavePdf(contentResolver, uri, cutList)

            result.onSuccess {
                AppEventBus.events.emit(
                    UiEvent.ShowSnackbar(
                        CustomSnackbarVisuals(
                            type = SnackbarType.SUCCESS,
                            message = "Berhasil di Download!"
                        )
                    )
                )
            }.onFailure { exception ->
                AppEventBus.events.emit(
                    UiEvent.ShowSnackbar(
                        CustomSnackbarVisuals(
                            type = SnackbarType.ERROR,
                            message = "Gagal mengunduh PDF: ${exception.localizedMessage}"
                        )
                    )
                )
            }
        }
    }
    private fun updateState(
        updateState: DetailProjectState.() -> DetailProjectState
    ){
        _state.update {
            it.updateState()
        }
    }
}