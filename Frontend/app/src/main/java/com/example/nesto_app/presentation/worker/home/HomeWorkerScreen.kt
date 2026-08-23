package com.example.nesto_app.presentation.worker.home

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavController
import com.example.nesto_app.presentation.commons.LazyBody
import com.example.nesto_app.presentation.worker.home.widgets.HeaderProjectListSection
import com.example.nesto_app.presentation.worker.home.widgets.HeaderWidget
import com.example.nesto_app.presentation.worker.home.widgets.ProjectListSection
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
            navController.navigate(
                WorkerRoutes.DetailProject(projectId = it.id)
            )
        }
    }
}

