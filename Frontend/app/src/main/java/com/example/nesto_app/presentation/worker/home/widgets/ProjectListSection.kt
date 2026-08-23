package com.example.nesto_app.presentation.worker.home.widgets

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import com.example.nesto_app.utils.State
import com.example.nesto_app.domain.entities.Project
import com.example.nesto_app.presentation.commons.FailedCommon
import com.example.nesto_app.presentation.worker.home.shimmer.ProjectListShimmer
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
fun LazyListScope.ProjectListSection(
    projects: State<List<Project>>,
    onClick: (Project) -> Unit
) {
    when(val state = projects){
        is State.Error<*> -> {
            item {
                FailedCommon(text = state.message)
            }
        }
        is State.Loading<*> -> {
            ProjectListShimmer()
        }
        is State.Success -> {
            items(
                items = state.data,
                key = {project -> project.id},
            ){ project ->
                Box(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    ProjectCard(
                        project,
                        onClick = onClick,
                    )
                }
            }
        }
    }
}