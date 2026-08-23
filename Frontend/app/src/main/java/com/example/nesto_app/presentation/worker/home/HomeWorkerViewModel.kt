package com.example.nesto_app.presentation.worker.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.domain.entities.Project
import com.example.nesto_app.utils.State
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject
import kotlin.time.Clock
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds
import kotlin.time.ExperimentalTime

@HiltViewModel
class HomeWorkerViewModel @Inject constructor(): ViewModel(){
    private val _state = MutableStateFlow<HomeWorkerState>(HomeWorkerState())
    val state = _state.asStateFlow()
    private val searchQuery = MutableStateFlow("")

    @OptIn(ExperimentalTime::class)
    private val initProjects = listOf<Project>(
        Project(
            1,
            "Project Satu - Kursi",
            CutList.empty(),
            Clock.System.now()
        ),
        Project(
            2,
            "Project Dua - Meja",
            CutList.empty(),
            Clock.System.now()
        ),
    )
    init {
        onLoad()
        observeSearchQuery()
    }

    fun onSearchNameChange(searchName: String){
        updateState {
            copy(searchName = searchName)
        }
        searchQuery.value = searchName
    }
    fun onLoad() = fetchProjects(isRefresh = false)
    fun onRefresh() = fetchProjects(isRefresh = true)

    private fun fetchProjects(isRefresh: Boolean) {
        viewModelScope.launch {
            updateState { copy(isRefreshing = isRefresh) }
            delay(1.seconds)
            searchProjects(query = state.value.searchName)
        }
    }
    @OptIn(FlowPreview::class)
    private fun observeSearchQuery() {
        viewModelScope.launch {
            searchQuery
                .debounce(500)
                .distinctUntilChanged()
                .collectLatest { query ->
                    searchProjects(query)
                }
        }
    }

    private suspend fun searchProjects(query: String) {
        updateState { copy(projects = State.Loading()) }
        delay(300.milliseconds)
        val projects = if (query.isBlank()) {
            initProjects
        } else {
            initProjects.filter { it.name.contains(query.trim(), ignoreCase = true) }
        }
        updateState {
            copy(
                projects = State.Success(projects),
                isRefreshing = false
            )
        }
    }
    private fun updateState(
        updateState: HomeWorkerState.() -> HomeWorkerState
    ){
        _state.update {
            it.updateState()
        }
    }
}