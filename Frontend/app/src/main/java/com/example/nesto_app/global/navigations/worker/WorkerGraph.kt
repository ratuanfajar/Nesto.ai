package com.example.nesto_app.global.navigations.worker

import WorkerRoutes
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import androidx.navigation.navigation
import com.example.nesto_app.global.navigations.NavGraph
import com.example.nesto_app.presentation.worker.home.HomeWorkerScreen


fun NavGraphBuilder.workerGraph(
    navController: NavHostController,
){
    navigation<NavGraph.WorkerGraph>(
        startDestination = WorkerRoutes.Home
    ){
        composable<WorkerRoutes.Home>{
            HomeWorkerScreen(navController = navController)
        }
    }
}