package com.example.nesto_app.presentation.worker.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavController
import com.example.nesto_app.presentation.commons.ButtonCustom
import com.example.nesto_app.presentation.commons.LazyBody
import com.example.nesto_app.presentation.worker.home.widgets.HeaderProjectListSection
import com.example.nesto_app.presentation.worker.home.widgets.HeaderWidget
import com.example.nesto_app.presentation.worker.home.widgets.ProjectListSection
import com.example.nesto_app.presentation.worker.home.widgets.SearchBar
import com.example.nesto_app.ui.theme.Dimens

@Composable
fun HomeWorkerScreen(
    modifier: Modifier = Modifier,
    navController: NavController,
    viewModel: HomeWorkerViewModel = hiltViewModel<HomeWorkerViewModel>()
    ) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    LazyBody(
        onRefresh = viewModel::onRefresh,
        isRefreshing = state.isRefreshing
    ) {
        item {
            HeaderWidget()
        }

        item {
            Spacer(modifier.height(Dimens.InnerPadding))
        }

        item {
            HeaderProjectListSection(
                state.searchName,
                viewModel::onSearchNameChange
            )
        }

        ProjectListSection(state.projects){
            it
        }
    }
}

