package com.example.nesto_app.global.navigations.worker

import WorkerRoutes
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import androidx.navigation.navigation
import androidx.navigation.toRoute
import com.example.nesto_app.global.navigations.NavGraph
import com.example.nesto_app.presentation.worker.home.HomeWorkerScreen
import com.example.nesto_app.presentation.worker.project.create_project.CreateProjectScreen
import com.example.nesto_app.presentation.worker.project.detail_project.DetailProjectScreen


fun NavGraphBuilder.workerGraph(
    navController: NavHostController,
){
    navigation<NavGraph.WorkerGraph>(
        startDestination = WorkerRoutes.Home
    ){
        composable<WorkerRoutes.Home>{
            HomeWorkerScreen(navController = navController)
        }

        composable<WorkerRoutes.CreateProject>{
            CreateProjectScreen(navController = navController)
        }

        composable<WorkerRoutes.DetailProject>{
            DetailProjectScreen(navController = navController)
        }
    }
}