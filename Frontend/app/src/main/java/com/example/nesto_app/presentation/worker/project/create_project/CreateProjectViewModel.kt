package com.example.nesto_app.presentation.worker.project.create_project

import android.content.ContentResolver
import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.utils.PdfExporter
import com.example.nesto_app.utils.dummy.initProjects
import com.example.nesto_app.utils.toMultipart
import com.example.nesto_app.utils.ui.AppEventBus
import com.example.nesto_app.utils.ui.CustomSnackbarVisuals
import com.example.nesto_app.utils.ui.SnackbarType
import com.example.nesto_app.utils.ui.UiEvent
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CreateProjectViewModel @Inject constructor(
    private val pdfExporter: PdfExporter
) : ViewModel() {
    private val _state = MutableStateFlow(CreateProjectState())
    val state: StateFlow<CreateProjectState> = _state.asStateFlow()

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
    fun onFilesSelected(newUris: List<Uri>) {
        updateState {
            val updatedList = (selectedUris + newUris).distinct()
            copy(
                selectedUris = updatedList,
                errorMessage = null
            )
        }
    }

    fun onRemoveFile(uri: Uri) {
        updateState {
            copy(
                selectedUris = selectedUris.filter { it != uri }
            )
        }
    }

    fun onProcessProjectFiles(context: Context) {
        val currentUris = _state.value.selectedUris
        if (currentUris.isEmpty()) {
            _state.update { it.copy(errorMessage = "Pilih setidaknya satu file gambar/PDF") }
            return
        }

        viewModelScope.launch(Dispatchers.IO) {
            updateState {
                copy(
                    isLoading = true,
                    errorMessage = null
                )
            }
            try {
                val allowedMimeTypes = listOf("image/jpeg", "image/png", "application/pdf")

                val multipartParts = currentUris.map { uri ->
                    uri.toMultipart(
                        context = context,
                        partName = "files",
                        allowedMimeTypes = allowedMimeTypes
                    )
                }

                val response = initProjects[0].cutList

                if (response != null) {
                    updateState {
                        copy(
                            isLoading = false,
                            cutList = response
                        )
                    }
                } else {
                    updateState {
                        copy(
                            isLoading = false,
                            errorMessage = "Gagal memproses dokumen di server"
                        )
                    }
                }

            } catch (e: IllegalArgumentException) {
                updateState {
                    copy(
                        isLoading = false,
                        errorMessage = e.localizedMessage
                    )
                }
            } catch (e: Exception) {
                updateState {
                    copy(
                        isLoading = false,
                        errorMessage = e.localizedMessage ?: "Terjadi kesalahan tidak terduga"
                    )
                }
            }
        }
    }

    private fun updateState(
        updateState: CreateProjectState.() -> CreateProjectState
    ){
        _state.update {
            it.updateState()
        }
    }
}