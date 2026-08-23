package com.example.nesto_app.global.navigations

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import com.example.nesto_app.global.navigations.worker.workerGraph

@Composable
fun RootNavGraph(
    navController: NavHostController,
    startDestination: NavGraph.WorkerGraph = NavGraph.WorkerGraph,
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        workerGraph(navController)
    }
}
